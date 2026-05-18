from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class MembersPage(BasePage):
    """Список пользователей (BRD «Сотрудники») /members в Client UI."""

    URL_PATH = "/members"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.members.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.members.add_button")
        )
        self._search_input: Locator = page.get_by_role(
            "textbox", name=t("client.members.search_placeholder")
        )
        # сначала role=table, потом строки в нём
        self._table: Locator = page.get_by_role("main").get_by_role("table")

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def table(self) -> Locator:
        return self._table

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def search(self, query: str) -> Self:
        self._search_input.fill(query)
        return self

    def row_by_phone(self, phone: str) -> Locator:
        # Каждая строка содержит cell с телефоном; ищем row у которой видно phone
        return self._table.get_by_role("row").filter(has_text=phone)

    def click_edit_for_phone(self, phone: str) -> Self:
        """В строке с указанным телефоном кликаем кнопку 'Редактировать'."""
        self.row_by_phone(phone).get_by_role(
            "button", name=t("client.members.row_action_edit")
        ).click()
        return self

    def click_disable_for_phone(self, phone: str) -> Self:
        """В строке с указанным телефоном кликаем кнопку 'Отключить'."""
        self.row_by_phone(phone).get_by_role(
            "button", name=t("client.members.row_action_disable")
        ).click()
        return self

    def status_cell_for_phone(self, phone: str) -> Locator:
        """Ячейка статуса в строке (колонка Статус)."""
        return self.row_by_phone(phone).get_by_role("cell").nth(4)

    def disable_button_for_phone(self, phone: str) -> Locator:
        return self.row_by_phone(phone).get_by_role(
            "button", name=t("client.members.row_action_disable")
        )

    def is_disable_button_disabled_for_phone(self, phone: str) -> Locator:
        return self.disable_button_for_phone(phone)

    def disable_self_tooltip(self) -> Locator:
        return self.page.get_by_text(
            t("client.members.tooltip_cant_disable_self"), exact=True
        )
