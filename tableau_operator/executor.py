"""Execution boundary for approved Tableau actions."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .audit import AuditEvent, AuditLog
from .models import Action, ExecutionMode
from .playwright_driver import PlaywrightAuthoringDriver
from .tableau_rest import TableauRestClient


class ActionExecutor:
    def __init__(self, rest: TableauRestClient, playwright: PlaywrightAuthoringDriver, audit: AuditLog) -> None:
        self.rest = rest
        self.playwright = playwright
        self.audit = audit

    def execute(self, run_id: str, action: Action) -> dict[str, Any]:
        self.audit.write(AuditEvent("mutation_started", run_id, asdict(action)))
        result = self._execute(action)
        self.audit.write(AuditEvent("mutation_finished", run_id, {"action": action.idempotency_key, "result": result}))
        return result

    def _execute(self, action: Action) -> dict[str, Any]:
        if action.execution_mode == ExecutionMode.PLAYWRIGHT:
            session = self.playwright.open_authoring_session(action.payload.get("datasource_content_url"))
            return {"mode": "playwright", "authoring_session": asdict(session)}
        if action.target_type == "project" and action.operation == "create":
            return {"mode": "api", "response": self.rest.create_project(action.target_name, action.payload.get("description", ""))}
        return {"mode": "manual_required", "reason": f"no executor for {action.operation}:{action.target_type}"}

