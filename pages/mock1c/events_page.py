"""BRD 1.0 §6.4 — Mock 1C: Event Queue Consumer.

ВНИМАНИЕ: на 2026-05-26 раздел UI не имплементирован. См. BUG-012.
Этот POM — placeholder. Локаторы могут поменяться когда фронт появится.
"""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class EventsPage(BasePage):
    """Mock 1C → раздел Event Queue (BRD §6.4)."""

    URL_PATH = "/events"

    COLUMNS: tuple[str, ...] = (
        "sequenceNumber",
        "timestamp",
        "type",
        "payload",
        "status",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role("heading", name="События")
        self._poll_button: Locator = page.get_by_role("button", name="Опросить HUB")
        self._table: Locator = page.get_by_role("main").get_by_role("table")
        self._bulk_delete: Locator = page.get_by_role(
            "button", name="Удалить обработанные"
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def poll_button(self) -> Locator:
        return self._poll_button

    @property
    def table(self) -> Locator:
        return self._table

    @property
    def bulk_delete_button(self) -> Locator:
        return self._bulk_delete

    def row_by_sequence(self, seq: int) -> Locator:
        return self._table.locator("tbody tr").filter(has_text=str(seq))

    def process_row(self, seq: int) -> Self:
        row = self.row_by_sequence(seq)
        row.get_by_role("button", name="Обработать").click()
        return self

    def delete_row(self, seq: int) -> Self:
        row = self.row_by_sequence(seq)
        row.get_by_role("button", name="Удалить").click()
        return self

