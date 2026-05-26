"""Client UI: BRD 3.0 раздел /departments (Подразделения)."""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class DepartmentsPage(BasePage):
    URL_PATH = "/departments"

    COLUMNS: tuple[str, ...] = (
        t("client.departments.col_name"),
        t("client.departments.col_code"),
        t("client.departments.col_parent"),
        t("client.departments.col_branch"),
        t("client.departments.col_actions"),
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.departments.title"), level=4
        ).or_(
            page.get_by_role("heading", name="Отделы", level=4)
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.departments.add_button")
        ).or_(
            page.get_by_role("button", name="Добавить отдел")
        )
        self._search_input: Locator = page.get_by_placeholder(
            t("client.departments.search_placeholder")
        )
        self._branch_filter: Locator = page.get_by_role(
            "combobox", name=t("client.departments.col_branch")
        )
        self._source_filter: Locator = page.get_by_role(
            "combobox", name="Источник"
        )
        self._table: Locator = page.get_by_role("main").get_by_role("table")

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def search_input(self) -> Locator:
        return self._search_input

    @property
    def branch_filter(self) -> Locator:
        return self._branch_filter

    @property
    def source_filter(self) -> Locator:
        return self._source_filter

    @property
    def table(self) -> Locator:
        return self._table

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def row_by_name(self, name: str) -> Locator:
        return self._table.get_by_role("row").filter(has_text=name)

    def search(self, query: str) -> Self:
        self._search_input.fill(query)
        return self

    def filter_by_branch(self, label: str) -> Self:
        self._branch_filter.click()
        self.page.get_by_role("option", name=label, exact=True).click()
        return self

    def filter_by_source(self, label: str) -> Self:
        self._source_filter.click()
        self.page.get_by_role("option", name=label, exact=True).click()
        return self

    def click_add(self) -> Self:
        self._add_button.click()
        return self


class DepartmentCreateDialog(BasePage):
    """Dialog создания подразделения.

    BUG-015: Branch combobox отсутствует в текущем UI, хотя BRD ожидает выбор
    филиала. Локатор branch намеренно не добавлен.
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.departments.create_dialog_title")
        )
        self._name_input: Locator = self._dialog.get_by_label(
            t("client.departments.field_name"), exact=False
        )
        self._parent_combo: Locator = self._dialog.get_by_label(
            t("client.departments.field_parent"), exact=True
        )
        self._code_input: Locator = self._dialog.get_by_label(
            t("client.departments.field_code"), exact=True
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.departments.create_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.departments.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    @property
    def name_input(self) -> Locator:
        return self._name_input

    @property
    def parent_combo(self) -> Locator:
        return self._parent_combo

    @property
    def code_input(self) -> Locator:
        return self._code_input

    def fill_name(self, name: str) -> Self:
        self._name_input.fill(name)
        return self

    def fill_code(self, code: str) -> Self:
        self._code_input.fill(code)
        return self

    def select_parent(self, parent_name: str) -> Self:
        self._parent_combo.click()
        self.page.get_by_role("option", name=parent_name, exact=True).click()
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
