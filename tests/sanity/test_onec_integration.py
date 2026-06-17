"""Sanity case 7 — 1C integration: data pushed from Mock 1C appears in Client UI.

Runs AFTER test_directories_clean (case 6 asserts the company is empty first).
Uses the fresh company's integration key, pushes the Mock 1C dataset, then
verifies the imported reference data in the Client UI as the company admin.
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.admin.create_company_page import CreatedTenant
from pages.client.app_page import ClientAppPage
from pages.mock1c.mock1c_page import PUSH_ROUTES, Mock1cPage

pytestmark = [pytest.mark.sanity, pytest.mark.mock1c]


@allure.title("7. Интеграция с 1С — данные импортируются")
@allure.description(
    "**Цель:** данные, отправленные из Mock 1C по ключу интеграции компании, "
    "появляются в Client UI.\n\n"
    "**Окружение:** stage, Mock 1C + Client UI.\n"
    "**Предусловие:** создана [SANITY]-компания (есть ключ интеграции `bh_live_…`).\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Открыть Mock 1C, ввести ключ интеграции компании, нажать «Сохранить» — статус «Подключено».\n"
    "2. Поочерёдно на страницах Организации/Подразделения/Должности/Физлица/Сотрудники "
    "нажать «Отправить все».\n"
    "3. Войти в Client UI как Администратор компании.\n"
    "4. Открыть `/positions`, `/persons`, `/members` и найти импортированные записи.\n\n"
    "**Ожидаемый результат:** push успешен («Отправлено»); в клиенте видны импортированные "
    "должность «Инициатор», физлицо «Иванова Елена», сотрудник «Иванова»."
)
def test_onec_import(page: Page, admin_client_page: Page, cfg, sanity_tenant: CreatedTenant) -> None:
    mock = Mock1cPage(page, cfg.mock1c_url)

    with allure.step("Mock 1C: подключение по ключу интеграции компании"):
        mock.connect(sanity_tenant.integration_key)

    for name, route in PUSH_ROUTES.items():
        with allure.step(f"Mock 1C: отправить все «{name}»"):
            mock.push_all(route)
            expect(page.get_by_text("Отправлено").first).to_be_visible(timeout=20_000)

    app = ClientAppPage(admin_client_page, cfg.client_url)
    with allure.step("Client UI: импортированная должность видна (/positions)"):
        app.open("/positions")
        expect(admin_client_page.get_by_text("Инициатор").first).to_be_visible(timeout=20_000)
    with allure.step("Client UI: импортированное физлицо видно (/persons)"):
        app.open("/persons")
        expect(admin_client_page.get_by_text("Иванова Елена").first).to_be_visible(timeout=20_000)
    with allure.step("Client UI: импортированный сотрудник виден (/members)"):
        app.open("/members")
        expect(admin_client_page.get_by_text("Иванова").first).to_be_visible(timeout=20_000)
