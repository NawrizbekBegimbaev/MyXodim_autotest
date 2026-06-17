"""Client UI inbox ("Требуют подписи", /inbox) + document approval action."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class InboxPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.heading: Locator = page.get_by_role("heading", name="Требуют подписи")
        self.rows: Locator = page.get_by_role("row")

    def open(self) -> InboxPage:
        self.goto(f"{self.base_url}/inbox")
        return self

    def open_first_task(self) -> None:
        # Click the first data row (skip the header row).
        self.rows.nth(1).click()

    def approve(self) -> None:
        """Approve the open document (action «Согласовать»)."""
        self.page.get_by_role("button", name="Согласовать").first.click()
