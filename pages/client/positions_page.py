from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class PositionsPage(BasePage):
    """Реестр должностей в Client UI (/positions)."""

    URL_PATH = "/positions"
    COLUMNS: tuple[str, ...] = ("Название должности", "Действия")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.positions.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.positions.add_button")
        )
        self._search: Locator = page.get_by_role(
            "textbox", name=t("client.positions.search_placeholder")
        )
        self._table: Locator = page.get_by_role("table").last

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def table(self) -> Locator:
        return self._table

    @property
    def search_input(self) -> Locator:
        return self._search

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def search(self, query: str) -> Self:
        self._search.fill(query)
        return self

    def row_by_title(self, title: str) -> Locator:
        return self._table.get_by_role("row").filter(has_text=title)

    def click_edit_for(self, title: str) -> Self:
        self.row_by_title(title).get_by_role(
            "button", name=t("client.positions.row_action_edit")
        ).click()
        return self

    def click_delete_for(self, title: str) -> Self:
        self.row_by_title(title).get_by_role(
            "button", name=t("client.positions.row_action_delete")
        ).click()
        return self
