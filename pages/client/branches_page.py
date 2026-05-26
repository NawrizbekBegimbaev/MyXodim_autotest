"""Филиалы /branches — Client UI. Покрывает BRD 2.0 (BHUB-38..48):

- Список + Иерархия (две таб-вкладки)
- Head office создаётся автоматически при tenant create (BHUB-38)
- Sub-branch CRUD через "Добавить филиал" / row "Редактировать" (BHUB-39)
- Edit dialog для head не содержит "Родительский офис" — отличается от edit child

ВАЖНО: ассертов внутри POM нет — только локаторы и действия. CLAUDE.md §8.
"""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class BranchesPage(BasePage):
    """Филиалы /branches — таблица + иерархия головного офиса."""

    URL_PATH = "/branches"
    # Колонки из live UI snapshot 2026-05-25 (recon).
    COLUMNS: tuple[str, ...] = (
        "Филиал",
        "Тип",
        "Отделы",
        "Пользователи",
        "Действия",
    )
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
        # Таблица — внутри <main>, чтобы не зацепить sidebar nav.
        self._table: Locator = page.get_by_role("main").get_by_role("table")

    # --- свойства ---

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
        return self._search

    @property
    def table(self) -> Locator:
        return self._table

    @property
    def tab_table(self) -> Locator:
        return self._tab_table

    @property
    def tab_hierarchy(self) -> Locator:
        return self._tab_hierarchy

    # --- действия ---

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def search(self, query: str) -> Self:
        self._search.fill(query)
        return self

    def switch_to_table(self) -> Self:
        self._tab_table.click()
        return self

    def switch_to_hierarchy(self) -> Self:
        self._tab_hierarchy.click()
        return self

    # --- локаторы-геттеры (без ассертов) ---

    def view_tab(self, name: str) -> Locator:
        return self.page.get_by_role("tab", name=name, exact=True)

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def row_by_title(self, title: str) -> Locator:
        """Строка таблицы по title (title — текст в первой колонке "Филиал")."""
        return self._table.locator("tbody tr").filter(has_text=title)

    def head_row(self) -> Locator:
        """Строка с типом "Главный офис" — в `[E2E recon]` орге она ровно одна."""
        return self._table.locator("tbody tr").filter(
            has_text=t("client.branches.type_head")
        )

    def head_edit_button(self) -> Locator:
        """Кнопка "Редактировать" в строке head-офиса."""
        return self.head_row().get_by_role(
            "button", name=t("client.branches.row_action_edit")
        )

    def row_edit_button(self, title: str) -> Locator:
        return self.row_by_title(title).get_by_role(
            "button", name=t("client.branches.row_action_edit")
        )

    def branch_node(self, title: str) -> Locator:
        """Уникальный текст филиала — в карточке Иерархии или ячейке таблицы.

        Для одного значения title в таблице может быть несколько вхождений
        (ячейка + бейдж "Активен" в той же ячейке), поэтому `.first`.
        """
        return self.page.get_by_text(title, exact=True).first

    def hierarchy_card_for_head(self) -> Locator:
        """Карточка head-офиса в Иерархии содержит бейдж "HEAD"."""
        # Карточка — общий контейнер с текстом и type-badge.
        return self.page.locator("main").get_by_text(
            t("client.branches.head_badge"), exact=True
        )


class BranchCreateDialog(BasePage):
    """Диалог "Новый филиал" — Название (обяз) + Родительский офис (обяз)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.branches.create_dialog_title")
        )
        # name input — type="text", name="name"
        self._title_input: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.branches.field_title")
        )
        self._parent_combo: Locator = self._dialog.get_by_role(
            "combobox", name=t("client.branches.field_parent")
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

    @property
    def title_input(self) -> Locator:
        return self._title_input

    @property
    def parent_combo(self) -> Locator:
        return self._parent_combo

    @property
    def submit_button(self) -> Locator:
        return self._submit

    def fill_title(self, title: str) -> Self:
        self._title_input.fill(title)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self


class BranchEditDialog(BasePage):
    """Диалог "Редактировать филиал". Для head НЕ показывает поле parent."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.branches.edit_dialog_title")
        )
        self._title_input: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.branches.field_title")
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.branches.edit_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.branches.dialog_cancel"), exact=True
        )
        # Поле "Родительский офис" — может отсутствовать (head office). Локатор
        # просто адресует label, наличие проверяет тест через .count().
        self._parent_label: Locator = self._dialog.get_by_text(
            t("client.branches.field_parent"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    @property
    def title_input(self) -> Locator:
        return self._title_input

    @property
    def parent_label(self) -> Locator:
        return self._parent_label

    def fill_title(self, title: str) -> Self:
        self._title_input.fill(title)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
