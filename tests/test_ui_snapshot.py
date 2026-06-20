import unittest
from unittest.mock import Mock

from tableau_operator.config import TableauConfig
from tableau_operator.ui_snapshot import (
    TableauUiSnapshotter,
    _clean,
    _dedupe,
    _index,
    _optional_int,
    _step,
    _validate_role,
    _visible_lines,
    _wait_for_body_text,
    _wait_for_tableau,
)


class UiSnapshotTests(unittest.TestCase):
    def test_content_url_allows_known_content_types(self):
        config = TableauConfig("https://tableau.example", "site", "", "", ())
        url = TableauUiSnapshotter(config).content_url("workbooks")
        self.assertEqual(url, "https://tableau.example/#/site/site/workbooks")

    def test_content_url_rejects_unknown_content_type(self):
        config = TableauConfig("https://tableau.example", "site", "", "", ())
        with self.assertRaisesRegex(ValueError, "unsupported"):
            TableauUiSnapshotter(config).content_url("admin")

    def test_click_role_validation_rejects_unknown_role(self):
        with self.assertRaisesRegex(ValueError, "unsupported click role"):
            _validate_role("combobox")

    def test_step_parses_click_defaults(self):
        step = _step({"action": "click", "text": "New"})
        self.assertEqual((step.action, step.role, step.text, step.index), ("click", "button", "New", 0))

    def test_step_parses_fill_index(self):
        step = _step({"action": "fill", "role": "textbox", "index": 1, "value": "Description"})
        self.assertEqual((step.action, step.role, step.index, step.value), ("fill", "textbox", 1, "Description"))

    def test_optional_int_rejects_zero(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            _optional_int(0)

    def test_index_rejects_negative(self):
        with self.assertRaisesRegex(ValueError, "zero or greater"):
            _index(-1)

    def test_visible_lines_cleans_dedupes_and_limits(self):
        self.assertEqual(_visible_lines(" A  B \n\nA B\n C ", limit=2), ["A B", "C"])

    def test_clean_normalizes_whitespace(self):
        self.assertEqual(_clean(" a\n\t b "), "a b")

    def test_dedupe_preserves_order(self):
        self.assertEqual(_dedupe(["a", "b", "a"]), ["a", "b"])

    def test_wait_for_tableau_falls_back_after_timeout(self):
        page = Mock()
        page.wait_for_load_state.side_effect = TimeoutError("busy")
        _wait_for_tableau(page, 1)
        page.wait_for_timeout.assert_called_once_with(1000)

    def test_wait_for_body_text_returns_when_text_exists(self):
        page = Mock()
        page.locator.return_value.inner_text.return_value = "Home"
        self.assertEqual(_wait_for_body_text(page, 1000), "Home")


if __name__ == "__main__":
    unittest.main()
