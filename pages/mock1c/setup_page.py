from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class Mock1CSetupPage(BasePage):
    """Главная Mock 1C — поле ключа + кнопка Сохранить + статус."""

    URL_PATH = "/"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("mock1c.setup_heading"), level=2
        )
        self._key_input: Locator = page.get_by_role("textbox").first
        self._save_button: Locator = page.get_by_role(
            "button", name=t("mock1c.save_button"), exact=True
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def key_input(self) -> Locator:
        return self._key_input

    @property
    def save_button(self) -> Locator:
        return self._save_button

    def status_connected(self) -> Locator:
        return self.page.get_by_text(t("mock1c.status_connected"), exact=True).first

    def fill_key(self, key: str) -> Self:
        self._key_input.fill(key)
        return self

    def save(self) -> Self:
        self._save_button.click()
        return self

    def ensure_russian_locale(self) -> Self:
        """Mock 1C может остаться в UZ от прошлой сессии. Если видим узбекские
        тексты — переключаем на русский (button 'RU' в banner).
        """
        page = self.page
        # До 3 попыток (язык может persist'иться в localStorage)
        for _ in range(3):
            if page.get_by_role("link", name="Подключение").count() > 0:
                return self
            try:
                page.get_by_role("button", name="RU").click(timeout=2_000)
                page.wait_for_timeout(1_500)
            except Exception:
                page.reload(wait_until="networkidle")
                page.wait_for_timeout(1_500)
        return self


class Mock1CDataPage(BasePage):
    """База для /positions /employees /templates Mock 1C — общая структура."""

    SECTION_HEADING_KEY: str = ""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t(self.SECTION_HEADING_KEY), level=2
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("mock1c.add_button"), exact=True
        )
        self._send_all: Locator = page.get_by_role(
            "button", name=t("mock1c.send_all_button"), exact=True
        )
        self._table: Locator = page.get_by_role("table").last

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def send_all_button(self) -> Locator:
        return self._send_all

    @property
    def table(self) -> Locator:
        return self._table


class Mock1CPositionsPage(Mock1CDataPage):
    URL_PATH = "/positions"
    SECTION_HEADING_KEY = "mock1c.nav_positions"


class Mock1CEmployeesPage(Mock1CDataPage):
    URL_PATH = "/employees"
    SECTION_HEADING_KEY = "mock1c.nav_employees"


class Mock1CTemplatesPage(Mock1CDataPage):
    URL_PATH = "/templates"
    SECTION_HEADING_KEY = "mock1c.nav_templates"
