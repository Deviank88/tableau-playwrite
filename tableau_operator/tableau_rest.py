"""Small Tableau REST client with injectable transport for tests."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable
from urllib import request

from .config import TableauConfig
from .models import TableauObject, TableauState


Transport = Callable[[str, str, dict[str, str], bytes | None], dict[str, Any]]


@dataclass(frozen=True)
class TableauSession:
    token: str
    site_id: str
    user_id: str


class TableauRestClient:
    def __init__(self, config: TableauConfig, transport: Transport | None = None) -> None:
        self.config = config
        self.transport = transport or _urllib_transport
        self.session: TableauSession | None = None

    def sign_in(self) -> TableauSession:
        payload = {
            "credentials": {
                "personalAccessTokenName": self.config.pat_name,
                "personalAccessTokenSecret": self.config.pat_secret,
                "site": {"contentUrl": self.config.site_content_url},
            }
        }
        data = self._request("POST", "/auth/signin", payload, auth=False)
        credentials = data["credentials"]
        self.session = TableauSession(
            token=credentials["token"],
            site_id=credentials["site"]["id"],
            user_id=credentials["user"]["id"],
        )
        return self.session

    def validate(self) -> dict[str, Any]:
        missing = self.config.missing_api_fields()
        if missing:
            return {"ok": False, "missing": missing}
        session = self.sign_in()
        return {"ok": True, "site_id": session.site_id, "user_id": session.user_id}

    def discover_state(self) -> TableauState:
        self._ensure_session()
        return TableauState(
            projects=tuple(self._list_objects("projects", "project")),
            datasources=tuple(self._list_objects("datasources", "datasource")),
            workbooks=tuple(self._list_objects("workbooks", "workbook")),
        )

    def _list_objects(self, endpoint: str, key: str) -> list[TableauObject]:
        session = self._ensure_session()
        data = self._request("GET", f"/sites/{session.site_id}/{endpoint}")
        items = data.get(endpoint, {}).get(key, [])
        return [
            TableauObject(
                name=item.get("name", ""),
                id=item.get("id"),
                project=item.get("project", {}).get("name"),
                content_url=item.get("contentUrl"),
            )
            for item in items
        ]

    def create_project(self, name: str, description: str = "", parent_project_id: str | None = None) -> dict[str, Any]:
        session = self._ensure_session()
        project: dict[str, Any] = {"name": name, "description": description}
        if parent_project_id:
            project["parentProjectId"] = parent_project_id
        return self._request("POST", f"/sites/{session.site_id}/projects", {"project": project})

    def _ensure_session(self) -> TableauSession:
        if self.session is None:
            self.sign_in()
        return self.session

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None, auth: bool = True) -> dict[str, Any]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if auth:
            session = self._ensure_session()
            headers["X-Tableau-Auth"] = session.token
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        url = f"{self.config.server_url}/api/{self.config.api_version}{path}"
        return self.transport(method, url, headers, body)


def _urllib_transport(method: str, url: str, headers: dict[str, str], body: bytes | None) -> dict[str, Any]:
    req = request.Request(url, data=body, headers=headers, method=method)
    with request.urlopen(req, timeout=30) as response:  # noqa: S310 - URL is user-configured Tableau endpoint.
        content = response.read().decode("utf-8")
    return json.loads(content) if content else {}
