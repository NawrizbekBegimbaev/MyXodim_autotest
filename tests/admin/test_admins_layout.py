"""Read-only тесты раздела /admins (Admin UI).

Раздел появился 2026-05-03. Тесты проверяют только структуру и read-only
взаимодействие (поиск). Создание/редактирование/удаление — отдельно
с маркером creates_data, когда будет можно мутировать данные.
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import BrowserContext, expect

from config.settings import Settings
from pages.admin.admins_page import AdminsPage


@pytest.mark.positive
@allure.title("/admins: heading 'Adminlar' и subtitle 'Platforma administratorlari'")
def test_admins_page_renders_heading(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    admins = AdminsPage(page)
    expect(admins.heading).to_be_visible(timeout=settings.expect_timeout)
    expect(admins.subtitle).to_be_visible()


@pytest.mark.positive
@allure.title("/admins: кнопка 'Yangi admin' и поле поиска присутствуют")
def test_admins_page_has_add_button_and_search(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    admins = AdminsPage(page)
    expect(admins.add_button).to_be_visible(timeout=settings.expect_timeout)
    expect(admins.search_input).to_be_visible()


@pytest.mark.positive
@allure.title("/admins: все 4 колонки таблицы присутствуют (UZ)")
@pytest.mark.parametrize("col_name", AdminsPage.COLUMNS)
def test_admins_table_columns_present(
    super_admin_context: BrowserContext, settings: Settings, col_name: str
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    admins = AdminsPage(page)
    expect(admins.column_header(col_name)).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.positive
@allure.title("/admins: URL содержит query-params page/size/search")
def test_admins_url_has_query_params(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    expect(page).to_have_url(
        re.compile(r"/admins\?(?=.*page=)(?=.*size=)(?=.*search=)"),
        timeout=settings.nav_timeout,
    )


@pytest.mark.positive
@allure.title("/admins: текущий Super Admin (+998991234567) виден в таблице")
def test_admins_table_contains_super_admin(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    admins = AdminsPage(page)
    # Используем телефон как ключ — стабильнее имени (которое
    # на UZ получается "Platform Admin(siz)").
    expect(
        admins.row_by_phone(settings.super_admin_phone)
    ).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("/admins: поиск по нулевому совпадению показывает пустой результат")
def test_admins_search_empty_match_shows_no_rows(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    admins = AdminsPage(page)
    admins.search("zzznotfoundzzz")
    # Проверяем что в tbody нет строк (или счётчик "0")
    rowgroups = admins.table.get_by_role("rowgroup").all()
    # rowgroups[0] — thead, rowgroups[1] — tbody
    if len(rowgroups) >= 2:
        expect(rowgroups[1].get_by_role("row")).to_have_count(0)


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("/admins: sidebar содержит ссылку 'Adminlar'")
def test_admins_sidebar_link_present(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    nav = page.get_by_role("navigation").first
    expect(nav.get_by_role("link", name="Adminlar", exact=True)).to_be_visible(
        timeout=settings.expect_timeout
    )
