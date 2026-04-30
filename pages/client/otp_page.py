from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class OtpPage(BasePage):
    """Экран ввода OTP. Dev принимает любой 6-значный (TEST_OTP=123456)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._code_input: Locator = page.get_by_label(t("otp.input_label"))
        self._submit: Locator = page.get_by_role("button", name=t("otp.submit"))

    def enter_code(self, code: str) -> Self:
        self._code_input.fill(code)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self
