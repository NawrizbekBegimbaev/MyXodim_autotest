"""Главный E2E: cross-app сценарий (CLAUDE.md §3).

Версия `_no_eimzo` (для CI):
1. Admin UI: Super Admin создаёт компанию → integration_key
2. Mock 1C: подключается по ключу → push должностей
3. Client UI: первый Администратор логинится → видит должности из 1С
4. Client UI: создаёт маршрут (default config 1 шаг)
5. Client UI: открывает создание документа → wizard работает

Проверяем КЛЮЧЕВЫЕ точки cross-app синхронизации, не EIMZO-подпись.
Полный маршрут с подписанием EIMZO — отдельный @eimzo_local_only тест.
"""

from __future__ import annotations

import re
import secrets

import allure
import pytest
from playwright.sync_api import Browser, expect

from config.settings import Settings
from data.constants import E2E_PREFIX, TEST_OTP
from pages.client.documents_page import DocumentCreateWizardPage, DocumentsPage
from pages.client.login_page import ClientLoginPage
from pages.client.otp_page import OtpPage
from pages.client.positions_page import PositionsPage
from pages.client.routes_page import RouteEditorPage, RoutesPage
from pages.mock1c.setup_page import Mock1CPositionsPage, Mock1CSetupPage


@pytest.mark.e2e
@pytest.mark.serial
@allure.title("§3 Главный E2E (no EIMZO): Admin → Mock 1C → Client UI документ-флоу")
def test_admin_to_client_full_flow_no_eimzo(
    browser: Browser,
    settings: Settings,
    mock1c_company: dict[str, str],
) -> None:
    """ОДИН интеграционный тест разбит на @allure.step (CLAUDE.md §3).

    `mock1c_company` уже создал компанию через Admin UI и достал integration_key —
    это шаги 1-3 главного E2E.
    """
    integration_key = mock1c_company["integration_key"]
    admin_phone_full = mock1c_company["phone_full"]
    company_name = mock1c_company["name"]

    with allure.step(f"1-3. Admin UI создал компанию '{company_name}' с ключом"):
        assert integration_key.startswith("bh_live_"), f"Невалидный ключ: {integration_key}"
        assert mock1c_company["tenant_id"], "Нет tenant_id"

    with allure.step("4. Mock 1C: подключение по ключу"):
        m1c_ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        m1c_page = m1c_ctx.new_page()
        setup = Mock1CSetupPage(m1c_page).goto(settings.mock1c_url)
        setup.ensure_russian_locale()
        setup.fill_key(integration_key).save()
        m1c_page.wait_for_timeout(3_000)
        expect(setup.status_connected()).to_be_visible(timeout=settings.nav_timeout)

    with allure.step("5. Mock 1C → Должности → 'Отправить все'"):
        positions_m1c = Mock1CPositionsPage(m1c_page).goto(settings.mock1c_url)
        expect(positions_m1c.heading).to_be_visible(timeout=settings.nav_timeout)
        positions_m1c.send_all_button.click()
        m1c_page.wait_for_timeout(4_000)
        m1c_ctx.close()

    with allure.step("6-7. Client UI: Администратор логинится через OTP"):
        cli_ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        from pages.client.select_organization_page import SelectOrganizationPage

        cli_page = cli_ctx.new_page()
        ClientLoginPage(cli_page).goto(settings.client_url).enter_phone(
            admin_phone_full
        ).submit()
        cli_page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
        cli_page.wait_for_timeout(3_000)
        otp_input = cli_page.get_by_role("textbox", name="Код подтверждения")
        expect(otp_input).to_be_visible(timeout=settings.nav_timeout)
        OtpPage(cli_page).enter_code(TEST_OTP).submit()
        cli_page.wait_for_url(
            re.compile(r"/(dashboard|tenant-select)"), timeout=settings.nav_timeout
        )
        cli_page.wait_for_timeout(2_500)
        # Если юзер попал на /tenant-select — выбираем свою новую компанию
        if "tenant-select" in cli_page.url:
            SelectOrganizationPage(cli_page).select(company_name)
            cli_page.wait_for_url("**/dashboard", timeout=settings.nav_timeout)
            cli_page.wait_for_timeout(2_000)
        from pathlib import Path

        Path("recon").mkdir(exist_ok=True)
        (Path("recon") / "e2e_after_login.yaml").write_text(
            cli_page.locator("body").aria_snapshot()
        )
        (Path("recon") / "e2e_after_login_url.txt").write_text(cli_page.url)

    with allure.step("8. Client UI /positions: должности из 1С появились (>0)"):
        cli_page.goto(f"{settings.client_url}/positions", wait_until="networkidle")
        cli_page.wait_for_timeout(3_000)
        pos = PositionsPage(cli_page)
        expect(pos.heading).to_be_visible(timeout=settings.nav_timeout)
        # Проверяем что после push в свежесозданной орг появились должности
        # (точные имена могут трансформироваться при синхронизации Mock 1C → BusinessHub)
        body = cli_page.locator("body").inner_text()
        match = re.search(r"Всего\s+(\d+)\s+должност", body)
        assert match is not None, f"Не нашли счётчик должностей. Фрагмент: {body[:300]}"
        count = int(match.group(1))
        assert count > 0, f"Ожидали >0 должностей после push из Mock 1C, получили {count}"

    with allure.step("9. Client UI: создаём маршрут"):
        route_name = f"{E2E_PREFIX} E2E-Route {secrets.token_hex(3)}"
        cli_page.goto(f"{settings.client_url}/routes", wait_until="networkidle")
        rt = RoutesPage(cli_page)
        expect(rt.heading).to_be_visible(timeout=settings.nav_timeout)
        rt.click_create()
        editor = RouteEditorPage(cli_page)
        expect(editor.save_button).to_be_visible(timeout=settings.nav_timeout)
        editor.fill_name(route_name).fill_description("E2E маршрут").save()
        cli_page.wait_for_timeout(3_000)

    with allure.step("10. Client UI: маршрут виден в списке"):
        cli_page.goto(f"{settings.client_url}/routes", wait_until="networkidle")
        cli_page.wait_for_timeout(2_000)
        rt2 = RoutesPage(cli_page)
        expect(rt2.heading).to_be_visible(timeout=settings.nav_timeout)
        rt2.search(route_name)
        cli_page.wait_for_timeout(1_500)
        expect(rt2.row_by_name(route_name)).to_be_visible(timeout=settings.nav_timeout)

    with allure.step("11. Client UI /documents: wizard открывается"):
        docs = DocumentsPage(cli_page).goto(settings.client_url)
        expect(docs.heading).to_be_visible(timeout=settings.nav_timeout)
        docs.click_create()
        wizard = DocumentCreateWizardPage(cli_page)
        expect(wizard.heading).to_be_visible(timeout=settings.nav_timeout)
        expect(wizard.tab_template).to_be_visible()

    cli_ctx.close()
