"""Mock 1C — базовые тесты (подключение + один push). Полная интеграция
с 1С будет реальной, расширенное покрытие после её приземления.
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Browser, expect

from config.settings import Settings
from pages.mock1c.setup_page import (
    Mock1CEmployeesPage,
    Mock1CPositionsPage,
    Mock1CSetupPage,
    Mock1CTemplatesPage,
)


@pytest.mark.e2e
@allure.title("Mock1C: страница настроек открывается, поле ключа видимо")
def test_mock1c_setup_page_opens(
    browser: Browser, settings: Settings
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    setup = Mock1CSetupPage(page).goto(settings.mock1c_url)
    setup.ensure_russian_locale()
    expect(setup.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(setup.key_input).to_be_visible()
    expect(setup.save_button).to_be_visible()
    ctx.close()


@pytest.mark.e2e
@allure.title("Mock1C: подключение валидным ключом → статус 'Подключено'")
def test_mock1c_connect_with_valid_key(
    browser: Browser, settings: Settings, mock1c_company: dict[str, str]
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    setup = Mock1CSetupPage(page).goto(settings.mock1c_url)
    expect(setup.heading).to_be_visible(timeout=settings.nav_timeout)
    setup.fill_key(mock1c_company["integration_key"]).save()
    page.wait_for_timeout(3_000)
    expect(setup.status_connected()).to_be_visible(timeout=settings.nav_timeout)
    ctx.close()


@pytest.mark.e2e
@allure.title("Mock1C: после подключения /positions показывает таблицу с предзагруженными должностями")
def test_mock1c_positions_page_has_table(
    browser: Browser, settings: Settings, mock1c_company: dict[str, str]
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    setup = Mock1CSetupPage(page).goto(settings.mock1c_url)
    setup.ensure_russian_locale()
    setup.fill_key(mock1c_company["integration_key"]).save()
    page.wait_for_timeout(3_000)

    positions = Mock1CPositionsPage(page).goto(settings.mock1c_url)
    expect(positions.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(positions.send_all_button).to_be_visible()
    # Хотя бы одна row с данными (jt-001 Директор и т.д.)
    expect(positions.table.get_by_role("row").nth(1)).to_be_visible(
        timeout=settings.nav_timeout
    )
    ctx.close()


@pytest.mark.e2e
@allure.title("Mock1C: 'Отправить все' должности → push в Client UI")
def test_mock1c_send_all_positions_pushes_to_client(
    browser: Browser,
    settings: Settings,
    mock1c_company: dict[str, str],
) -> None:
    """После Send all в Mock 1C должности должны появиться на /positions Client UI."""
    from data.constants import TEST_OTP
    from pages.client.login_page import ClientLoginPage
    from pages.client.otp_page import OtpPage
    from pages.client.positions_page import PositionsPage

    # 1. Подключаемся в Mock 1C
    ctx_m1c = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    m1c_page = ctx_m1c.new_page()
    setup = Mock1CSetupPage(m1c_page).goto(settings.mock1c_url)
    setup.fill_key(mock1c_company["integration_key"]).save()
    m1c_page.wait_for_timeout(3_000)
    expect(setup.status_connected()).to_be_visible(timeout=settings.nav_timeout)

    # 2. Идём на /positions и жмём "Отправить все"
    positions_m1c = Mock1CPositionsPage(m1c_page).goto(settings.mock1c_url)
    expect(positions_m1c.heading).to_be_visible(timeout=settings.nav_timeout)
    positions_m1c.send_all_button.click()
    m1c_page.wait_for_timeout(4_000)
    ctx_m1c.close()

    # 3. Логинимся в Client UI как Администратор этой компании
    ctx_cli = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    cli_page = ctx_cli.new_page()
    ClientLoginPage(cli_page).goto(settings.client_url).enter_phone(
        mock1c_company["phone_full"]
    ).submit()
    OtpPage(cli_page).enter_code(TEST_OTP).submit()
    cli_page.wait_for_timeout(3_000)
    # Один в орг → /dashboard. Идём на /positions.
    cli_page.goto(f"{settings.client_url}/positions", wait_until="networkidle")
    cli_page.wait_for_timeout(2_000)

    # 4. Проверяем что в /positions свежей орг появилось хотя бы 1 должность
    import re as _re

    pos = PositionsPage(cli_page)
    expect(pos.heading).to_be_visible(timeout=settings.nav_timeout)
    body = cli_page.locator("body").inner_text()
    m = _re.search(r"Всего\s+(\d+)\s+должност", body)
    assert m and int(m.group(1)) > 0, f"После push должно быть >0 должностей, фрагмент: {body[:300]}"
    ctx_cli.close()


@pytest.mark.e2e
@allure.title("Mock1C: /employees страница доступна с send-all кнопкой")
def test_mock1c_employees_page_has_table(
    browser: Browser, settings: Settings, mock1c_company: dict[str, str]
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    setup = Mock1CSetupPage(page).goto(settings.mock1c_url)
    setup.ensure_russian_locale()
    setup.fill_key(mock1c_company["integration_key"]).save()
    page.wait_for_timeout(3_000)

    employees = Mock1CEmployeesPage(page).goto(settings.mock1c_url)
    expect(employees.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(employees.send_all_button).to_be_visible()
    ctx.close()


@pytest.mark.e2e
@allure.title("Mock1C: /templates страница доступна с send-all кнопкой")
def test_mock1c_templates_page_has_table(
    browser: Browser, settings: Settings, mock1c_company: dict[str, str]
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    setup = Mock1CSetupPage(page).goto(settings.mock1c_url)
    setup.ensure_russian_locale()
    setup.fill_key(mock1c_company["integration_key"]).save()
    page.wait_for_timeout(3_000)

    templates = Mock1CTemplatesPage(page).goto(settings.mock1c_url)
    expect(templates.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(templates.send_all_button).to_be_visible()
    ctx.close()


@pytest.mark.e2e
@allure.title("Mock1C: главная навигация содержит 4 раздела")
def test_mock1c_navigation_has_all_sections(
    browser: Browser, settings: Settings
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    setup = Mock1CSetupPage(page).goto(settings.mock1c_url)
    setup.ensure_russian_locale()
    page.wait_for_timeout(1_000)
    for section in ["Подключение", "Должности", "Сотрудники", "Шаблоны"]:
        expect(page.get_by_role("link", name=section).first).to_be_visible(
            timeout=settings.expect_timeout
        )
    ctx.close()
    _ = re  # keep import used (if applicable)
