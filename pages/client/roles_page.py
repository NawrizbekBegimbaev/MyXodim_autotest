from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class RolesPage(BasePage):
    """Кастомные роли /roles."""

    URL_PATH = "/roles"
    COLUMNS: tuple[str, ...] = ("Название роли", "Права доступа", "Действия")
    PERM_GROUPS: tuple[str, ...] = (
        t("client.roles.group_docflow"),
        t("client.roles.group_hr"),
        t("client.roles.group_finance"),
        t("client.roles.group_settings"),
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.roles.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.roles.add_button")
        )
        self._table: Locator = page.get_by_role("table").last

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def table(self) -> Locator:
        return self._table

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def row_by_title(self, title: str) -> Locator:
        return self.page.get_by_role("row").filter(has_text=title)

    def click_edit_first_row(self) -> Self:
        """Клик 'Редактировать' на первой data-row (для теста edit-page)."""
        self.page.get_by_role("row").nth(1).get_by_role(
            "button", name=t("client.roles.row_action_edit")
        ).click()
        return self


class RoleEditPage(BasePage):
    """Страница редактирования роли /roles/{id}/edit с permissions matrix."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.roles.edit_page_title"), level=4
        )
        self._back_button: Locator = page.get_by_role(
            "button", name=t("client.roles.edit_back"), exact=True
        )
        self._save_button: Locator = page.get_by_role(
            "button", name=t("client.roles.edit_save"), exact=True
        )
        self._search_perms: Locator = page.get_by_role(
            "textbox", name=t("client.roles.edit_search_permissions")
        )
        self._expand_all: Locator = page.get_by_role(
            "button", name=t("client.roles.edit_expand_all"), exact=True
        )
        self._collapse_all: Locator = page.get_by_role(
            "button", name=t("client.roles.edit_collapse_all"), exact=True
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def back_button(self) -> Locator:
        return self._back_button

    @property
    def save_button(self) -> Locator:
        return self._save_button

    @property
    def search_perms_input(self) -> Locator:
        return self._search_perms

    @property
    def expand_all_button(self) -> Locator:
        return self._expand_all

    @property
    def collapse_all_button(self) -> Locator:
        return self._collapse_all


class RoleCreateDialog(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.roles.create_dialog_title")
        )
        self._title_input: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.roles.field_title")
        )
        self._description_input: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.roles.field_description")
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.roles.create_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.roles.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def fill(self, title: str, description: str) -> Self:
        self._title_input.fill(title)
        self._description_input.fill(description)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
