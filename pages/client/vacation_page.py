"""BRD 3.0 / Мой кабинет / Отпуск.

DOC-002 conflict: BRD 1.0 §1 заявляет HR Out-of-scope, BRD 3.0 включает.
На 2026-05-26 UI — degenerate stub (один <p>Нет данных</p>), см. BUG-021.
POM минимален пока feature не имплементирован.
"""

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class VacationPage(BasePage):
    URL_PATH = "/vacation"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._empty: Locator = page.get_by_text(t("client.vacation.empty"), exact=True)

    @property
    def empty(self) -> Locator:
        return self._empty
