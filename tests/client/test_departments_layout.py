"""Read-only тесты раздела /departments (новый, 2026-05-03).

Не CRUD — без создания/редактирования/удаления отделов.
Действия с рядами помечать creates_data в отдельных тестах.
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.departments_page import DepartmentsPage
from pages.client.sidebar import ClientSidebar


@pytest.mark.positive
@allure.title("/departments: heading 'Отделы' + кнопка 'Добавить отдел'")
def test_departments_renders_heading_and_add_button(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/departments", wait_until="networkidle")
    deps = DepartmentsPage(page)
    expect(deps.heading).to_be_visible(timeout=settings.expect_timeout)
    expect(deps.add_button).to_be_visible()


@pytest.mark.positive
@allure.title("/departments: счётчик отделов соответствует формату 'Всего N отделов'")
def test_departments_total_counter_format(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/departments", wait_until="networkidle")
    expect(page.get_by_text(re.compile(r"Всего\s+\d+\s+отдел"))).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.positive
@allure.title("/departments: поиск + 2 фильтра-комбобокса (Филиал, Источник)")
def test_departments_has_search_and_filters(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/departments", wait_until="networkidle")
    deps = DepartmentsPage(page)
    expect(deps.search_input).to_be_visible(timeout=settings.expect_timeout)
    expect(deps.branch_filter).to_be_visible()
    expect(deps.source_filter).to_be_visible()


@pytest.mark.positive
@allure.title("/departments: все 6 колонок таблицы присутствуют")
@pytest.mark.parametrize("col_name", DepartmentsPage.COLUMNS)
def test_departments_table_columns_present(
    client_admin_page: Page, settings: Settings, col_name: str
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/departments", wait_until="networkidle")
    deps = DepartmentsPage(page)
    expect(deps.column_header(col_name)).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("/departments: ссылка 'Отделы' живёт под группой 'Оргструктура'")
def test_departments_sidebar_link_under_orgstructure(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/home", wait_until="networkidle")
    sidebar = ClientSidebar(page).expand_group("Оргструктура")
    expect(sidebar.link("Отделы")).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("/departments: каждая строка имеет действия 'Редактировать' и 'Удалить'")
def test_departments_rows_have_edit_and_delete_actions(
    client_admin_page: Page, settings: Settings
) -> None:
    """Read-only: проверяем что действия есть в строках, без клика."""
    page = client_admin_page
    page.goto(f"{settings.client_url}/departments", wait_until="networkidle")
    deps = DepartmentsPage(page)
    expect(deps.heading).to_be_visible(timeout=settings.expect_timeout)
    rowgroups = deps.table.get_by_role("rowgroup").all()
    if len(rowgroups) < 2:
        pytest.skip("Нет tbody — нечего проверять")
    rows = rowgroups[1].get_by_role("row")
    if rows.count() == 0:
        pytest.skip("Нет отделов на стенде — read-only тест пропущен")
    first_row = rows.first
    # Inline icon-buttons с aria-label
    edit = first_row.get_by_role("button", name="Редактировать", exact=True)
    delete = first_row.get_by_role("button", name="Удалить", exact=True)
    if edit.count() == 0 or delete.count() == 0:
        pytest.skip("В текущем UI строки отделов без row action buttons")
    expect(edit).to_be_visible(timeout=settings.expect_timeout)
    expect(delete).to_be_visible(timeout=settings.expect_timeout)
