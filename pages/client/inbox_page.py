from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class InboxPage(BasePage):
    URL_PATH = "/inbox"

    COLUMNS: tuple[str, ...] = (
        "№",
        "Наименование",
        "Инициатор",
        "Дата начала",
        "Подпись",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.inbox.title"), level=4
        )
        self._subtitle: Locator = page.get_by_text(
            t("client.inbox.subtitle"), exact=True
        )
        self._refresh_button: Locator = page.get_by_role(
            "button", name=t("client.inbox.refresh"), exact=True
        )
        self._history_button: Locator = page.get_by_role(
            "button", name=t("client.inbox.history"), exact=True
        )
        self._search: Locator = page.get_by_placeholder(
            t("client.inbox.search_placeholder")
        )
        self._date_from: Locator = page.get_by_placeholder("дд.мм.гггг").first
        self._date_to: Locator = page.get_by_placeholder("дд.мм.гггг").nth(1)
        self._table: Locator = page.get_by_role("main").get_by_role("table")

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def subtitle(self) -> Locator:
        return self._subtitle

    @property
    def history_button(self) -> Locator:
        return self._history_button

    @property
    def refresh_button(self) -> Locator:
        return self._refresh_button

    @property
    def search_input(self) -> Locator:
        return self._search

    @property
    def search(self) -> Locator:
        return self._search

    @property
    def table(self) -> Locator:
        return self._table

    def fill_date_range(self, date_from: str, date_to: str) -> Self:
        self._date_from.fill(date_from)
        self._date_to.fill(date_to)
        return self

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def filter_chip(self, label: str) -> Locator:
        return self.page.get_by_text(label, exact=True)

    def empty_message(self) -> Locator:
        return self.page.get_by_text(t("client.inbox.empty_title"), exact=True)

    def status_tab(self, name: str) -> Locator:
        return self.filter_chip(name)
