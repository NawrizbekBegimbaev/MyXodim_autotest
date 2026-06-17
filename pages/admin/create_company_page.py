"""Admin UI — create company + admin (/tenants/new). Verified on staging."""

from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import Locator, Page

from config.sanity_data import SanityTenantData
from pages.base_page import BasePage


@dataclass(frozen=True)
class CreatedTenant:
    name: str
    admin_phone: str
    integration_key: str
    tenant_id: str
    admin_id: str


class CreateCompanyPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.name_input: Locator = page.get_by_role("textbox", name="Название компании")
        self.slug_input: Locator = page.get_by_role("textbox", name="Slug")
        self.inn_input: Locator = page.get_by_role("textbox", name="ИНН")
        self.first_name_input: Locator = page.get_by_role("textbox", name="Имя")
        self.last_name_input: Locator = page.get_by_role("textbox", name="Фамилия")
        self.phone_input: Locator = page.get_by_role("textbox", name="Телефон")
        self.pinfl_input: Locator = page.get_by_role("textbox", name="ПИНФЛ")
        self.submit_button: Locator = page.get_by_role("button", name="Создать")
        # Success modal marker.
        self.success_marker: Locator = page.get_by_text("Ключ интеграции")

    def open(self) -> CreateCompanyPage:
        self.goto(f"{self.base_url}/tenants/new")
        return self

    def fill(self, data: SanityTenantData) -> CreateCompanyPage:
        self.name_input.fill(data.name)
        self.slug_input.fill(data.slug)
        self.inn_input.fill(data.inn)
        self.first_name_input.fill(data.admin_first_name)
        self.last_name_input.fill(data.admin_last_name)
        self.phone_input.fill(data.admin_phone)
        self.pinfl_input.fill(data.admin_pinfl)
        return self

    def submit(self) -> None:
        self.submit_button.click()

    def read_result(self, data: SanityTenantData) -> CreatedTenant:
        """Read the success modal (integration key + ids). Call after submit."""
        body = self.page.locator("body").inner_text()
        key = self._find(r"bh_live_[0-9a-f]+", body)
        ids = re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", body)
        return CreatedTenant(
            name=data.name,
            admin_phone=data.admin_phone,
            integration_key=key,
            tenant_id=ids[0] if ids else "",
            admin_id=ids[1] if len(ids) > 1 else "",
        )

    @staticmethod
    def _find(pattern: str, text: str) -> str:
        m = re.search(pattern, text)
        return m.group(0) if m else ""
