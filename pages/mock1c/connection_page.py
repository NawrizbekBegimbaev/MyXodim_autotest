"""Mock 1C UI connection screen (no login — integration-key based)."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class Mock1cConnectionPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.heading: Locator = page.get_by_role("heading", name="Mock 1C")
        self.key_input: Locator = page.get_by_placeholder("bh_live_...")
        self.save_button: Locator = page.get_by_role("button", name="Сохранить")

    def open(self) -> Mock1cConnectionPage:
        self.goto(f"{self.base_url}/")
        return self
