"""Client UI documents list (/documents)."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class DocumentsPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.heading: Locator = page.get_by_role("heading", name="Документы")
        self.create_button: Locator = page.get_by_role("button", name="Запустить документ")

    def open(self) -> DocumentsPage:
        self.goto(f"{self.base_url}/documents")
        return self

    def start_new_document(self) -> None:
        self.create_button.click()
