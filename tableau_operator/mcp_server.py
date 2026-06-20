"""MCP transport for Tableau Operator."""

from __future__ import annotations

from typing import Any

from .config import TableauConfig
from .tools import TableauOperator


def build_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install the 'mcp' package to run the MCP server") from exc

    operator = TableauOperator(TableauConfig.from_env())
    mcp = FastMCP("tableau-operator")

    @mcp.tool()
    def validate_connection() -> dict[str, Any]:
        return operator.validate_connection()

    @mcp.tool()
    def discover_site() -> dict[str, Any]:
        return operator.discover_site()

    @mcp.tool()
    def query_tableau_data(asset_id: str) -> dict[str, Any]:
        return operator.query_tableau_data(asset_id)

    @mcp.tool()
    def plan_bi_spec(goal: str) -> dict[str, Any]:
        return operator.plan_bi_spec(goal)

    @mcp.tool()
    def preview_bi_spec(spec: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any]:
        return operator.preview_bi_spec(spec, state)

    @mcp.tool()
    def apply_bi_spec(approval_id: str) -> dict[str, Any]:
        return operator.apply_bi_spec(approval_id)

    @mcp.tool()
    def open_authoring_session(datasource_content_url: str | None = None) -> dict[str, Any]:
        return operator.open_authoring_session(datasource_content_url)

    @mcp.tool()
    def snapshot_tableau_ui(content_type: str = "home") -> dict[str, Any]:
        return operator.snapshot_tableau_ui(content_type)

    @mcp.tool()
    def click_tableau_ui(text: str, content_type: str = "home", role: str = "button", exact: bool = True) -> dict[str, Any]:
        return operator.click_tableau_ui(text, content_type, role, exact)

    @mcp.tool()
    def run_tableau_ui_steps(steps: list[dict[str, object]], content_type: str = "home") -> dict[str, Any]:
        return operator.run_tableau_ui_steps(steps, content_type)

    @mcp.tool()
    def capture_state(run_id: str) -> dict[str, str]:
        return operator.capture_state(run_id)

    @mcp.resource("tableau://catalog")
    def catalog() -> dict[str, Any]:
        return operator.discover_site()

    @mcp.resource("tableau://lineage/{asset_id}")
    def lineage(asset_id: str) -> dict[str, Any]:
        return operator.query_tableau_data(asset_id)

    @mcp.resource("tableau://runs/{run_id}")
    def run(run_id: str) -> dict[str, str]:
        return operator.capture_state(run_id)

    @mcp.resource("tableau://screenshots/{run_id}")
    def screenshots(run_id: str) -> dict[str, str]:
        return operator.capture_state(run_id)

    return mcp


def main() -> None:
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
