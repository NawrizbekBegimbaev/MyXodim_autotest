from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class OtpPage(BasePage):
    """Экран ввода OTP. Dev принимает любой 6-значный (TEST_OTP=123456)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("otp.heading"), level=5
        )
        self._code_input: Locator = page.get_by_label(t("otp.input_label")).or_(
            page.get_by_placeholder(t("otp.input_placeholder"))
        ).first
        self._submit: Locator = page.get_by_role("button", name=t("otp.submit"))

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def code_input(self) -> Locator:
        return self._code_input

    @property
    def submit_button(self) -> Locator:
        return self._submit

    def enter_code(self, code: str) -> Self:
        self._code_input.fill(code)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self
