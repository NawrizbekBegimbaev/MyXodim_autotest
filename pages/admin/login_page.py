"""Admin (platform) UI login (phone + password). Verified on staging."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class AdminLoginPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.phone_input: Locator = page.locator('input[name="phone"]')
        self.password_input: Locator = page.locator('input[name="password"]')
        self.login_button: Locator = page.get_by_role("button", name="Войти")

    def open(self) -> AdminLoginPage:
        self.goto(f"{self.base_url}/login")
        return self

    def login(self, phone: str, password: str) -> None:
        self.open()
        self.phone_input.fill(phone)
        self.password_input.fill(password)
        self.login_button.click()
