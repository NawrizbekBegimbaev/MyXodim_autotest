"""Admin UI dashboard (/dashboard) and tenants list."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class AdminDashboardPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.heading: Locator = page.get_by_role("heading", name="Дашборд")
        self.tenants_nav: Locator = page.get_by_role("link", name="Компании")

    def open_tenants(self) -> None:
        self.tenants_nav.click()
