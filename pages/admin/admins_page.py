"""Admin UI — platform admins list + create (/admins)."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class AdminsPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.heading: Locator = page.get_by_role("heading", name="Администраторы")
        self.new_admin_button: Locator = page.get_by_role("button", name="Новый администратор")
        # Create form
        self.name_input: Locator = page.get_by_role("textbox", name="Имя")
        self.phone_input: Locator = page.get_by_role("textbox", name="Телефон")
        self.submit_button: Locator = page.get_by_role("button", name="Сохранить")

    def open(self) -> AdminsPage:
        self.goto(f"{self.base_url}/admins")
        return self

    def create(self, full_name: str, phone: str) -> None:
        self.new_admin_button.click()
        self.name_input.fill(full_name)
        self.phone_input.fill(phone)
        self.submit_button.click()
        # Success dialog "Администратор создан — сохраните пароль" → close it.
        close = self.page.get_by_role("button", name="Закрыть")
        close.wait_for(state="visible", timeout=15_000)
        close.click()

    def row(self, text: str) -> Locator:
        return self.page.get_by_role("row").filter(has_text=text)
