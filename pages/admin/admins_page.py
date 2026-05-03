"""Admin UI: раздел /admins (платформенные администраторы).

Появился 2026-05-03. Heading и колонки на UZ ("Adminlar", "Ism", "Telefon",
"Holat", "Yaratilgan") даже когда выбрана RU-локаль — это bug-candidate
по mixed-locale, но для PoM фиксируем что есть.
"""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class AdminsPage(BasePage):
    URL_PATH = "/admins"

    # Колонки таблицы — UZ-имена в RU контексте.
    COLUMNS: tuple[str, ...] = ("Ism", "Telefon", "Holat", "Yaratilgan")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name="Adminlar", level=4
        )
        self._subtitle: Locator = page.get_by_text(
            "Platforma administratorlari"
        )
        self._add_button: Locator = page.get_by_role(
            "button", name="Yangi admin"
        )
        self._search_input: Locator = page.get_by_role(
            "textbox", name="Qidirish..."
        )
        self._table: Locator = page.get_by_role("table").first

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def subtitle(self) -> Locator:
        return self._subtitle

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def search_input(self) -> Locator:
        return self._search_input

    @property
    def table(self) -> Locator:
        return self._table

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def row_by_phone(self, phone: str) -> Locator:
        return self._table.get_by_role("row").filter(has_text=phone)

    def search(self, query: str) -> Self:
        self._search_input.fill(query)
        return self
