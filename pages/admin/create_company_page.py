"""POM страницы создания компании /tenants/new и success-view после submit.

После клика "Создать" страница меняет содержимое на success-state
(heading "Компания создана") с ключом интеграции, tenantId, adminUserId
прямо на экране. Извлечение этих значений — в `CompanyCreatedView`.
"""

import re
from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class CreateCompanyPage(BasePage):
    URL_PATH = "/tenants/new"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._page_heading: Locator = page.get_by_role(
            "heading", name=t("admin.company.page_title"), level=5
        )
        self._name: Locator = page.get_by_role(
            "textbox", name=t("admin.company.field_name")
        )
        self._slug: Locator = page.get_by_role(
            "textbox", name=t("admin.company.field_slug")
        )
        self._inn: Locator = page.get_by_role(
            "textbox", name=t("admin.company.field_inn")
        )
        self._first_name: Locator = page.get_by_role(
            "textbox", name=t("admin.company.field_first_name")
        )
        self._last_name: Locator = page.get_by_role(
            "textbox", name=t("admin.company.field_last_name")
        )
        self._phone: Locator = page.get_by_role(
            "textbox", name=t("admin.company.field_phone")
        )
        self._pinfl: Locator = page.get_by_role(
            "textbox", name=t("admin.company.field_pinfl")
        )
        self._submit: Locator = page.get_by_role(
            "button", name=t("admin.company.submit")
        )
        self._cancel: Locator = page.get_by_role(
            "button", name=t("admin.company.cancel")
        )

    @property
    def page_heading(self) -> Locator:
        return self._page_heading

    @property
    def submit_button(self) -> Locator:
        return self._submit

    def fill_company(self, name: str, slug: str, inn: str = "") -> Self:
        self._name.fill(name)
        self._slug.fill(slug)
        if inn:
            self._inn.fill(inn)
        return self

    def fill_admin(
        self,
        first_name: str,
        last_name: str,
        phone_local: str,
        pinfl: str = "",
    ) -> Self:
        """phone_local — 9 цифр без префикса +998 (префикс показан отдельно)."""
        self._first_name.fill(first_name)
        self._last_name.fill(last_name)
        self._phone.fill(phone_local)
        if pinfl:
            self._pinfl.fill(pinfl)
        return self

    def submit(self) -> Self:
        """Click "Создать". Не ждёт ответа — клиент-валидация может заблокировать submit.

        Тесты сами выбирают как ждать результат: success-heading (positive) или
        page-heading стабильно остаётся (negative).
        """
        self._submit.click()
        return self


class CompanyCreatedView(BasePage):
    """Success-state после успешного создания (на той же странице /tenants/new)."""

    INTEGRATION_KEY_PATTERN = re.compile(r"^bh_live_[a-f0-9]{32}$")
    UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("admin.company.success_heading"), level=5
        )
        self._back_button: Locator = page.get_by_role(
            "button", name=t("admin.company.success_back_to_list")
        )
        # bh_live_<32 hex>
        self._integration_key: Locator = page.get_by_text(self.INTEGRATION_KEY_PATTERN)
        # UUID нашей tenant'а — первый из двух uuid на странице (в порядке: tenantId, adminUserId)
        self._uuids: Locator = page.get_by_text(self.UUID_PATTERN)

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def back_button(self) -> Locator:
        return self._back_button

    @property
    def integration_key_locator(self) -> Locator:
        return self._integration_key

    def integration_key(self) -> str:
        return self._integration_key.inner_text().strip()

    def tenant_id(self) -> str:
        return self._uuids.nth(0).inner_text().strip()

    def admin_user_id(self) -> str:
        return self._uuids.nth(1).inner_text().strip()

    def click_back(self) -> Self:
        self._back_button.click()
        return self
