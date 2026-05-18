from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class BranchesPage(BasePage):
    """Филиалы /branches — tree головного офиса."""

    URL_PATH = "/branches"
    COLUMNS: tuple[str, ...] = ("Филиал", "Тип", "Отделы", "Пользователи", "Действия")
    VIEW_TABS: tuple[str, ...] = ("Таблица", "Иерархия")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.branches.title"), level=4
        )
        self._subtitle: Locator = page.get_by_text(
            t("client.branches.subtitle"), exact=True
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.branches.add_button")
        )
        self._search: Locator = page.get_by_placeholder(
            t("client.branches.search_placeholder")
        )
        self._tab_table: Locator = page.get_by_role(
            "tab", name=t("client.branches.tab_table"), exact=True
        )
        self._tab_hierarchy: Locator = page.get_by_role(
            "tab", name=t("client.branches.tab_hierarchy"), exact=True
        )
        self._table: Locator = page.get_by_role("main").get_by_role("table")

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def subtitle(self) -> Locator:
        return self._subtitle

    @property
    def search_input(self) -> Locator:
        return self._search

    @property
    def table(self) -> Locator:
        return self._table

    def view_tab(self, name: str) -> Locator:
        return self.page.get_by_role("tab", name=name, exact=True)

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def branch_node(self, title: str) -> Locator:
        return self.page.get_by_role("heading", name=title, level=6, exact=True)


class BranchCreateDialog(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.branches.create_dialog_title")
        )
        self._title_input: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.branches.field_title")
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.branches.create_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.branches.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def fill_title(self, title: str) -> Self:
        self._title_input.fill(title)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
