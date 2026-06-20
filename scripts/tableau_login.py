"""Open a headed Tableau login session and persist Playwright storage state."""

from __future__ import annotations

import argparse
from pathlib import Path
import time

from tableau_operator.config import TableauConfig
from tableau_operator.playwright_driver import PlaywrightAuthoringDriver


def main() -> None:
    args = _args()
    config = TableauConfig.from_env()
    driver = PlaywrightAuthoringDriver(config)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Install Playwright first: pip install -e .[dev] && playwright install chromium") from exc

    config.playwright_storage.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = _context(browser, config.playwright_storage)
        page = context.new_page()
        page.goto(driver.login_url(), wait_until="domcontentloaded")
        if args.manual:
            input("Complete Tableau login in the browser, then press Enter here to save the session...")
        elif args.autosave:
            print(f"Complete Tableau login in the opened browser. Autosaving for up to {args.timeout} seconds...")
            _autosave_until_timeout(context, config.playwright_storage, args.timeout, args.interval)
        else:
            print(f"Complete Tableau login in the opened browser. Waiting up to {args.timeout} seconds...")
            _wait_for_login(page, config.site_content_url, args.timeout)
        context.storage_state(path=str(config.playwright_storage))
        browser.close()
    print(f"Saved Tableau Playwright storage state: {config.playwright_storage}")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Persist Tableau browser auth for Playwright.")
    parser.add_argument("--autosave", action="store_true", help="Periodically persist browser state regardless of URL.")
    parser.add_argument("--interval", type=int, default=3, help="Autosave interval in seconds.")
    parser.add_argument("--manual", action="store_true", help="Wait for Enter instead of detecting the Tableau redirect.")
    parser.add_argument("--timeout", type=int, default=300, help="Seconds to wait for Tableau login completion.")
    return parser.parse_args()


def _wait_for_login(page, site_content_url: str, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        url = page.url.lower()
        if site_content_url.lower() in url and any(marker in url for marker in ("/home", "#/site/", "/site/")):
            return
        time.sleep(1)
    raise TimeoutError(f"Timed out waiting for Tableau login. Last URL: {page.url}")


def _autosave_until_timeout(context, storage_path: Path, timeout: int, interval: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        summary = _save_state(context, storage_path)
        print(f"Saved state snapshot: cookies={summary['cookies']} origins={summary['origins']}")
        time.sleep(max(1, interval))


def _save_state(context, storage_path: Path) -> dict[str, int]:
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    state = context.storage_state(path=str(storage_path))
    return {"cookies": len(state.get("cookies", [])), "origins": len(state.get("origins", []))}


def _context(browser, storage_path: Path):
    if storage_path.exists():
        return browser.new_context(storage_state=str(storage_path))
    return browser.new_context()


if __name__ == "__main__":
    main()
