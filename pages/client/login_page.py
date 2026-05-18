from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class ClientLoginPage(BasePage):
    """Login в Client UI: телефон → OTP.

    Подтверждено разведкой: label "Номер телефона", кнопка "Отправить код".
    Префикс +998 показан отдельно — инпут принимает 9 цифр без префикса.
    """

    URL_PATH = "/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("login.client.heading"), level=5
        )
        self._subtitle: Locator = page.get_by_text(t("login.client.subtitle"), exact=True)
        self._phone_input: Locator = page.get_by_role(
            "textbox", name=t("login.client.phone_label")
        )
        self._submit: Locator = page.get_by_role("button", name=t("login.client.send_otp"))

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def subtitle(self) -> Locator:
        return self._subtitle

    @property
    def submit_button(self) -> Locator:
        return self._submit

    def enter_phone(self, phone: str) -> Self:
        # Поле ожидает 9 цифр без префикса +998 — нормализуем
        digits = phone.removeprefix("+998") if phone.startswith("+998") else phone
        self._phone_input.fill(digits)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self
