from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class PositionsPage(BasePage):
    """BRD 3.0: Должности (jobTitle) — отдельная сущность."""

    URL_PATH = "/positions"
    COLUMNS: tuple[str, ...] = (
        t("client.positions.col_title"),
        t("client.positions.col_code"),
        t("client.positions.col_created_at"),
        t("client.positions.col_actions"),
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.positions.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.positions.add_button")
        )
        self._search: Locator = page.get_by_placeholder(
            t("client.positions.search_placeholder")
        )
        self._code_filter: Locator = page.get_by_label(
            t("client.positions.filter_code"), exact=True
        )
        self._date_from_filter: Locator = page.get_by_label(
            t("client.positions.filter_date_from"), exact=True
        )
        self._date_to_filter: Locator = page.get_by_label(
            t("client.positions.filter_date_to"), exact=True
        )
        self._reset_filters_button: Locator = page.get_by_role(
            "button", name=t("client.positions.reset_filters"), exact=True
        )
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

    @property
    def search_input(self) -> Locator:
        return self._search

    @property
    def code_filter(self) -> Locator:
        return self._code_filter

    @property
    def date_from_filter(self) -> Locator:
        return self._date_from_filter

    @property
    def date_to_filter(self) -> Locator:
        return self._date_to_filter

    @property
    def reset_filters_button(self) -> Locator:
        return self._reset_filters_button

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def search(self, query: str) -> Self:
        self._search.fill(query)
        return self

    def filter_by_code(self, code: str) -> Self:
        self._code_filter.fill(code)
        return self

    def filter_by_date_range(self, date_from: str, date_to: str) -> Self:
        self._date_from_filter.fill(date_from)
        self._date_to_filter.fill(date_to)
        return self

    def reset_filters(self) -> Self:
        self._reset_filters_button.click()
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

    def open_card(self, position_name: str) -> Self:
        self.row_by_title(position_name).get_by_role(
            "button", name=t("client.positions.row_action_open_card"), exact=True
        ).click()
        return self


class PositionDetailPage(BasePage):
    """Карточка должности, открываемая row action 'Открыть карточку'."""

    def __init__(self, page: Page, position_name: str) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role("heading", name=position_name)

    @property
    def heading(self) -> Locator:
        return self._heading
