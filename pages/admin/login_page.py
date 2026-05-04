from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class AdminLoginPage(BasePage):
    """Login Super Admin в Admin UI: телефон + пароль.

    Подтверждено разведкой: label "Телефон" / "Пароль", кнопка "Войти".
    Использую get_by_role("textbox", ...) — `get_by_label("Пароль")` ловит кнопку-toggle.
    TODO (CLAUDE.md §14): попросить data-testid у фронта.
    """

    URL_PATH = "/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._phone_input: Locator = page.get_by_role(
            "textbox", name=t("login.admin.phone_label")
        )
        self._password_input: Locator = page.get_by_role(
            "textbox", name=t("login.admin.password_label")
        )
        self._submit: Locator = page.get_by_role("button", name=t("login.admin.submit"))

    def enter_credentials(self, phone: str, password: str) -> Self:
        # После BUG-015 fix фронт canonicalize'ит phone в '+998<9 цифр>'.
        # Input ограничен 9 цифрами (digitsOnly + maxLength=9), поэтому
        # передаём только локальную часть. Если получили "+998..." — strip.
        local_phone = phone.removeprefix("+998")
        self._phone_input.fill(local_phone)
        self._password_input.fill(password)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def login(self, phone: str, password: str) -> Self:
        return self.enter_credentials(phone, password).submit()

    @property
    def submit_button(self) -> Locator:
        return self._submit

    def invalid_creds_alert(self) -> Locator:
        return self.page.get_by_role("alert").filter(
            has_text=t("admin.login.invalid_creds_alert")
        )
