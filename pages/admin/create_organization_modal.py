from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class CreateOrganizationModal(BasePage):
    """Модалка создания организации."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role("dialog")
        self._name: Locator = self._dialog.get_by_label(t("org.name_label"))
        self._inn: Locator = self._dialog.get_by_label(t("org.inn_label"))
        self._admin_phone: Locator = self._dialog.get_by_label(t("org.admin_phone_label"))
        self._submit: Locator = self._dialog.get_by_role("button", name=t("org.submit"))

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def fill(self, name: str, inn: str, admin_phone: str) -> Self:
        self._name.fill(name)
        self._inn.fill(inn)
        self._admin_phone.fill(admin_phone)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self
