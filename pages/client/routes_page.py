from __future__ import annotations

import re
from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class RoutesPage(BasePage):
    """Список маршрутов /routes."""

    URL_PATH = "/routes"
    COLUMNS: tuple[str, ...] = (
        "Название",
        "Шаги",
        "Статус",
        "Version",
        "Последнее изменение",
        "Действия",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.routes.title"), level=4
        )
        self._create_button: Locator = page.get_by_role(
            "button", name=t("client.routes.create_button")
        )
        self._search: Locator = page.get_by_role(
            "textbox", name=t("client.routes.search_placeholder")
        )
        self._table: Locator = page.get_by_role("table").last

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def create_button(self) -> Locator:
        return self._create_button

    @property
    def table(self) -> Locator:
        return self._table

    @property
    def search_input(self) -> Locator:
        return self._search

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def click_create(self) -> Self:
        self._create_button.click()
        return self

    def search(self, query: str) -> Self:
        self._search.fill(query)
        return self

    def row_by_name(self, name: str) -> Locator:
        return self._table.get_by_role("row").filter(has_text=name)


class RouteEditorPage(BasePage):
    """Страница конструктора /routes/new (или /routes/{id}/edit).

    Recon 2026-05-26 (BRD 3.0):
        - H4 "Шаблоны маршрутов", статус-чип "Черновик"
        - Секция "Наименование" (h6) → input "Наименование *"
        - Секция "Группы видов документов" (h6) → MUI Autocomplete
          "Группы видов документов *" (multi-select; ссылка на ГРУППЫ,
          не на отдельные Виды, как было предположено в i18n изначально)
        - Секция "Этапы маршрута" (h6) → 1 дефолтный шаг с вложенными
          combobox'ами: Роль для согласований / Сотрудник / Подразделение
          + чип "Подписать" (action)
        - Внизу: "Готово" и "Сохранить изменения"
        - Empty submit показывает 3 валидации:
          "Введите название маршрута" / "Выберите хотя бы одну группу" /
          "Шаги без исполнителя: N"

    POM поддерживает: fill name, выбор Группы (single или multi), submit,
    и observers для validation-ошибок (read-only via `error_*` properties).
    """

    URL_PATH = "/routes/new"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._save_button: Locator = page.get_by_role(
            "button", name=t("client.routes.new_save_changes"), exact=True
        )
        self._done_button: Locator = page.get_by_role(
            "button", name=t("client.routes.new_done_button"), exact=True
        )
        # Legacy: на старом UI Save называли "Сохранить" — оставлен для совместимости.
        self._save_button_legacy: Locator = page.get_by_role(
            "button", name=t("client.routes.new_page_save"), exact=True
        )
        self._back_button: Locator = page.get_by_role(
            "button", name=t("client.routes.new_page_back"), exact=True
        )
        # Поле "Наименование *" — textbox с label-обёрткой.
        self._name_input: Locator = page.get_by_role(
            "textbox", name=t("client.routes.new_field_name_required"), exact=True
        )
        # Старый placeholder-based — fallback для legacy форм.
        self._name_input_legacy: Locator = page.get_by_role(
            "textbox", name=t("client.routes.field_name_placeholder")
        )
        self._description_input: Locator = page.get_by_role(
            "textbox", name=t("client.routes.field_description_placeholder")
        )
        # NEW (BRD 3.0): "Группы видов документов *" — MUI Autocomplete.
        # Адресуем через combobox+name (label-обёртка прокидывает aria-label).
        self._doc_groups_combobox: Locator = page.get_by_role(
            "combobox", name=t("client.routes.new_field_doc_groups_required"), exact=True
        )
        # Секционный heading h6 — для проверки структуры.
        self._doc_groups_section: Locator = page.get_by_role(
            "heading", name=t("client.routes.new_section_doc_groups"), level=6
        )

    # --- свойства ---

    @property
    def save_button(self) -> Locator:
        """Кнопка "Сохранить изменения" (recon 2026-05-26)."""
        return self._save_button

    @property
    def done_button(self) -> Locator:
        """Кнопка "Готово"."""
        return self._done_button

    @property
    def back_button(self) -> Locator:
        return self._back_button

    @property
    def name_input(self) -> Locator:
        return self._name_input

    @property
    def doc_groups_combobox(self) -> Locator:
        """MUI Autocomplete "Группы видов документов *". multi-select по реальной
        реализации (можно выбрать несколько групп).
        """
        return self._doc_groups_combobox

    @property
    def doc_groups_section(self) -> Locator:
        return self._doc_groups_section

    @property
    def error_name_required(self) -> Locator:
        return self.page.get_by_text(
            t("client.routes.new_error_name_required"), exact=True
        )

    @property
    def error_doc_groups_required(self) -> Locator:
        return self.page.get_by_text(
            t("client.routes.new_error_doc_groups_required"), exact=True
        )

    @property
    def error_steps_without_assignee(self) -> Locator:
        """Сообщение "Шаги без исполнителя: N" — N меняется, проверяем prefix."""
        return self.page.get_by_text(
            t("client.routes.new_error_steps_without_assignee")
        )

    # --- действия ---

    def fill_name(self, name: str) -> Self:
        """Заполнить "Наименование *". Fallback на legacy placeholder-локатор."""
        if self._name_input.count() > 0:
            self._name_input.fill(name)
        else:
            self._name_input_legacy.fill(name)
        return self

    def fill_description(self, desc: str) -> Self:
        self._description_input.fill(desc)
        return self

    def open_doc_groups_combobox(self) -> Self:
        """Открыть MUI Autocomplete popup для "Группы видов документов"."""
        self._doc_groups_combobox.click()
        return self

    def select_doc_group(self, group_name: str) -> Self:
        """Выбрать одну группу. Для multi-select вызвать несколько раз."""
        self._doc_groups_combobox.click()
        self._doc_groups_combobox.fill(group_name)
        # MUI Autocomplete popup — role=option в portal.
        self.page.get_by_role("option", name=group_name, exact=True).click()
        return self

    def select_doc_groups(self, group_names: list[str]) -> Self:
        """Multi-select: выбрать список групп подряд."""
        for name in group_names:
            self.select_doc_group(name)
        return self

    def save(self) -> Self:
        """Клик "Сохранить изменения" (текущий UI). Fallback на старый "Сохранить"."""
        if self._save_button.count() > 0:
            self._save_button.click()
        else:
            self._save_button_legacy.click()
        return self

    def click_default_step(self) -> RouteStepPanel:
        """Click на дефолтный 'Шаг 1' → открывает боковую panel настроек."""
        self.page.get_by_text(t("client.routes.step_default_label"), exact=True).click()
        return RouteStepPanel(self.page)


class RouteStepPanel(BasePage):
    """Боковая panel 'Настройки шага' (после клика на step в editor)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._panel_title: Locator = page.get_by_text(
            t("client.routes.step_panel_title"), exact=True
        )
        self._name_input: Locator = page.get_by_role(
            "textbox", name=t("client.routes.step_field_name_placeholder")
        )
        self._delete_button: Locator = page.get_by_role(
            "button", name=t("client.routes.step_delete_button"), exact=True
        )
        self._close_button: Locator = page.get_by_role(
            "button", name=t("client.routes.step_close_button"), exact=True
        )
        self._duration_spinbutton: Locator = page.get_by_role("spinbutton")
        self._target_type_combo: Locator = page.get_by_role(
            "combobox",
            name=re.compile(
                "|".join(
                    (
                        re.escape(t("client.routes.new_step_field_role")),
                        re.escape(t("client.routes.new_step_field_employee")),
                        re.escape(t("client.routes.new_step_field_department")),
                    )
                )
            ),
        ).first

    @property
    def panel_title(self) -> Locator:
        return self._panel_title

    @property
    def name_input(self) -> Locator:
        return self._name_input

    @property
    def delete_button(self) -> Locator:
        return self._delete_button

    @property
    def close_button(self) -> Locator:
        return self._close_button

    @property
    def target_type_combobox(self) -> Locator:
        return self._target_type_combo

    def fill_name(self, name: str) -> Self:
        self._name_input.fill(name)
        return self

    def click_action(self, action: str) -> Self:
        self.page.get_by_role("button", name=action, exact=True).click()
        return self

    def set_duration_days(self, days: int) -> Self:
        self._duration_spinbutton.fill(str(days))
        return self

    def close(self) -> Self:
        self._close_button.click()
        return self

    def delete_step(self) -> Self:
        self._delete_button.click()
        return self

    def target_option(self, name: str) -> Locator:
        return self.page.get_by_role("option", name=name, exact=True)

    def select_target_role(self, role_name: str) -> Self:
        self._select_target(t("client.routes.new_step_field_role"), role_name)
        return self

    def select_target_employee(self, employee_name: str) -> Self:
        self._select_target(t("client.routes.new_step_field_employee"), employee_name)
        return self

    def select_target_department(self, department_name: str) -> Self:
        self._select_target(
            t("client.routes.new_step_field_department"), department_name
        )
        return self

    def _select_target(self, target_type: str, target_value: str) -> None:
        self._target_type_combo.click()
        self.page.get_by_role("option", name=target_type, exact=True).click()
        self.page.get_by_role("combobox").last.click()
        self.page.get_by_role("option", name=target_value, exact=True).click()
