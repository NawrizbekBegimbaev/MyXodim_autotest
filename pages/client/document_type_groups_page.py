"""BRD 3.0 §26 — Группы видов документов (/document-groups), Client UI / Admin role.

Сущность:
    Группа видов документов — справочник для группировки нескольких "Видов
    документов". Один Вид → одна Группа (BRD). Используется при создании
    документов, фильтрации, маршрутизации.

Recon-наблюдения (2026-05-25, tenant [E2E recon] 8dgk1l):
    - Страница /document-groups доступна admin'у.
    - Heading h4 "Группы видов документов", subtitle "N групп".
    - Кнопка "Создать", search-input "Поиск...", таблица колонка "Наименование".
    - Empty state: одна строка "Нет данных" в tbody.
    - Dialog "Создать":
        * **БАГ-КАНДИДАТ**: title диалога — "Добавить категорию"
          (copy/paste из /categories), placeholder поля — "Название категории".
          Ожидаемо: "Новая группа видов документов" / "Название группы".
        * input name="name" (НЕ required атрибут, но пустой submit показывает
          helper "Введите название" — server/client side validation сработала).
        * Кнопка "Создать" enabled даже при пустом name → клик показывает
          helper-text. Closes only после успешного POST.

ВАЖНО: POM без ассертов (CLAUDE.md §8). Текст dialog_title локализован в
i18n как `client.doc_groups.create_dialog_title` = текущий ("Добавить
категорию"). Когда фронт исправит — поменять в i18n, тесты автомат подхватят.
"""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class DocumentTypeGroupsPage(BasePage):
    """Список групп видов документов /document-groups."""

    URL_PATH = "/document-groups"
    COLUMNS: tuple[str, ...] = ("Наименование",)

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.doc_groups.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "main"
        ).get_by_role("button", name=t("client.doc_groups.add_button"), exact=True)
        self._search: Locator = page.get_by_placeholder(
            t("client.doc_groups.search_placeholder")
        )
        self._table: Locator = page.get_by_role("main").get_by_role("table")
        self._empty_cell: Locator = self._table.get_by_text(
            t("client.doc_groups.empty_state"), exact=True
        )

    # --- свойства ---

    @property
    def heading(self) -> Locator:
        return self._heading

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
    def empty_cell(self) -> Locator:
        return self._empty_cell

    # --- действия ---

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def search(self, query: str) -> Self:
        self._search.fill(query)
        return self

    # --- локаторы-геттеры ---

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def row_by_name(self, name: str) -> Locator:
        return self._table.locator("tbody tr").filter(has_text=name)


class DocumentTypeGroupCreateDialog(BasePage):
    """Dialog "Создать группу видов документов".

    Recon 2026-05-25: текущий title = "Добавить категорию" (BUG-кандидат).
    Используется константа i18n — когда фронт исправит, тесты подхватят.
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Используем dialog без strict name-фильтра (текст копипаст с /categories),
        # затем ищем элементы внутри.
        self._dialog: Locator = page.get_by_role("dialog")
        # input[name="name"] — единственный текстовый input в диалоге.
        self._name_input: Locator = self._dialog.locator('input[name="name"]')
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.doc_groups.dialog_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.doc_groups.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    @property
    def name_input(self) -> Locator:
        return self._name_input

    @property
    def submit_button(self) -> Locator:
        return self._submit

    @property
    def cancel_button(self) -> Locator:
        return self._cancel

    @property
    def error_text(self) -> Locator:
        """Helper-text валидации "Введите название" — появляется после
        submit с пустым name (recon 2026-05-25).
        """
        return self._dialog.get_by_text(
            t("client.doc_groups.error_name_required"), exact=True
        )

    def fill_name(self, name: str) -> Self:
        self._name_input.fill(name)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
