"""Smoke: Super Admin логинится в Admin UI и попадает на дашборд.

BRD §4.4: Super Admin имеет доступ ко всем разделам Admin UI.
"""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.admin.dashboard_page import AdminDashboardPage
from pages.admin.login_page import AdminLoginPage


@pytest.mark.smoke
@allure.title("Super Admin: вход в Admin UI → редирект на /dashboard")
def test_super_admin_login_with_valid_credentials_opens_dashboard(
    page: Page, settings: Settings
) -> None:
    with allure.step("Логинимся в Admin UI"):
        AdminLoginPage(page).goto(settings.admin_url).login(
            settings.super_admin_phone, settings.super_admin_password
        )

    dashboard = AdminDashboardPage(page)
    with allure.step("Редирект на /dashboard"):
        expect(page).to_have_url(re.compile(r"/dashboard"), timeout=settings.nav_timeout)
    with allure.step("Sidebar и кнопка добавления компании видны"):
        expect(dashboard.companies_link).to_be_visible(timeout=settings.expect_timeout)
        expect(dashboard.add_company_button).to_be_visible()
        expect(dashboard.logout_button).to_be_visible()
