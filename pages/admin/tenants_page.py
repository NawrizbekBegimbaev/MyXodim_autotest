"""Admin UI — companies list (/tenants)."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class TenantsPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.heading: Locator = page.get_by_role("heading", name="Компании")
        self.search: Locator = page.get_by_placeholder("Поиск...")

    def open(self) -> TenantsPage:
        self.goto(f"{self.base_url}/tenants")
        return self

    def find_row(self, name: str) -> Locator:
        self.search.fill(name)
        return self.page.get_by_role("row").filter(has_text=name)
