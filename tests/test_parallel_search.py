import asyncio
from contextlib import contextmanager
import json
import unittest
from unittest.mock import Mock, patch

import httpx

from scoring import parallel_search
from scoring.web_discovery import THEMES, search_theme, web_context


TIER = next(iter(THEMES))
THEME = next(iter(THEMES[TIER]))
QUERY = THEMES[TIER][THEME]
PAYLOAD = {"results": [
    {"title": "Treasury market update", "url": "https://example.org/research#rates",
     "publish_date": "2026-10-01", "excerpts": ["Public source excerpt."]},
    {"title": "Unsafe link", "url": "javascript:alert(1)", "excerpts": []},
    {"title": None, "url": "https://example.com/undated", "excerpts": []},
]}


class MCPServer:
    """Exercise the real MCP session/HTTP transport, replacing only the network."""

    def __init__(self, payload=None, error=False, text=False, status=200):
        self.payload = PAYLOAD if payload is None else payload
        self.error, self.text, self.status = error, text, status
        self.requests = []

    def handle(self, request):
        message = json.loads(request.content)
        self.requests.append((request, message))
        if message["method"].startswith("notifications/"):
            return httpx.Response(202)
        if message["method"] == "initialize":
            result = {"protocolVersion": message["params"]["protocolVersion"],
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "fixture", "version": "1"}}
        elif message["method"] == "tools/list":
            result = {"tools": [{"name": "web_search", "inputSchema": {"type": "object"}}]}
        elif message["method"] == "tools/call":
            if self.status != 200:
                return httpx.Response(self.status, text="private remote diagnostic")
            result = {"isError": self.error, "content": [
                {"type": "text", "text": json.dumps(self.payload)}]}
            if not self.text:
                result["structuredContent"] = self.payload
        else:
            raise AssertionError(message)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

    @contextmanager
    def installed(self):
        real_client = httpx.AsyncClient
        clients = []

        def client(**kwargs):
            value = real_client(transport=httpx.MockTransport(self.handle), **kwargs)
            clients.append(value)
            return value

        with patch.object(parallel_search.httpx, "AsyncClient", side_effect=client):
            yield self
        assert all(client.is_closed for client in clients)


class ParallelSearchTests(unittest.TestCase):
    def dispatch(self, server, **kwargs):
        with server.installed(), patch("requests.get") as news:
            news.return_value.json.return_value = {"articles": []}
            return search_theme(TIER, THEME, parallel=True,
                                parallel_session_id="a" * 32, **kwargs)

    def test_dispatch_transport_and_downstream_context_without_credentials(self):
        server = MCPServer()
        with patch.dict("os.environ", {"PARALLEL_API_KEY": "must-not-be-used"}):
            leads, errors = self.dispatch(server)
        self.assertEqual(errors, [])
        self.assertEqual(len(leads), 2)
        self.assertEqual(leads[0]["url"], "https://example.org/research")
        self.assertEqual(leads[1]["published"], "Date not supplied")
        self.assertIn("Public source excerpt.", web_context(leads))
        self.assertIn("not instructions", web_context(leads))
        self.assertIn("https://example.org/research", web_context(leads))
        calls = [message for _, message in server.requests if message["method"] == "tools/call"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["params"]["name"], "web_search")
        arguments = calls[0]["params"]["arguments"]
        self.assertEqual(arguments["search_queries"], [QUERY])
        self.assertIn(THEME, arguments["objective"])
        self.assertEqual(arguments["session_id"], "a" * 32)
        self.assertEqual(set(arguments), {"objective", "search_queries", "session_id"})
        self.assertIn("initialize", [message["method"] for _, message in server.requests])
        for request, _ in server.requests:
            self.assertEqual(str(request.url), parallel_search.MCP_URL)
            self.assertEqual(request.headers["User-Agent"], parallel_search.USER_AGENT)
            self.assertNotIn("Authorization", request.headers)

    def test_text_content_and_bounded_results(self):
        leads, errors = self.dispatch(MCPServer(text=True), count=1)
        self.assertEqual(errors, [])
        self.assertEqual(len(leads), 1)

    def test_existing_sources_and_deduplication_preserved(self):
        server = MCPServer()
        with server.installed(), patch("requests.get") as get, patch("requests.post") as post:
            get.return_value.json.side_effect = [
                {"articles": [{"title": "News", "url": "https://example.org/research"}]},
                {"web": {"results": [{"title": "Brave", "url": "https://brave.example/"}]}},
            ]
            post.return_value.json.return_value = {"data": {"web": [
                {"title": "Firecrawl", "url": "https://firecrawl.example/"}]}}
            leads, errors = search_theme(TIER, THEME, brave_key="saved-brave",
                                         firecrawl_key="saved-firecrawl", parallel=True)
        self.assertEqual(errors, [])
        self.assertEqual(len(leads), 4)
        self.assertEqual(leads[0]["provider"], "GDELT news index")
        self.assertEqual(get.call_args.kwargs["headers"]["X-Subscription-Token"], "saved-brave")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer saved-firecrawl")

    def test_disabled_and_invalid_input_never_connect(self):
        with patch.object(parallel_search.httpx, "AsyncClient") as client, patch("requests.get") as get:
            get.return_value.json.return_value = {"articles": []}
            search_theme(TIER, THEME)
            for tier, theme, count in [("bad", THEME, 1), (TIER, "bad", 1), (TIER, THEME, 0)]:
                with self.assertRaises(ValueError):
                    search_theme(tier, theme, count=count, parallel=True)
            client.assert_not_called()

    def test_provider_and_http_errors_are_visible_without_remote_details(self):
        for server in [MCPServer(error=True), MCPServer(status=401), MCPServer(status=429),
                       MCPServer(payload={"wrong": []}),
                       MCPServer(payload={"results": [{"url": 12}]})]:
            with self.subTest(server=server):
                leads, errors = self.dispatch(server)
                self.assertEqual(leads, [])
                self.assertIn("Parallel web search unavailable", errors[0])
                self.assertNotIn("private remote", str(errors))

    def test_timeout_closes_transport(self):
        server = MCPServer()
        original = server.handle

        async def slow(request):
            if json.loads(request.content)["method"] == "tools/call":
                await asyncio.sleep(10)
            return original(request)

        server.handle = slow
        with patch.object(parallel_search, "TIMEOUT_SECONDS", 0.05):
            leads, errors = self.dispatch(server)
        self.assertEqual(leads, [])
        self.assertIn("timed out", errors[0])

    def test_cancellation_propagates_and_closes_transport(self):
        server = MCPServer()
        original = server.handle

        async def exercise():
            started = asyncio.Event()

            async def slow(request):
                if json.loads(request.content)["method"] == "tools/call":
                    started.set()
                    await asyncio.sleep(10)
                return original(request)

            server.handle = slow
            with server.installed():
                task = asyncio.create_task(parallel_search._search({
                    "objective": THEME, "search_queries": [QUERY]}))
                await asyncio.wait_for(started.wait(), 2)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
