"""Hyper extract creation boundary."""

from __future__ import annotations

from pathlib import Path

from .models import BiDatasource


class HyperService:
    def create_extract(self, datasource: BiDatasource, output_dir: Path) -> Path:
        try:
            from tableauhyperapi import HyperProcess  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("tableauhyperapi is required to create Hyper extracts") from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{datasource.name}.hyper"
        path.touch(exist_ok=True)
        return path

