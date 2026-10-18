import json
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from tests.test_parallel_search import MCPServer


APP = str(Path(__file__).resolve().parents[1] / "samson_app.py")


def button(app, label):
    return next(item for item in app.button if item.label == label)


class SamsonSearchTests(unittest.TestCase):
    def test_opt_in_search_reaches_queue_and_conversation_and_can_be_disabled(self):
        server = MCPServer()
        # No real credentials or saved Streamlit secrets are used by this path.
        with patch.dict("os.environ", {}, clear=True), \
                patch("streamlit.runtime.secrets.Secrets.get", return_value=""), \
                server.installed(), patch("requests.get") as news, \
                patch("scoring.samson.ask_samson", return_value="Scripted answer") as ask:
            news.return_value.json.return_value = {"articles": []}
            app = AppTest.from_file(APP, default_timeout=10).run()
            self.assertEqual(len(app.exception), 0)
            self.assertFalse(app.checkbox(key="include_parallel").value)
            self.assertTrue(button(app, "Send to Samson").disabled)
            button(app, "Search Internet sources").click().run()
            self.assertEqual(server.requests, [])

            app.session_state.samson_messages = [{"role": "user", "content": "PRIVATE PORTFOLIO"}]
            app.checkbox(key="include_parallel").check().run()
            self.assertEqual(server.requests, [])  # Enabling grants no automatic request.
            button(app, "Search Internet sources").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.session_state.web_leads), 2)
            self.assertIn("Public source excerpt.", "\n".join(item.value for item in app.text))
            first_session = app.session_state.parallel_search_session
            button(app, "Search Internet sources").click().run()
            self.assertEqual(app.session_state.parallel_search_session, first_session)
            calls = [message for _, message in server.requests if message["method"] == "tools/call"]
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0]["params"]["arguments"]["session_id"], first_session)
            self.assertNotIn("PRIVATE PORTFOLIO", json.dumps(calls))

            # Scripted model response: verify the real form passes search context downstream.
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-only"}):
                app.run()
                next(item for item in app.text_input if item.label.startswith("Ask about")).set_value("Review these sources")
                button(app, "Send to Samson").click().run()
            self.assertIn("https://example.org/research", ask.call_args.args[1])
            self.assertIn("Unverified source excerpt", ask.call_args.args[1])

            app.selectbox(key="web_status_widget_1_https://example.org/research").select("Dismiss").run()
            context = next(item.value for item in app.text if "No saved evaluations" in item.value)
            self.assertNotIn("https://example.org/research", context)
            app.checkbox(key="include_parallel").uncheck().run()
            button(app, "Search Internet sources").click().run()
            self.assertEqual(len([m for _, m in server.requests if m["method"] == "tools/call"]), 2)
            self.assertFalse(app.checkbox(key="include_parallel").value)

    def test_provider_failure_is_visible_in_normal_search_action(self):
        server = MCPServer(error=True)
        with patch.dict("os.environ", {}, clear=True), \
                patch("streamlit.runtime.secrets.Secrets.get", return_value=""), \
                server.installed(), patch("requests.get") as news:
            news.return_value.json.return_value = {"articles": []}
            app = AppTest.from_file(APP, default_timeout=10).run()
            app.checkbox(key="include_parallel").check().run()
            button(app, "Search Internet sources").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("Parallel web search unavailable" in item.value for item in app.warning))
            self.assertEqual(app.session_state.web_leads, [])


if __name__ == "__main__":
    unittest.main()
