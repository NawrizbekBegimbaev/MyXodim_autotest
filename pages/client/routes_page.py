from __future__ import annotations

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

    По умолчанию имеет один шаг (start → step 1 → end). Минимальный тест:
    заполнить имя + Сохранить.
    """

    URL_PATH = "/routes/new"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._save_button: Locator = page.get_by_role(
            "button", name=t("client.routes.new_page_save"), exact=True
        )
        self._back_button: Locator = page.get_by_role(
            "button", name=t("client.routes.new_page_back"), exact=True
        )
        self._name_input: Locator = page.get_by_role(
            "textbox", name=t("client.routes.field_name_placeholder")
        )
        self._description_input: Locator = page.get_by_role(
            "textbox", name=t("client.routes.field_description_placeholder")
        )

    @property
    def save_button(self) -> Locator:
        return self._save_button

    @property
    def back_button(self) -> Locator:
        return self._back_button

    def fill_name(self, name: str) -> Self:
        self._name_input.fill(name)
        return self

    def fill_description(self, desc: str) -> Self:
        self._description_input.fill(desc)
        return self

    def save(self) -> Self:
        self._save_button.click()
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
