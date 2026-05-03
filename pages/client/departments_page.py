"""Client UI: раздел /departments (Отделы).

Появился 2026-05-03 в группе "Оргструктура". Read-only POM —
CRUD-методы будут добавлены отдельно (помечать creates_data).
"""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class DepartmentsPage(BasePage):
    URL_PATH = "/departments"

    COLUMNS: tuple[str, ...] = (
        "Название отдела",
        "Филиал",
        "Родитель",
        "Пользователи",
        "Источник",
        "Действия",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name="Отделы", level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name="Добавить отдел"
        )
        self._search_input: Locator = page.get_by_role(
            "textbox", name="Поиск по названию..."
        )
        self._branch_filter: Locator = page.get_by_role(
            "combobox", name="Филиал"
        )
        self._source_filter: Locator = page.get_by_role(
            "combobox", name="Источник"
        )
        self._table: Locator = page.get_by_role("table").first

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
