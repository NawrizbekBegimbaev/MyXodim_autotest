from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class PersonCreateDialog(BasePage):
    """Dialog opened from /persons with personal-data fields."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.persons.dialog_title")
        )
        self._full_name: Locator = self._dialog.get_by_label(
            t("client.persons.field_full_name"), exact=True
        )
        self._pinfl: Locator = self._dialog.get_by_label(
            t("client.persons.field_pinfl"), exact=True
        )
        self._birth_date: Locator = self._dialog.get_by_label(
            t("client.persons.field_birth_date"), exact=True
        )
        self._email: Locator = self._dialog.get_by_label(
            t("client.persons.field_email"), exact=True
        )
        self._phone: Locator = self._dialog.get_by_label(
            t("client.persons.field_phone"), exact=True
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.persons.dialog_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.persons.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def fill(
        self,
        full_name: str,
        pinfl: str,
        birth_date: str = "",
        email: str = "",
        phone: str = "",
    ) -> Self:
        self._full_name.fill(full_name)
        self._pinfl.fill(pinfl)
        if birth_date:
            self._birth_date.fill(birth_date)
        if email:
            self._email.fill(email)
        if phone:
            self._phone.fill(phone)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
