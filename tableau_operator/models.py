"""Typed desired-state models for Tableau BI operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any


class Operation(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    AUTHOR = "author"


class ExecutionMode(StrEnum):
    API = "api"
    PLAYWRIGHT = "playwright"
    MANUAL_REQUIRED = "manual_required"


@dataclass(frozen=True)
class BiColumn:
    name: str
    type: str = "text"
    nullable: bool = True


@dataclass(frozen=True)
class BiTable:
    name: str
    columns: tuple[BiColumn, ...] = ()
    rows: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class BiProject:
    name: str
    description: str = ""
    parent: str | None = None


@dataclass(frozen=True)
class BiDatasource:
    name: str
    project: str
    tables: tuple[BiTable, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class BiWorkbook:
    name: str
    project: str
    datasource: str | None = None
    dashboards: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class BiPermission:
    target_type: str
    target_name: str
    grantee: str
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class BiSpec:
    name: str
    projects: tuple[BiProject, ...] = ()
    datasources: tuple[BiDatasource, ...] = ()
    workbooks: tuple[BiWorkbook, ...] = ()
    permissions: tuple[BiPermission, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BiSpec":
        spec = cls(
            name=_required_str(data, "name"),
            projects=tuple(BiProject(**item) for item in data.get("projects", [])),
            datasources=tuple(_datasource(item) for item in data.get("datasources", [])),
            workbooks=tuple(_workbook(item) for item in data.get("workbooks", [])),
            permissions=tuple(_permission(item) for item in data.get("permissions", [])),
            metadata=dict(data.get("metadata", {})),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        _ensure_unique("project", (project.name for project in self.projects))
        _ensure_unique("datasource", (datasource.name for datasource in self.datasources))
        _ensure_unique("workbook", (workbook.name for workbook in self.workbooks))
        project_names = {project.name for project in self.projects}
        for datasource in self.datasources:
            _require_project(project_names, datasource.project, f"datasource {datasource.name}")
        for workbook in self.workbooks:
            _require_project(project_names, workbook.project, f"workbook {workbook.name}")

    def stable_hash(self) -> str:
        payload = json.dumps(_to_plain(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TableauObject:
    name: str
    id: str | None = None
    project: str | None = None
    content_url: str | None = None


@dataclass(frozen=True)
class TableauState:
    projects: tuple[TableauObject, ...] = ()
    datasources: tuple[TableauObject, ...] = ()
    workbooks: tuple[TableauObject, ...] = ()


@dataclass(frozen=True)
class Action:
    operation: Operation
    target_type: str
    target_name: str
    execution_mode: ExecutionMode
    payload: dict[str, Any] = field(default_factory=dict)
    destructive: bool = False

    @property
    def idempotency_key(self) -> str:
        base = f"{self.operation}:{self.target_type}:{self.target_name}:{self.execution_mode}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Preview:
    spec_hash: str
    approval_id: str
    actions: tuple[Action, ...]
    risks: tuple[str, ...] = ()
    unsupported: tuple[str, ...] = ()


def _datasource(data: dict[str, Any]) -> BiDatasource:
    tables = tuple(_table(item) for item in data.get("tables", []))
    return BiDatasource(
        name=_required_str(data, "name"),
        project=_required_str(data, "project"),
        tables=tables,
        description=data.get("description", ""),
    )


def _table(data: dict[str, Any]) -> BiTable:
    return BiTable(
        name=_required_str(data, "name"),
        columns=tuple(BiColumn(**item) for item in data.get("columns", [])),
        rows=tuple(dict(row) for row in data.get("rows", [])),
    )


def _workbook(data: dict[str, Any]) -> BiWorkbook:
    return BiWorkbook(
        name=_required_str(data, "name"),
        project=_required_str(data, "project"),
        datasource=data.get("datasource"),
        dashboards=tuple(data.get("dashboards", [])),
        description=data.get("description", ""),
    )


def _permission(data: dict[str, Any]) -> BiPermission:
    return BiPermission(
        target_type=_required_str(data, "target_type"),
        target_name=_required_str(data, "target_name"),
        grantee=_required_str(data, "grantee"),
        capabilities=tuple(data.get("capabilities", [])),
    )


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _ensure_unique(label: str, values: Any) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {label}: {value}")
        seen.add(value)


def _require_project(projects: set[str], project: str, label: str) -> None:
    if projects and project not in projects:
        raise ValueError(f"{label} references unknown project: {project}")


def _to_plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _to_plain(getattr(value, key)) for key in value.__dataclass_fields__}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, StrEnum):
        return str(value)
    return value
