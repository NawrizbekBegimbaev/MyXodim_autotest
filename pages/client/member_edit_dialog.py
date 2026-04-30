from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class MemberEditDialog(BasePage):
    """Модалка редактирования сотрудника (открывается кнопкой 'Редактировать' на /members).

    Те же поля что и в MemberCreateDialog, но title 'Редактировать сотрудника'
    и кнопка submit 'Сохранить' (вместо 'Добавить').
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.members.edit_dialog_title")
        )
        self._first_name: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.members.field_first_name")
        )
        self._last_name: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.members.field_last_name")
        )
        self._middle_name: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.members.field_middle_name")
        )
        self._phone: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.members.field_phone")
        )
        self._pinfl: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.members.field_pinfl")
        )
        self._role: Locator = self._dialog.get_by_role(
            "combobox", name=t("client.members.field_role")
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.members.edit_dialog_submit")
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.members.dialog_cancel")
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    @property
    def first_name_input(self) -> Locator:
        return self._first_name

    @property
    def last_name_input(self) -> Locator:
        return self._last_name

    def update_first_name(self, value: str) -> Self:
        self._first_name.fill(value)
        return self

    def update_last_name(self, value: str) -> Self:
        self._last_name.fill(value)
        return self

    def select_role(self, label: str) -> Self:
        self._role.click()
        self.page.get_by_role("listbox").get_by_role(
            "option", name=label, exact=True
        ).click()
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
