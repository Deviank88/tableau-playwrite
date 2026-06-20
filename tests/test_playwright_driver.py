import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from tableau_operator.config import TableauConfig
from tableau_operator.playwright_driver import PlaywrightAuthoringDriver
from scripts.tableau_login import _save_state, _wait_for_login


class PlaywrightDriverTests(unittest.TestCase):
    def test_new_workbook_url_without_datasource(self):
        config = TableauConfig("https://tableau.example", "site", "pat", "secret", ())
        url = PlaywrightAuthoringDriver(config).new_workbook_url()
        self.assertTrue(url.startswith("https://tableau.example/t/site/newWorkbook/"))

    def test_new_workbook_url_with_datasource(self):
        config = TableauConfig("https://tableau.example", "site", "pat", "secret", ())
        url = PlaywrightAuthoringDriver(config).new_workbook_url("SalesExtract")
        self.assertIn("/authoringNewWorkbook/", url)
        self.assertTrue(url.endswith("/SalesExtract"))

    def test_login_url_prefers_configured_url(self):
        config = TableauConfig("https://tableau.example", "site", "pat", "secret", (), login_url="https://login.example")
        self.assertEqual(PlaywrightAuthoringDriver(config).login_url(), "https://login.example")

    def test_storage_state_status_reads_json(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "storage.json"
            path.write_text('{"cookies": [{"name": "x"}], "origins": []}', encoding="utf-8")
            config = TableauConfig("https://tableau.example", "site", "pat", "secret", (), playwright_storage=path)
            self.assertEqual(PlaywrightAuthoringDriver(config).storage_state_status()["cookies"], 1)

    def test_wait_for_login_returns_when_site_url_is_reached(self):
        page = Mock(url="https://tableau.example/#/site/site/home")
        _wait_for_login(page, "site", 1)

    def test_wait_for_login_accepts_site_url_without_home(self):
        page = Mock(url="https://tableau.example/#/site/site/projects")
        _wait_for_login(page, "site", 1)

    def test_wait_for_login_times_out_on_login_url(self):
        page = Mock(url="https://tableau.example/login")
        with patch("scripts.tableau_login.time.sleep", return_value=None):
            with self.assertRaises(TimeoutError):
                _wait_for_login(page, "site", 0)

    def test_save_state_returns_cookie_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            context = Mock()
            context.storage_state.return_value = {"cookies": [{"name": "sid"}], "origins": [{"origin": "https://tableau.example"}]}
            self.assertEqual(_save_state(context, path), {"cookies": 1, "origins": 1})
            context.storage_state.assert_called_once_with(path=str(path))


if __name__ == "__main__":
    unittest.main()
