"""Smoke: сотрудник логинится в Client UI через OTP.

BRD §3.4: Client UI вход через телефон + OTP.
После OTP две развилки:
- ≥2 орг → /tenant-select (выбор организации)
- одна орг → сразу /documents (или /dashboard)

Тест проверяет успешный логин (либо tenant-select, либо landing-страница).
"""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import TEST_OTP
from pages.client.login_page import ClientLoginPage
from pages.client.otp_page import OtpPage


@pytest.mark.smoke
@allure.title("Client UI: вход через OTP → tenant-select или landing")
def test_client_login_with_valid_otp_redirects_to_app(
    page: Page, settings: Settings
) -> None:
    with allure.step("Открываем Client UI и вводим телефон"):
        ClientLoginPage(page).goto(settings.client_url).enter_phone(
            settings.client_smoke_phone
        ).submit()

    with allure.step("Вводим TEST_OTP"):
        OtpPage(page).enter_code(TEST_OTP).submit()

    with allure.step("Редирект на /tenant-select (≥2 орг) или /documents (одна орг)"):
        # URL не /login — успешный логин
        expect(page).not_to_have_url(
            re.compile(r"/login"), timeout=settings.nav_timeout
        )
        # И один из двух валидных landing'ов
        expect(page).to_have_url(
            re.compile(r"/(tenant-select|documents|dashboard)"),
            timeout=settings.nav_timeout,
        )
