"""Smoke: сотрудник логинится в Client UI через OTP.

BRD §3.4: Client UI вход через телефон + OTP.
Пользователь из CLIENT_SMOKE_PHONE состоит в нескольких организациях,
поэтому после OTP редирект на /tenant-select (см. CLAUDE.md §14 п.3).
"""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import TEST_OTP
from pages.client.login_page import ClientLoginPage
from pages.client.otp_page import OtpPage
from pages.client.select_organization_page import SelectOrganizationPage


@pytest.mark.smoke
@allure.title("Client UI: вход через OTP → экран выбора организации")
def test_client_login_with_valid_otp_opens_tenant_select(
    page: Page, settings: Settings
) -> None:
    with allure.step("Открываем Client UI и вводим телефон"):
        ClientLoginPage(page).goto(settings.client_url).enter_phone(
            settings.client_smoke_phone
        ).submit()

    with allure.step("Вводим TEST_OTP"):
        OtpPage(page).enter_code(TEST_OTP).submit()

    with allure.step("Редирект на /tenant-select (пользователь в нескольких орг)"):
        expect(page).to_have_url(re.compile(r"/tenant-select"), timeout=settings.nav_timeout)
        expect(SelectOrganizationPage(page).heading).to_be_visible(
            timeout=settings.expect_timeout
        )
