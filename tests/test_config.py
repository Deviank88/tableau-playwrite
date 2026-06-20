import os
import tempfile
import unittest
from pathlib import Path

from tableau_operator.config import TableauConfig, _dotenv_values


class ConfigTests(unittest.TestCase):
    def test_from_env_reads_dotenv_file(self):
        old_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temp:
            try:
                os.chdir(temp)
                Path(".env").write_text(
                    "TABLEAU_SERVER_URL=https://tableau.example/\n"
                    "TABLEAU_SITE_CONTENT_URL=site\n"
                    "TABLEAU_PAT_NAME=name\n"
                    "TABLEAU_PAT_SECRET=secret\n"
                    "TABLEAU_ALLOWED_PROJECTS=AI Sandbox,BI Sandbox\n",
                    encoding="utf-8",
                )
                _dotenv_values.cache_clear()
                config = TableauConfig.from_env()
            finally:
                os.chdir(old_cwd)
                _dotenv_values.cache_clear()

        self.assertEqual(config.server_url, "https://tableau.example")
        self.assertEqual(config.site_content_url, "site")
        self.assertEqual(config.allowed_projects, ("AI Sandbox", "BI Sandbox"))

    def test_api_configured_is_false_without_pat(self):
        config = TableauConfig("https://tableau.example", "site", "", "", ())
        self.assertFalse(config.api_configured())


if __name__ == "__main__":
    unittest.main()
