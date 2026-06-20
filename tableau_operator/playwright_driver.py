"""Playwright boundary for Tableau web authoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import uuid

from .config import TableauConfig
from .ui_snapshot import TableauUiSnapshotter


@dataclass(frozen=True)
class AuthoringSession:
    run_id: str
    url: str
    storage_state_exists: bool


class PlaywrightAuthoringDriver:
    def __init__(self, config: TableauConfig) -> None:
        self.config = config

    def new_workbook_url(self, datasource_content_url: str | None = None) -> str:
        guid = uuid.uuid4()
        base = f"{self.config.server_url}/t/{self.config.site_content_url}"
        if datasource_content_url:
            return f"{base}/authoringNewWorkbook/{guid}/{datasource_content_url}"
        return f"{base}/newWorkbook/{guid}"

    def login_url(self) -> str:
        if self.config.login_url:
            return self.config.login_url
        return f"{self.config.server_url}/#/site/{self.config.site_content_url}/home"

    def storage_state_status(self) -> dict[str, object]:
        path = self.config.playwright_storage
        if not path.exists():
            return {"exists": False, "valid_json": False, "cookies": 0, "origins": 0}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"exists": True, "valid_json": False, "cookies": 0, "origins": 0}
        return {
            "exists": True,
            "valid_json": True,
            "cookies": len(data.get("cookies", [])),
            "origins": len(data.get("origins", [])),
        }

    def open_authoring_session(self, datasource_content_url: str | None = None) -> AuthoringSession:
        url = self.new_workbook_url(datasource_content_url)
        return AuthoringSession(run_id=str(uuid.uuid4()), url=url, storage_state_exists=self.config.playwright_storage.exists())

    def capture_state(self, run_id: str, output_dir: Path) -> dict[str, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        return {"run_id": run_id, "output_dir": str(output_dir)}

    def snapshot_home(self) -> dict[str, object]:
        return asdict(TableauUiSnapshotter(self.config).snapshot())

    def snapshot_content(self, content_type: str) -> dict[str, object]:
        snapshotter = TableauUiSnapshotter(self.config)
        return asdict(snapshotter.snapshot(snapshotter.content_url(content_type)))

    def click_and_snapshot(self, content_type: str, role: str, text: str, exact: bool = True) -> dict[str, object]:
        return asdict(TableauUiSnapshotter(self.config).click_and_snapshot(content_type, role, text, exact))

    def run_steps_and_snapshot(self, content_type: str, steps: list[dict[str, object]]) -> dict[str, object]:
        return asdict(TableauUiSnapshotter(self.config).run_steps_and_snapshot(content_type, steps))
