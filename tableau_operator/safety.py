"""Mutation safety checks for Tableau actions."""

from __future__ import annotations

from dataclasses import dataclass

from .config import TableauConfig
from .models import Action, Preview


class SafetyError(ValueError):
    """Raised when a requested Tableau mutation violates the configured safety policy."""


@dataclass(frozen=True)
class SafetyGate:
    config: TableauConfig

    def validate_preview(self, preview: Preview) -> None:
        for action in preview.actions:
            self.validate_action(action)

    def validate_action(self, action: Action) -> None:
        if action.destructive and not self.config.allow_destructive:
            raise SafetyError(f"destructive action blocked: {action.target_name}")
        project = action.payload.get("project") or action.payload.get("target_project")
        if project:
            self._validate_project(project)
        if action.target_type == "project":
            self._validate_project(action.target_name)

    def require_approval(self, preview: Preview, approval_id: str) -> None:
        if approval_id != preview.approval_id:
            raise SafetyError("approval id does not match preview")
        self.validate_preview(preview)

    def _validate_project(self, project: str) -> None:
        if self.config.allowed_projects and project not in self.config.allowed_projects:
            raise SafetyError(f"project is outside allowlist: {project}")
        prefix = self.config.project_name_prefix
        if prefix and project not in self.config.allowed_projects and not project.startswith(prefix):
            raise SafetyError(f"project must start with configured prefix: {prefix}")
