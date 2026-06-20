"""Desired-state diffing for Tableau BI specifications."""

from __future__ import annotations

import hashlib
from typing import Iterable

from .models import Action, BiSpec, ExecutionMode, Operation, Preview, TableauObject, TableauState


class Planner:
    def preview(self, spec: BiSpec, state: TableauState) -> Preview:
        actions = tuple(self._actions(spec, state))
        risks = self._risks(actions)
        approval_id = _approval_id(spec.stable_hash(), (action.idempotency_key for action in actions))
        return Preview(spec_hash=spec.stable_hash(), approval_id=approval_id, actions=actions, risks=risks)

    def _actions(self, spec: BiSpec, state: TableauState) -> Iterable[Action]:
        projects = _names(state.projects)
        datasources = _names(state.datasources)
        workbooks = _names(state.workbooks)

        for project in spec.projects:
            if project.name not in projects:
                yield Action(Operation.CREATE, "project", project.name, ExecutionMode.API, project.__dict__)

        for datasource in spec.datasources:
            if datasource.name not in datasources:
                payload = {"name": datasource.name, "project": datasource.project, "tables": len(datasource.tables)}
                yield Action(Operation.PUBLISH, "datasource", datasource.name, ExecutionMode.API, payload)

        for workbook in spec.workbooks:
            if workbook.name not in workbooks:
                payload = {"name": workbook.name, "project": workbook.project, "datasource": workbook.datasource}
                yield Action(Operation.AUTHOR, "workbook", workbook.name, ExecutionMode.PLAYWRIGHT, payload)

        for permission in spec.permissions:
            payload = permission.__dict__ | {"capabilities": list(permission.capabilities)}
            yield Action(Operation.UPDATE, "permission", permission.target_name, ExecutionMode.API, payload)

    @staticmethod
    def _risks(actions: tuple[Action, ...]) -> tuple[str, ...]:
        risks: list[str] = []
        if any(action.execution_mode == ExecutionMode.PLAYWRIGHT for action in actions):
            risks.append("Playwright authoring depends on Tableau UI stability and an authenticated browser session.")
        if any(action.target_type == "permission" for action in actions):
            risks.append("Permission updates can expose content to additional users or groups.")
        return tuple(risks)


def _names(objects: tuple[TableauObject, ...]) -> set[str]:
    return {item.name for item in objects}


def _approval_id(spec_hash: str, action_keys: Iterable[str]) -> str:
    payload = "|".join([spec_hash, *sorted(action_keys)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
