import json
import tempfile
import unittest
from pathlib import Path

from tableau_operator.audit import AuditEvent, AuditLog
from tableau_operator.config import TableauConfig
from tableau_operator.tableau_rest import TableauRestClient
from tableau_operator.tools import TableauOperator


class RestAndToolsTests(unittest.TestCase):
    def test_rest_sign_in_uses_pat_payload(self):
        seen = {}

        def transport(method, url, headers, body):
            seen.update(method=method, url=url, body=json.loads(body.decode("utf-8")))
            return {"credentials": {"token": "tok", "site": {"id": "site-id"}, "user": {"id": "user-id"}}}

        config = TableauConfig("https://tableau.example", "site", "pat-name", "pat-secret", ())
        session = TableauRestClient(config, transport).sign_in()
        self.assertEqual(session.site_id, "site-id")
        self.assertEqual(seen["body"]["credentials"]["personalAccessTokenName"], "pat-name")

    def test_audit_log_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "audit.jsonl"
            AuditLog(path).write(AuditEvent("test", "run", {"ok": True}))
            self.assertIn('"event": "test"', path.read_text(encoding="utf-8"))

    def test_apply_requires_preview_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            config = TableauConfig("https://tableau.example", "site", "pat", "secret", ("AI Sandbox",), audit_log=Path(temp) / "audit.jsonl")
            operator = TableauOperator(config)
            operator.rest.transport = lambda *_: {"credentials": {"token": "tok", "site": {"id": "site-id"}, "user": {"id": "user-id"}}}
            preview = operator.preview_bi_spec({"name": "Sales BI", "projects": [{"name": "AI Sandbox"}]})
            result = operator.apply_bi_spec(preview["approval_id"])
            self.assertEqual(result["applied"], 1)

    def test_discover_site_uses_playwright_without_pat(self):
        config = TableauConfig("https://tableau.example", "site", "", "", ())
        operator = TableauOperator(config)
        operator.playwright.snapshot_content = lambda content_type: {"content_type": content_type}
        self.assertEqual(operator.discover_site(), {"mode": "playwright", "snapshot": {"content_type": "explore"}})


if __name__ == "__main__":
    unittest.main()
