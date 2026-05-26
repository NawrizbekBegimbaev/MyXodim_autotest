from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class MemberCreateDialog(BasePage):
    """Модалка создания сотрудника (открывается на /members кнопкой "Добавить сотрудника")."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role("dialog", name=t("client.members.dialog_title"))
        self._first_name: Locator = self._dialog.get_by_label(
            t("client.members.field_first_name"), exact=False
        )
        self._last_name: Locator = self._dialog.get_by_label(
            t("client.members.field_last_name"), exact=False
        )
        self._middle_name: Locator = self._dialog.get_by_label(
            t("client.members.field_middle_name"), exact=True
        )
        self._phone: Locator = self._dialog.get_by_label(
            t("client.members.field_phone"), exact=False
        )
        self._pinfl: Locator = self._dialog.get_by_label(
            t("client.members.field_pinfl"), exact=False
        )
        self._role: Locator = self._dialog.get_by_role(
            "combobox", name=t("client.members.field_role"), exact=False
        )
        self._position: Locator = self._dialog.get_by_role(
            "combobox", name=t("client.members.field_position"), exact=True
        )
        self._department: Locator = self._dialog.get_by_role(
            "combobox", name=t("client.members.field_department_brd3"), exact=True
        ).or_(
            self._dialog.get_by_role(
                "combobox", name=t("client.members.field_department"), exact=True
            )
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.members.dialog_submit")
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.members.dialog_cancel")
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    @property
    def pinfl_input(self) -> Locator:
        return self._pinfl

    @property
    def position_combobox(self) -> Locator:
        return self._position

    @property
    def department_combobox(self) -> Locator:
        return self._department

    def fill_required(
        self, first_name: str, last_name: str, phone: str, role: str
    ) -> Self:
        self._first_name.fill(first_name)
        self._last_name.fill(last_name)
        self._phone.fill(phone)
        self.select_role(role)
        return self

    def fill_middle_name(self, value: str) -> Self:
        self._middle_name.fill(value)
        return self

    def fill_pinfl(self, value: str) -> Self:
        self._pinfl.fill(value)
        return self

    def select_role(self, label: str) -> Self:
        # MUI Select: кликаем combobox → выбираем option из открывшегося listbox
        self._role.click()
        self.page.get_by_role("listbox").get_by_role(
            "option", name=label, exact=True
        ).click()
        return self

    def select_position(self, label: str) -> Self:
        self._position.click()
        self.page.get_by_role("listbox").get_by_role(
            "option", name=label, exact=True
        ).click()
        return self

    def select_department(self, label: str) -> Self:
        self._department.click()
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
