"""UC-4.2: просмотр / поиск компаний в Admin UI (/tenants).

BRD §4.2: список компаний, поиск, открытие деталей.
Замечания:
- pagination сломан (BUG-007), отдельные тесты для пагинации не пишем
- search — client-side фильтрация по уже загруженным записям (10)
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import BrowserContext, expect

from config.settings import Settings
from pages.admin.organizations_page import OrganizationsPage


def _open_list(ctx: BrowserContext, settings: Settings) -> OrganizationsPage:
    page = ctx.new_page()
    # Сначала dashboard — фронт инициализирует state там, /tenants без этого "чистый" не грузится
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    page.wait_for_timeout(1_500)
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    page.wait_for_timeout(2_500)
    orgs = OrganizationsPage(page)
    expect(orgs.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(orgs.table.get_by_role("row").nth(1)).to_be_visible(timeout=settings.nav_timeout)
    return orgs


@pytest.mark.positive
@allure.title("UC-4.2: /tenants показывает существующие компании")
def test_tenants_list_shows_existing_companies(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    # минимум 2 row (header + ≥1 data)
    rows_count = orgs.table.get_by_role("row").count()
    assert rows_count >= 2, f"Ожидали ≥2 row (header+data), получили {rows_count}"


@pytest.mark.positive
@allure.title("UC-4.2: header колонок таблицы — Компания, ИНН, Пользователи, Статус, Создана")
def test_tenants_list_has_expected_column_headers(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    expected = ["Компания", "ИНН", "Пользователи", "Статус", "Создана"]
    for col in expected:
        expect(orgs.table.get_by_role("columnheader", name=col)).to_be_visible()


@pytest.mark.positive
@allure.title("UC-4.2: поиск по имени существующей компании фильтрует список")
def test_tenants_list_search_by_name_filters(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    anchor_company: dict[str, str],
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    # Используем slug как уникальный паттерн (имя содержит общий префикс [E2E anchor])
    orgs.search(anchor_company["slug"])
    expect(orgs.row_by_name(anchor_company["name"])).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("UC-4.2: search с не-существующей строкой → empty-state")
def test_tenants_list_search_with_no_match_shows_empty_state(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    orgs.search("__no_such_company_xyz_12345__")
    expect(orgs.empty_state()).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("UC-4.2: очистка search возвращает полный список")
def test_tenants_list_clear_search_restores_list(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    initial_rows = orgs.table.get_by_role("row").count()

    orgs.search("__no_match__")
    expect(orgs.empty_state()).to_be_visible(timeout=settings.expect_timeout)

    orgs.search("")  # очистить
    # вернулось столько же row сколько было изначально
    expect(orgs.table.get_by_role("row")).to_have_count(initial_rows)
