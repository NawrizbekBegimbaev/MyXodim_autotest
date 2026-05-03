"""Read-only тесты структуры /tenants (Admin UI).

После редизайна 2026-05-03:
- Pagination control (BUG-007 fixed)
- Inline-кнопки "Отключить"/"Включить" (вместо switch'ей)
- Колонки таблицы: Компания / ИНН / Пользователи / Статус / Создана
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import BrowserContext, expect

from config.settings import Settings
from pages.admin.organizations_page import OrganizationsPage

EXPECTED_COLUMNS: tuple[str, ...] = (
    "Компания",
    "ИНН",
    "Пользователи",
    "Статус",
    "Создана",
)


@pytest.mark.positive
@allure.title("/tenants: heading 'Компании' и таблица рендерятся")
def test_tenants_heading_and_table(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    orgs = OrganizationsPage(page)
    expect(orgs.heading).to_be_visible(timeout=settings.expect_timeout)
    expect(orgs.table).to_be_visible()


@pytest.mark.positive
@allure.title("/tenants: 5 ожидаемых колонок таблицы присутствуют")
@pytest.mark.parametrize("col_name", EXPECTED_COLUMNS)
def test_tenants_table_columns_present(
    super_admin_context: BrowserContext, settings: Settings, col_name: str
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    orgs = OrganizationsPage(page)
    expect(orgs.table.get_by_role("columnheader", name=col_name, exact=True)).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.positive
@allure.title("/tenants: BUG-007 fixed — pagination control присутствует")
def test_tenants_pagination_controls_visible(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    pagination_nav = page.get_by_role("navigation", name="pagination navigation")
    expect(pagination_nav).to_be_visible(timeout=settings.expect_timeout)
    # Хотя бы одна кнопка перехода — page 1 — должна быть кликабельной
    expect(pagination_nav.get_by_role("button", name="page 1")).to_be_visible()
    # Селектор размера страницы
    expect(page.get_by_text("На странице:")).to_be_visible()


@pytest.mark.positive
@allure.title("/tenants: URL содержит query-params page/size/search")
def test_tenants_url_has_query_params(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    expect(page).to_have_url(
        re.compile(r"/tenants\?(?=.*page=)(?=.*size=)(?=.*search=)"),
        timeout=settings.nav_timeout,
    )


@pytest.mark.positive
@allure.title("/tenants: активная компания имеет toggle 'Отключить'")
def test_tenants_active_company_has_disable_toggle(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    """Read-only: проверяем что локатор находит MUI Switch с aria-label
    'Отключить' хотя бы на одной активной компании. Не кликаем!"""
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    orgs = OrganizationsPage(page)
    expect(orgs.heading).to_be_visible(timeout=settings.expect_timeout)
    active_rows = orgs.table.get_by_role("row").filter(has_text="Активна")
    first_active = active_rows.first
    expect(first_active).to_be_visible()
    expect(
        first_active.get_by_label("Отключить", exact=True)
    ).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("/tenants: отключённая компания имеет toggle 'Включить'")
def test_tenants_disabled_company_has_enable_toggle(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    """Read-only зеркальный тест: 'Отключена' row → toggle с aria-label='Включить'.

    Skip если на стенде нет ни одной отключённой компании.
    """
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    orgs = OrganizationsPage(page)
    expect(orgs.heading).to_be_visible(timeout=settings.expect_timeout)
    disabled_rows = orgs.table.get_by_role("row").filter(has_text="Отключена")
    if disabled_rows.count() == 0:
        pytest.skip("На стенде нет отключённых компаний — нечего проверять")
    expect(
        disabled_rows.first.get_by_label("Включить", exact=True)
    ).to_be_visible(timeout=settings.expect_timeout)
