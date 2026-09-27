import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scoring.web_discovery import THEMES, search_theme, web_context


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class RateLimited(Exception):
    response = SimpleNamespace(status_code=429)


class LimitedResponse(Response):
    def raise_for_status(self):
        raise RateLimited()


class WebDiscoveryTests(unittest.TestCase):
    def test_news_and_web_deduplicate_and_retain_provenance(self):
        tier = next(iter(THEMES))
        theme = next(iter(THEMES[tier]))
        url = "https://example.org/story"
        news = {"articles": [{"title": "New development", "url": url,
                              "seendate": "20260927T120000Z", "domain": "example.org"}]}
        web = {"web": {"results": [{"title": "Same story", "url": url + "#section"},
                                   {"title": "Different source", "url": "https://example.com/other"}]}}
        get = Mock(side_effect=[Response(news), Response(web)])
        fake_requests = SimpleNamespace(get=get, RequestException=Exception)
        with patch.dict("sys.modules", {"requests": fake_requests}):
            leads, errors = search_theme(tier, theme, brave_key="test-token")
        self.assertEqual(len(leads), 2)
        self.assertEqual(errors, [])
        self.assertEqual(leads[0]["published"], "20260927T120000Z")
        self.assertIn("Search result only", leads[0]["verification"])
        self.assertIn(url, web_context(leads))
        self.assertEqual(get.call_args_list[1].kwargs["headers"]["X-Subscription-Token"], "test-token")

    def test_invalid_theme_does_not_make_network_call(self):
        get = Mock()
        fake_requests = SimpleNamespace(get=get, RequestException=Exception)
        with patch.dict("sys.modules", {"requests": fake_requests}):
            with self.assertRaises(ValueError):
                search_theme("not a tier", "unknown")
            get.assert_not_called()

    def test_public_rate_limit_falls_back_to_web_search(self):
        tier = next(iter(THEMES))
        theme = next(iter(THEMES[tier]))
        web = {"web": {"results": [{"title": "Alternative", "url": "https://example.com/source"}]}}
        get = Mock(side_effect=[LimitedResponse({}), Response(web)])
        fake_requests = SimpleNamespace(get=get, RequestException=Exception)
        with patch.dict("sys.modules", {"requests": fake_requests}):
            leads, errors = search_theme(tier, theme, brave_key="configured")
        self.assertEqual(len(leads), 1)
        self.assertIn("rate-limited", errors[0])
        self.assertEqual(get.call_count, 2)

    def test_public_rate_limit_without_key_returns_setup_message(self):
        tier = next(iter(THEMES))
        theme = next(iter(THEMES[tier]))
        get = Mock(return_value=LimitedResponse({}))
        fake_requests = SimpleNamespace(get=get, RequestException=Exception)
        with patch.dict("sys.modules", {"requests": fake_requests}):
            leads, errors = search_theme(tier, theme)
        self.assertEqual(leads, [])
        self.assertIn("FIRECRAWL_API_KEY", errors[0])

    def test_firecrawl_key_finds_web_results_after_news_rate_limit(self):
        tier = next(iter(THEMES))
        theme = next(iter(THEMES[tier]))
        post = Mock(return_value=Response({"success": True, "data": {"web": [
            {"title": "Public lead", "url": "https://example.com/lead"}
        ]}}))
        fake_requests = SimpleNamespace(get=Mock(return_value=LimitedResponse({})),
                                        post=post, RequestException=Exception)
        with patch.dict("sys.modules", {"requests": fake_requests}):
            leads, errors = search_theme(tier, theme, firecrawl_key="fc-test")
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["provider"], "Firecrawl web search")
        self.assertIn("rate-limited", errors[0])
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer fc-test")
        self.assertEqual(post.call_args.kwargs["json"]["sources"], ["web"])


if __name__ == "__main__":
    unittest.main()
