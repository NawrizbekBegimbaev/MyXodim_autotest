"""Sanity case 28 — access rights match the role (RBAC).

Contrast two roles on management-only routes:
- ADMINISTRATOR (the company admin) — access granted (sees the page).
- EMPLOYEE (a known restricted user) — redirected to /forbidden «Доступ запрещён».
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.client.app_page import ClientAppPage

pytestmark = [pytest.mark.sanity, pytest.mark.client]

# Management-only routes an EMPLOYEE must not reach.
RESTRICTED = ["/members", "/document-types", "/positions"]


@allure.title("28. Вход на аккаунты с ролью — права соответствуют роли")
@allure.description(
    "**Цель:** доступ к разделам соответствует роли пользователя (RBAC).\n\n"
    "**Окружение:** stage, Client UI.\n"
    "**Предусловия:** известный пользователь с ролью Сотрудник (EMPLOYEE) и Администратор.\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Войти как Сотрудник (EMPLOYEE).\n"
    "2. Поочерёдно открыть `/members`, `/document-types`, `/positions`.\n"
    "3. Войти как Администратор и открыть `/members`.\n\n"
    "**Ожидаемый результат:** Сотруднику показывается `/forbidden` «Доступ запрещён» на "
    "управленческих разделах; Администратору раздел «Сотрудники» доступен."
)
def test_rbac_role_access(employee_client_page: Page, admin_client_page: Page, cfg) -> None:
    with allure.step("EMPLOYEE: управленческие разделы недоступны (/forbidden)"):
        app = ClientAppPage(employee_client_page, cfg.client_url)
        for route in RESTRICTED:
            app.open(route)
            expect(employee_client_page).to_have_url(re.compile(r"/forbidden"), timeout=15_000)
            expect(
                employee_client_page.get_by_role("heading", name="Доступ запрещён")
            ).to_be_visible()

    with allure.step("ADMINISTRATOR: тот же раздел доступен (контраст)"):
        admin = ClientAppPage(admin_client_page, cfg.client_url).open("/members")
        expect(admin.heading("Сотрудники")).to_be_visible()
        expect(admin_client_page).to_have_url(re.compile(r"/members"))
