"""Read-only Playwright snapshots for Tableau UI pages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import time
import uuid

from .config import TableauConfig


@dataclass(frozen=True)
class UiElement:
    role: str
    text: str


@dataclass(frozen=True)
class UiStep:
    action: str
    text: str = ""
    role: str = "button"
    value: str = ""
    exact: bool = True
    index: int = 0
    timeout_ms: int | None = None


@dataclass(frozen=True)
class UiSnapshot:
    run_id: str
    url: str
    title: str
    screenshot: str | None
    text: tuple[str, ...]
    links: tuple[UiElement, ...]
    buttons: tuple[UiElement, ...]


class TableauUiSnapshotter:
    def __init__(self, config: TableauConfig) -> None:
        self.config = config

    def snapshot(self, url: str | None = None, screenshot: bool = True, timeout_ms: int = 30000) -> UiSnapshot:
        return self._visit(url or self.home_url(), None, screenshot, timeout_ms)

    def click_and_snapshot(
        self,
        content_type: str,
        role: str,
        text: str,
        exact: bool = True,
        screenshot: bool = True,
        timeout_ms: int = 30000,
    ) -> UiSnapshot:
        _validate_role(role)
        url = self.home_url() if content_type == "home" else self.content_url(content_type)
        return self._visit(url, [UiStep("click", text=text, role=role, exact=exact)], screenshot, timeout_ms)

    def run_steps_and_snapshot(
        self,
        content_type: str,
        steps: list[dict[str, object]],
        screenshot: bool = True,
        timeout_ms: int = 30000,
    ) -> UiSnapshot:
        url = self.home_url() if content_type == "home" else self.content_url(content_type)
        return self._visit(url, [_step(step) for step in steps], screenshot, timeout_ms)

    def _visit(
        self,
        target_url: str,
        steps: list[UiStep] | None,
        screenshot: bool,
        timeout_ms: int,
    ) -> UiSnapshot:
        self._require_storage_state()
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is required for Tableau UI snapshots") from exc

        run_id = str(uuid.uuid4())
        screenshot_path = self._screenshot_path(run_id) if screenshot else None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(storage_state=str(self.config.playwright_storage))
            page = context.new_page()
            page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
            _wait_for_tableau(page, timeout_ms)
            for step in steps or []:
                _run_step(page, step, timeout_ms)
                _wait_for_tableau(page, step.timeout_ms or timeout_ms)
            body_text = _wait_for_body_text(page, timeout_ms)
            if screenshot_path:
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path), full_page=True)
            snapshot = UiSnapshot(
                run_id=run_id,
                url=page.url,
                title=page.title(),
                screenshot=str(screenshot_path) if screenshot_path else None,
                text=tuple(_visible_lines(body_text)),
                links=tuple(_elements(page, "a")),
                buttons=tuple(_elements(page, "button")),
            )
            browser.close()
        return snapshot

    def home_url(self) -> str:
        return f"{self.config.server_url}/#/site/{self.config.site_content_url}/home"

    def content_url(self, content_type: str) -> str:
        allowed = {"projects", "workbooks", "datasources", "views", "explore"}
        if content_type not in allowed:
            raise ValueError(f"unsupported Tableau content type: {content_type}")
        return f"{self.config.server_url}/#/site/{self.config.site_content_url}/{content_type}"

    def _require_storage_state(self) -> None:
        if not self.config.playwright_storage.exists():
            raise RuntimeError(f"missing Playwright storage state: {self.config.playwright_storage}")

    def _screenshot_path(self, run_id: str) -> Path:
        return self.config.audit_log.parent / "screenshots" / f"{run_id}.png"


def _visible_lines(text: str, limit: int = 80) -> list[str]:
    lines = [line for line in (_clean(line) for line in text.splitlines()) if line]
    return _dedupe(lines)[:limit]


def _elements(page, selector: str, limit: int = 50) -> list[UiElement]:
    items: list[UiElement] = []
    for item in page.locator(selector).all()[:limit]:
        try:
            text = _clean(item.inner_text(timeout=1000))
        except Exception:
            continue
        if text:
            items.append(UiElement(selector, text))
    return items


def _run_step(page, step: UiStep, default_timeout_ms: int) -> None:
    timeout_ms = step.timeout_ms or default_timeout_ms
    if step.action == "click":
        _target(page, UiElement(step.role, step.text), step.exact, step.index).click(timeout=timeout_ms)
        return
    if step.action == "fill":
        _target(page, UiElement(step.role, step.text), step.exact, step.index).fill(step.value, timeout=timeout_ms)
        return
    if step.action == "wait":
        page.wait_for_timeout(timeout_ms)
        return
    raise ValueError(f"unsupported UI step action: {step.action}")


def _click(page, element: UiElement, exact: bool, timeout_ms: int) -> None:
    _target(page, element, exact, 0).click(timeout=timeout_ms)


def _fill(page, element: UiElement, value: str, exact: bool, timeout_ms: int) -> None:
    _target(page, element, exact, 0).fill(value, timeout=timeout_ms)


def _target(page, element: UiElement, exact: bool, index: int):
    if index < 0:
        raise ValueError("index must be zero or greater")
    if element.role == "text":
        return page.get_by_text(element.text, exact=exact).nth(index)
    if element.text:
        return page.get_by_role(element.role, name=element.text, exact=exact).nth(index)
    return page.get_by_role(element.role).nth(index)


def _validate_role(role: str) -> None:
    allowed = {"button", "link", "menuitem", "tab", "text", "textbox"}
    if role not in allowed:
        raise ValueError(f"unsupported click role: {role}")


def _step(data: dict[str, object]) -> UiStep:
    action = _str(data, "action")
    role = str(data.get("role", "button"))
    _validate_role(role)
    return UiStep(
        action=action,
        text=str(data.get("text", "")),
        role=role,
        value=str(data.get("value", "")),
        exact=bool(data.get("exact", True)),
        index=_index(data.get("index", 0)),
        timeout_ms=_optional_int(data.get("timeout_ms")),
    )


def _str(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"UI step requires non-empty {key}")
    return value


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise ValueError("timeout_ms must be a positive integer")
    return value


def _index(value: object) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError("index must be zero or greater")
    return value


def _wait_for_tableau(page, timeout_ms: int) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        page.wait_for_timeout(1000)


def _wait_for_body_text(page, timeout_ms: int) -> str:
    deadline = time.monotonic() + (timeout_ms / 1000)
    last_text = ""
    while time.monotonic() < deadline:
        try:
            last_text = page.locator("body").inner_text(timeout=1000)
        except Exception:
            last_text = ""
        if _visible_lines(last_text, limit=1):
            return last_text
        page.wait_for_timeout(500)
    return last_text


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
