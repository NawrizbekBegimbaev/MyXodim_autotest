"""Client UI login (phone + OTP). Locators verified on staging (RU locale)."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class ClientLoginPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        # Phone step
        self.phone_input: Locator = page.locator('input[name="phone"]')
        self.send_code_button: Locator = page.get_by_role("button", name="Отправить код")
        # OTP step
        self.otp_input: Locator = page.locator('input[name="otp"]')
        self.login_button: Locator = page.get_by_role("button", name="Войти")

    def open(self) -> ClientLoginPage:
        self.goto(f"{self.base_url}/login")
        return self

    def request_otp(self, phone: str) -> ClientLoginPage:
        """Fill phone and request a code. Tolerates the staging 60s OTP
        rate-limit (429) by waiting and retrying the request."""
        self.phone_input.fill(phone)
        # Fresh phones don't hit the cooldown; one retry bounds the worst case
        # if a 429 (rate-limit) does occur.
        for _ in range(2):
            self.send_code_button.click()
            try:
                self.otp_input.wait_for(state="visible", timeout=8_000)
                return self
            except Exception:
                self.page.wait_for_timeout(62_000)
        self.otp_input.wait_for(state="visible", timeout=8_000)
        return self

    def submit_otp(self, otp: str) -> None:
        self.otp_input.fill(otp)
        self.login_button.click()

    def login(self, phone: str, otp: str) -> None:
        """Full UI login: phone -> request OTP -> enter OTP -> submit."""
        self.open()
        self.request_otp(phone)
        self.submit_otp(otp)
