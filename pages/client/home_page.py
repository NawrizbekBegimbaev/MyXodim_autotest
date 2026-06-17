"""Client UI authenticated landing (/home)."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        # "Добро пожаловать, <ИМЯ>" — match by prefix.
        self.greeting: Locator = page.get_by_role("heading", name="Добро пожаловать")
        self.documents_nav: Locator = page.get_by_role("link", name="Исходящие документы")
        self.inbox_nav: Locator = page.get_by_role("link", name="Входящие документы")

    def open(self) -> HomePage:
        self.goto(f"{self.base_url}/home")
        return self
