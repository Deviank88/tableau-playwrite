import unittest

from tableau_operator.config import TableauConfig
from tableau_operator.models import BiSpec, ExecutionMode, TableauObject, TableauState
from tableau_operator.planner import Planner
from tableau_operator.safety import SafetyError, SafetyGate


class PlannerSafetyTests(unittest.TestCase):
    def test_preview_creates_missing_assets(self):
        spec = BiSpec.from_dict(
            {
                "name": "Sales BI",
                "projects": [{"name": "AI Sandbox"}],
                "datasources": [{"name": "Sales Extract", "project": "AI Sandbox"}],
                "workbooks": [{"name": "Sales Dashboard", "project": "AI Sandbox", "datasource": "Sales Extract"}],
            }
        )
        preview = Planner().preview(spec, TableauState())
        self.assertEqual([action.target_type for action in preview.actions], ["project", "datasource", "workbook"])
        self.assertEqual(preview.actions[-1].execution_mode, ExecutionMode.PLAYWRIGHT)
        self.assertTrue(preview.approval_id)

    def test_existing_assets_are_not_recreated(self):
        spec = BiSpec.from_dict({"name": "Sales BI", "projects": [{"name": "AI Sandbox"}]})
        state = TableauState(projects=(TableauObject(name="AI Sandbox"),))
        self.assertEqual(Planner().preview(spec, state).actions, ())

    def test_safety_blocks_outside_project(self):
        config = TableauConfig("https://tableau.example", "site", "pat", "secret", ("AI Sandbox",))
        spec = BiSpec.from_dict({"name": "Ops BI", "projects": [{"name": "Other"}]})
        preview = Planner().preview(spec, TableauState())
        with self.assertRaisesRegex(SafetyError, "outside allowlist"):
            SafetyGate(config).validate_preview(preview)

    def test_approval_id_must_match_preview(self):
        config = TableauConfig("https://tableau.example", "site", "pat", "secret", ("AI Sandbox",))
        spec = BiSpec.from_dict({"name": "Sales BI", "projects": [{"name": "AI Sandbox"}]})
        preview = Planner().preview(spec, TableauState())
        with self.assertRaisesRegex(SafetyError, "approval id"):
            SafetyGate(config).require_approval(preview, "wrong")


if __name__ == "__main__":
    unittest.main()
