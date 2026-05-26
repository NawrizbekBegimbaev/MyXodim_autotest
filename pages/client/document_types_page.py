"""BRD 3.0 §25 — Виды документов для согласования (/document-types).

Сущность:
    Вид документа = template-метадата (имя, префикс, флаги QR/files) +
    опциональная ссылка на Группу. Несколько Видов могут принадлежать одной
    Группе (один-ко-многим). Используется при создании документов и
    в Маршрутах (через привязку к Группе).

Recon-наблюдения (2026-05-26, tenant [E2E recon] 8dgk1l, role admin):
    - Страница /document-types?search=&useQr=all&allowFiles=all&hasTemplate=all
      доступна admin'у. Heading h4 "Виды документов для согласования",
      subtitle "N вид(ов)".
    - Кнопка "Создать" в шапке. Поиск (placeholder "Название или префикс"),
      3 фильтра-комбобокса (QR код / Загрузка файлов / Есть шаблон, все со
      значением "Все"), кнопка "Сбросить" (disabled при дефолтном состоянии).
    - Таблица колонок: Файл, Наименование, Префикс, QR код, Загрузка файлов.
      Пример: 1 строка "ReconTemplate 0519" (— префикс), оба флага off.
    - Клик "Создать" ведёт на отдельную **страницу** /document-types/create
      (НЕ dialog). Поля:
        * Наименование * (textbox)
        * Группа видов документов (MUI Autocomplete, optional) — если групп
          нет в БД, popup показывает "No options"
        * Префикс (textbox) + helper "Заглавные буквы и цифры, макс. 20 символов"
        * Использовать QR код (checkbox)
        * Разрешить загрузку файлов (checkbox)
      Кнопки: "Сохранить", "Отмена".
    - Empty submit показывает helper-text "Наименование обязательно"
      (другое сообщение чем у /document-groups — там "Введите название").

ВАЖНО: ассертов в POM нет (CLAUDE.md §8). Все локаторы — через role+name
или label-aware.
"""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class DocumentTypesPage(BasePage):
    """Список видов документов /document-types."""

    URL_PATH = "/document-types"
    # Колонки live UI 2026-05-26.
    COLUMNS: tuple[str, ...] = (
        "Файл",
        "Наименование",
        "Префикс",
        "QR код",
        "Загрузка файлов",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.doc_types.title"), level=4
        )
        # Кнопка "Создать" — в шапке main (не в фильтрах).
        self._add_button: Locator = page.get_by_role(
            "main"
        ).get_by_role("button", name=t("client.doc_types.add_button"), exact=True)
        # Search-input у /document-types имеет label "Поиск" (accessible name) и
        # placeholder = "Название или префикс". Адресуем по placeholder,
        # чтобы не перепутать с другими search-инпутами на странице.
        self._search: Locator = page.get_by_placeholder(
            t("client.doc_types.search_placeholder"), exact=True
        )
        self._reset_filters: Locator = page.get_by_role(
            "main"
        ).get_by_role("button", name=t("client.doc_types.reset_filters"), exact=True)
        self._table: Locator = page.get_by_role("main").get_by_role("table")

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
    def reset_filters_button(self) -> Locator:
        return self._reset_filters

    @property
    def table(self) -> Locator:
        return self._table

    # --- действия ---

    def click_add(self) -> Self:
        """Клик "Создать" → переход на /document-types/create."""
        self._add_button.click()
        return self

    def search(self, query: str) -> Self:
        self._search.fill(query)
        return self

    # --- локаторы-геттеры (без ассертов) ---

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def row_by_name(self, name: str) -> Locator:
        """Строка таблицы по тексту во второй колонке "Наименование"."""
        return self._table.locator("tbody tr").filter(has_text=name)

    def filter_combobox(self, label: str) -> Locator:
        """Combobox-фильтр по тексту-лейблу (QR код / Загрузка файлов / Есть шаблон)."""
        return self.page.get_by_role("combobox", name=label, exact=True)


class DocumentTypeCreatePage(BasePage):
    """Страница /document-types/create.

    В отличие от групп (диалог), создание Вида — отдельная страница.
    Поле "Группа видов документов" — MUI Autocomplete, popup отдельный
    `.MuiAutocomplete-popper`; адресуем через label.
    """

    URL_PATH = "/document-types/create"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.doc_types.create_page_title")
        )
        # Back-кнопка ведёт обратно в список — название кнопки = заголовок раздела.
        self._back_button: Locator = page.get_by_role(
            "main"
        ).get_by_role("button", name=t("client.doc_types.back_button"), exact=True)
        # Поля: textbox с aria-label по label-тексту (MUI оборачивает label/input).
        self._name_input: Locator = page.get_by_role(
            "textbox", name=t("client.doc_types.field_name"), exact=True
        )
        # MUI Autocomplete — role=combobox, имя берёт из label-обёртки.
        self._group_combo: Locator = page.get_by_role(
            "combobox", name=t("client.doc_types.field_group"), exact=True
        )
        self._prefix_input: Locator = page.get_by_role(
            "textbox", name=t("client.doc_types.field_prefix"), exact=True
        )
        self._prefix_helper: Locator = page.get_by_text(
            t("client.doc_types.field_prefix_helper"), exact=True
        )
        self._qr_checkbox: Locator = page.get_by_role(
            "checkbox", name=t("client.doc_types.checkbox_use_qr"), exact=True
        )
        self._files_checkbox: Locator = page.get_by_role(
            "checkbox", name=t("client.doc_types.checkbox_allow_files"), exact=True
        )
        self._submit: Locator = page.get_by_role(
            "main"
        ).get_by_role("button", name=t("client.doc_types.create_submit"), exact=True)
        self._cancel: Locator = page.get_by_role(
            "main"
        ).get_by_role("button", name=t("client.doc_types.create_cancel"), exact=True)

    # --- свойства ---

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def back_button(self) -> Locator:
        return self._back_button

    @property
    def name_input(self) -> Locator:
        return self._name_input

    @property
    def group_combobox(self) -> Locator:
        return self._group_combo

    @property
    def prefix_input(self) -> Locator:
        return self._prefix_input

    @property
    def prefix_helper(self) -> Locator:
        return self._prefix_helper

    @property
    def qr_checkbox(self) -> Locator:
        return self._qr_checkbox

    @property
    def files_checkbox(self) -> Locator:
        return self._files_checkbox

    @property
    def submit_button(self) -> Locator:
        return self._submit

    @property
    def cancel_button(self) -> Locator:
        return self._cancel

    @property
    def error_name_required(self) -> Locator:
        """Helper-text "Наименование обязательно" после submit с пустым name."""
        return self.page.get_by_text(
            t("client.doc_types.error_name_required"), exact=True
        )

    @property
    def group_combobox_no_options(self) -> Locator:
        """MUI-Autocomplete popup-маркер "No options" — когда групп нет в БД."""
        return self.page.get_by_text(
            t("client.doc_types.combobox_no_options"), exact=True
        )

    # --- действия ---

    def fill_name(self, name: str) -> Self:
        self._name_input.fill(name)
        return self

    def fill_prefix(self, prefix: str) -> Self:
        self._prefix_input.fill(prefix)
        return self

    def open_group_combobox(self) -> Self:
        """Открыть MUI Autocomplete dropdown — click на input + Open button."""
        self._group_combo.click()
        return self

    def select_group(self, group_name: str) -> Self:
        """Выбор группы из dropdown. Заполнит filter-text и выберет option."""
        self._group_combo.fill(group_name)
        # MUI Autocomplete popup рисуется в portal, role=option.
        self.page.get_by_role("option", name=group_name, exact=True).click()
        return self

    def toggle_qr(self) -> Self:
        self._qr_checkbox.click()
        return self

    def toggle_files(self) -> Self:
        self._files_checkbox.click()
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
