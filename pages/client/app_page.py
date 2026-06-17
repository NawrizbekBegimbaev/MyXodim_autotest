"""Generic Client UI page: navigate to a route and expose shell/heading/create
locators. Used by the navigation/page-load sanity cases (8-27)."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class ClientAppPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        # App shell rendered = user is authenticated and a route mounted.
        self.shell: Locator = page.get_by_role("button", name="User menu")

    def open(self, route: str) -> ClientAppPage:
        # No networkidle wait: the SPA keeps live connections (notification
        # polling) so networkidle never settles. Tests assert on a concrete
        # element via auto-retrying expect() instead.
        self.goto(f"{self.base_url}{route}")
        return self

    def heading(self, text: str) -> Locator:
        return self.page.get_by_role("heading", name=text).first

    def button(self, text: str) -> Locator:
        return self.page.get_by_role("button", name=text).first
