from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class PersonsPage(BasePage):
    URL_PATH = "/persons"

    COLUMNS: tuple[str, ...] = (
        "ФИО",
        "ПИНФЛ",
        "Дата рождения",
        "Email",
        "Телефон",
        "Источник",
        "Статус",
        "Действия",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.persons.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.persons.add_button"), exact=True
        )
        self._search: Locator = page.get_by_placeholder(
            t("client.persons.search_placeholder")
        )
        self._filter_combobox: Locator = page.get_by_role("combobox").first
        self._table: Locator = page.get_by_role("main").get_by_role("table")

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def search_input(self) -> Locator:
        return self._search

    @property
    def search(self) -> Locator:
        return self._search

    @property
    def table(self) -> Locator:
        return self._table

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)
