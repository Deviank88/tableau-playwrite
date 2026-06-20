"""Application service layer exposed by MCP tools."""

from __future__ import annotations

from dataclasses import asdict
import uuid
from typing import Any

from .audit import AuditEvent, AuditLog
from .config import TableauConfig
from .executor import ActionExecutor
from .metadata import TableauMetadataClient
from .models import BiSpec, Preview, TableauObject, TableauState
from .planner import Planner
from .playwright_driver import PlaywrightAuthoringDriver
from .safety import SafetyGate
from .tableau_rest import TableauRestClient


class TableauOperator:
    def __init__(self, config: TableauConfig) -> None:
        self.config = config
        self.rest = TableauRestClient(config)
        self.metadata = TableauMetadataClient(self.rest)
        self.planner = Planner()
        self.safety = SafetyGate(config)
        self.audit = AuditLog(config.audit_log)
        self.playwright = PlaywrightAuthoringDriver(config)
        self.executor = ActionExecutor(self.rest, self.playwright, self.audit)
        self._previews: dict[str, Preview] = {}

    def validate_connection(self) -> dict[str, Any]:
        api = self.rest.validate() if self.config.api_configured() else {"ok": False, "missing": self.config.missing_api_fields()}
        return {
            "api": api,
            "playwright": self.playwright.storage_state_status(),
            "playwright_login_url": self.playwright.login_url(),
            "allowed_projects": list(self.config.allowed_projects),
        }

    def discover_site(self) -> dict[str, Any]:
        if not self.config.api_configured():
            return {"mode": "playwright", "snapshot": self.playwright.snapshot_content("explore")}
        return asdict(self.rest.discover_state())

    def query_tableau_data(self, asset_id: str) -> dict[str, Any]:
        return self.metadata.lineage_for_asset(asset_id)

    def plan_bi_spec(self, goal: str) -> dict[str, Any]:
        project = self.config.allowed_projects[0] if self.config.allowed_projects else f"{self.config.project_name_prefix}{goal[:40]}"
        return {"name": goal, "projects": [{"name": project, "description": f"Workspace for {goal}"}]}

    def preview_bi_spec(self, spec_data: dict[str, Any], state_data: dict[str, Any] | None = None) -> dict[str, Any]:
        spec = BiSpec.from_dict(spec_data)
        state = _state_from_dict(state_data) if state_data else TableauState()
        preview = self.planner.preview(spec, state)
        self.safety.validate_preview(preview)
        self._previews[preview.approval_id] = preview
        return asdict(preview)

    def apply_bi_spec(self, approval_id: str) -> dict[str, Any]:
        preview = self._previews.get(approval_id)
        if preview is None:
            raise ValueError("unknown approval id; call preview_bi_spec first")
        self.safety.require_approval(preview, approval_id)
        run_id = str(uuid.uuid4())
        results = [self.executor.execute(run_id, action) for action in preview.actions]
        return {"run_id": run_id, "applied": len(results), "results": results}

    def open_authoring_session(self, datasource_content_url: str | None = None) -> dict[str, Any]:
        return asdict(self.playwright.open_authoring_session(datasource_content_url))

    def snapshot_tableau_ui(self, content_type: str = "home") -> dict[str, Any]:
        if content_type == "home":
            return self.playwright.snapshot_home()
        return self.playwright.snapshot_content(content_type)

    def click_tableau_ui(self, text: str, content_type: str = "home", role: str = "button", exact: bool = True) -> dict[str, Any]:
        self.audit.write(AuditEvent("ui_click_requested", str(uuid.uuid4()), {"content_type": content_type, "role": role, "text": text}))
        return self.playwright.click_and_snapshot(content_type, role, text, exact)

    def run_tableau_ui_steps(self, steps: list[dict[str, object]], content_type: str = "home") -> dict[str, Any]:
        self.audit.write(AuditEvent("ui_steps_requested", str(uuid.uuid4()), {"content_type": content_type, "steps": steps}))
        return self.playwright.run_steps_and_snapshot(content_type, steps)

    def capture_state(self, run_id: str) -> dict[str, str]:
        return self.playwright.capture_state(run_id, self.config.audit_log.parent / "captures")


def _state_from_dict(data: dict[str, Any]) -> TableauState:
    return TableauState(
        projects=tuple(TableauObject(**item) for item in data.get("projects", [])),
        datasources=tuple(TableauObject(**item) for item in data.get("datasources", [])),
        workbooks=tuple(TableauObject(**item) for item in data.get("workbooks", [])),
    )
