"""Base page object: navigation + load helpers. No asserts here (asserts live in tests)."""

from __future__ import annotations

from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded")

    def wait_loaded(self) -> None:
        # Do NOT use networkidle — this SPA keeps live connections open
        # (notification polling), so it never settles. Assert on a concrete
        # element via expect() in tests instead.
        self.page.wait_for_load_state("domcontentloaded")
