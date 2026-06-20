"""Tableau Metadata API client."""

from __future__ import annotations

from typing import Any

from .tableau_rest import TableauRestClient


class TableauMetadataClient:
    def __init__(self, rest: TableauRestClient) -> None:
        self.rest = rest

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        self.rest._ensure_session()
        return self.rest._request("POST", "/metadata/graphql", {"query": query, "variables": variables or {}})

    def lineage_for_asset(self, asset_id: str) -> dict[str, Any]:
        query = """
        query Lineage($id: ID!) {
          node(id: $id) { id name __typename }
        }
        """
        return self.graphql(query, {"id": asset_id})

