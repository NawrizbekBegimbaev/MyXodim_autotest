"""Диалоги Должностей: Create / Edit / DeleteConfirm."""

from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class _PositionDialogBase(BasePage):
    """База: textbox Название + Cancel + Submit (имя зависит от Create/Edit)."""

    DIALOG_TITLE_KEY: str = ""
    SUBMIT_KEY: str = ""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role("dialog", name=t(self.DIALOG_TITLE_KEY))
        self._title_input: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.positions.field_title")
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t(self.SUBMIT_KEY), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.positions.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def fill_title(self, title: str) -> Self:
        self._title_input.fill(title)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self


class PositionCreateDialog(_PositionDialogBase):
    DIALOG_TITLE_KEY = "client.positions.create_dialog_title"
    SUBMIT_KEY = "client.positions.create_submit"


class PositionEditDialog(_PositionDialogBase):
    DIALOG_TITLE_KEY = "client.positions.edit_dialog_title"
    SUBMIT_KEY = "client.positions.edit_submit"


class PositionDeleteConfirmDialog(BasePage):
    """Подтверждение удаления (общий паттерн в Client UI)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.positions.delete_dialog_title")
        )
        self._confirm: Locator = self._dialog.get_by_role(
            "button", name=t("client.positions.delete_confirm_button"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.positions.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def confirm(self) -> Self:
        self._confirm.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
