from typing import Self

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class SelectOrganizationPage(BasePage):
    """Экран выбора организации после OTP (если пользователь в нескольких).

    Подтверждено разведкой: URL /tenant-select, каждая орг = button с inner
    heading level=6 (имя орг) + текст роли + "Войти".
    """

    URL_PATH = "/tenant-select"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role("heading", name="Выберите организацию")
        self._logout: Locator = page.get_by_role("button", name="Выйти")

    @property
    def heading(self) -> Locator:
        return self._heading

    def organization_card(self, name: str) -> Locator:
        # Карточка — button содержащая heading с именем орг (level=6).
        # exact=True чтобы "QaTeam" не матчил "SecondQaTeam" по substring.
        return self.page.get_by_role("button").filter(
            has=self.page.get_by_role("heading", name=name, level=6, exact=True)
        )

    def select(self, name: str) -> Self:
        self.organization_card(name).click()
        return self
