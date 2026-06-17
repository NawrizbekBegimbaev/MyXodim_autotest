"""Sanity cases 1-4 — Admin UI."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.sanity_data import SanityAdminData
from pages.admin.admins_page import AdminsPage
from pages.admin.create_company_page import CreatedTenant
from pages.admin.tenants_page import TenantsPage

pytestmark = [pytest.mark.sanity, pytest.mark.admin]


@allure.title("1. Логин — вход по телефону+пароль → /dashboard")
@allure.description(
    "**Цель:** платформенный администратор входит в Admin UI и попадает на дашборд.\n\n"
    "**Окружение:** stage, Admin UI.\n"
    "**Предусловие:** существует платформенный админ (телефон + пароль из конфигурации).\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Открыть Admin UI `/login`.\n"
    "2. Ввести телефон и пароль платформенного админа, нажать «Войти».\n"
    "3. Дождаться редиректа.\n\n"
    "**Ожидаемый результат:** редирект на `/dashboard`, виден заголовок «Дашборд»."
)
def test_admin_login(admin_page: Page, cfg) -> None:
    with allure.step("Перейти на /dashboard под залогиненным платформенным админом"):
        admin_page.goto(f"{cfg.admin_url}/dashboard", wait_until="domcontentloaded")
    with allure.step("Проверить URL /dashboard и заголовок «Дашборд»"):
        expect(admin_page).to_have_url(re.compile(r"/dashboard"))
        expect(admin_page.get_by_role("heading", name="Дашборд")).to_be_visible()


@allure.title("2. Дашборд — метрики и блоки грузятся без ошибок")
@allure.description(
    "**Цель:** на дашборде Admin UI отображаются ключевые метрики платформы.\n\n"
    "**Окружение:** stage, Admin UI. **Предусловие:** выполнен вход как платформенный админ.\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Открыть `/dashboard`.\n"
    "2. Проверить наличие блоков метрик.\n\n"
    "**Ожидаемый результат:** видны «Всего компаний», «Активных компаний», «Всего пользователей»."
)
def test_admin_dashboard_metrics(admin_page: Page, cfg) -> None:
    with allure.step("Открыть /dashboard"):
        admin_page.goto(f"{cfg.admin_url}/dashboard", wait_until="domcontentloaded")
    with allure.step("Проверить метрики дашборда"):
        expect(admin_page.get_by_text("Всего компаний")).to_be_visible()
        expect(admin_page.get_by_text("Активных компаний")).to_be_visible()
        expect(admin_page.get_by_text("Всего пользователей")).to_be_visible()


@allure.title("3. Новый администратор — создаётся и виден в списке")
@allure.description(
    "**Цель:** платформенный админ создаёт нового администратора, и он появляется в списке.\n\n"
    "**Окружение:** stage, Admin UI. **Предусловие:** выполнен вход как платформенный админ.\n"
    "**Данные:** уникальное имя `Санити Админ<epoch>` и телефон, генерируются на прогон.\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Открыть `/admins`.\n"
    "2. Нажать «Новый администратор».\n"
    "3. Заполнить имя и телефон, нажать «Сохранить».\n"
    "4. Закрыть модал с паролем, вернуться к списку.\n\n"
    "**Ожидаемый результат:** новый администратор присутствует в списке."
)
def test_admin_create_new_admin(admin_page: Page, cfg) -> None:
    data = SanityAdminData()
    admins = AdminsPage(admin_page, cfg.admin_url)
    with allure.step("Открыть раздел «Администраторы» (/admins)"):
        admins.open()
        expect(admins.heading).to_be_visible()
    with allure.step(f"Создать администратора «{data.first_name} {data.last_name}»"):
        admins.create(f"{data.first_name} {data.last_name}", data.phone)
    with allure.step("Вернуться к списку и убедиться, что админ виден"):
        admins.open()
        # Match by the unique name token (phone is reformatted with spaces).
        expect(admins.row(data.last_name)).to_be_visible()


@allure.title("4. Создание компании — компания создаётся со статусом Активна")
@allure.description(
    "**Цель:** платформенный админ создаёт компанию с администратором; она активна.\n\n"
    "**Окружение:** stage, Admin UI. **Предусловие:** выполнен вход как платформенный админ.\n"
    "**Данные:** `[SANITY] <epoch>` с уникальными slug/ИНН/телефон/ПИНФЛ (создаётся фикстурой).\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Открыть `/tenants/new`.\n"
    "2. Заполнить данные компании и администратора, нажать «Создать».\n"
    "3. В модале успеха получить ключ интеграции и ID.\n"
    "4. Найти компанию в списке `/tenants`.\n\n"
    "**Ожидаемый результат:** выдан ключ `bh_live_…`; компания в списке со статусом «Активна»."
)
def test_company_created_is_active(admin_page: Page, cfg, sanity_tenant: CreatedTenant) -> None:
    with allure.step("Компания создана фикстурой — проверить выданный ключ интеграции"):
        # The company was created by the `sanity_tenant` session fixture.
        assert sanity_tenant.integration_key.startswith("bh_live_")
    with allure.step(f"Найти компанию «{sanity_tenant.name}» в списке и проверить статус «Активна»"):
        tenants = TenantsPage(admin_page, cfg.admin_url).open()
        row = tenants.find_row(sanity_tenant.name)
        expect(row).to_be_visible()
        expect(row.get_by_text("Активна")).to_be_visible()
