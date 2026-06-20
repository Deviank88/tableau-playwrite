"""Configuration loading for Tableau MCP Operator."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path


@lru_cache
def _dotenv_values(path: Path = Path(".env")) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, _dotenv_values().get(name, default))


def _split_csv(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class TableauConfig:
    server_url: str
    site_content_url: str
    pat_name: str
    pat_secret: str
    allowed_projects: tuple[str, ...]
    login_url: str = ""
    project_name_prefix: str = ""
    playwright_storage: Path = Path(".tableau-auth/storage-state.json")
    audit_log: Path = Path("logs/audit.jsonl")
    api_version: str = "3.23"
    allow_destructive: bool = False

    @classmethod
    def from_env(cls) -> "TableauConfig":
        return cls(
            server_url=_env("TABLEAU_SERVER_URL").rstrip("/"),
            site_content_url=_env("TABLEAU_SITE_CONTENT_URL"),
            pat_name=_env("TABLEAU_PAT_NAME"),
            pat_secret=_env("TABLEAU_PAT_SECRET"),
            allowed_projects=tuple(_split_csv(_env("TABLEAU_ALLOWED_PROJECTS"))),
            login_url=_env("TABLEAU_LOGIN_URL"),
            project_name_prefix=_env("TABLEAU_PROJECT_NAME_PREFIX"),
            playwright_storage=Path(_env("TABLEAU_PLAYWRIGHT_STORAGE", ".tableau-auth/storage-state.json")),
            audit_log=Path(_env("TABLEAU_AUDIT_LOG", "logs/audit.jsonl")),
            api_version=_env("TABLEAU_API_VERSION", "3.23"),
            allow_destructive=_as_bool(_env("TABLEAU_ALLOW_DESTRUCTIVE"), False),
        )

    def missing_api_fields(self) -> list[str]:
        required = {
            "TABLEAU_SERVER_URL": self.server_url,
            "TABLEAU_SITE_CONTENT_URL": self.site_content_url,
            "TABLEAU_PAT_NAME": self.pat_name,
            "TABLEAU_PAT_SECRET": self.pat_secret,
        }
        return [name for name, value in required.items() if not value]

    def api_configured(self) -> bool:
        return not self.missing_api_fields()
