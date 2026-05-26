"""BRD 1.0 §6.4a — Mock 1C: Импорт документов в HUB.

ВНИМАНИЕ: на 2026-05-26 этот раздел UI ещё не имплементирован в Mock 1C.
См. BUG-007 в Bugs.txt. Этот POM-класс — placeholder для будущей
имплементации; все локаторы могут поменяться после повторного recon.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class ImportDocumentsPage(BasePage):
    """Раздел Mock 1C для импорта документов через integration documents."""

    URL_PATH = "/documents"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role("heading", name="Импорт документов")
        self._upload_button: Locator = page.get_by_role(
            "button", name="Импортировать в HUB"
        )
        self._file_input: Locator = page.locator('input[type="file"]')
        self._external_id_input: Locator = page.get_by_label("externalId")
        self._template_select: Locator = page.get_by_label("Шаблон")
        self._route_select: Locator = page.get_by_label("Маршрут")
        self._submit_button: Locator = page.get_by_role(
            "button", name="Импортировать"
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def upload_button(self) -> Locator:
        return self._upload_button

    @property
    def file_input(self) -> Locator:
        return self._file_input

    @property
    def external_id_input(self) -> Locator:
        return self._external_id_input

    @property
    def template_select(self) -> Locator:
        return self._template_select

    @property
    def route_select(self) -> Locator:
        return self._route_select

    @property
    def submit_button(self) -> Locator:
        return self._submit_button

