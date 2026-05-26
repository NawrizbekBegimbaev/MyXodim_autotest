"""BRD 3.0 Подразделения (/departments)."""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.departments_page import DepartmentCreateDialog, DepartmentsPage


def _open_departments(page: Page, settings: Settings) -> DepartmentsPage:
    departments = DepartmentsPage(page).goto(settings.client_url)
    expect(departments.heading).to_be_visible(timeout=settings.nav_timeout)
    return departments


@pytest.mark.smoke
@pytest.mark.positive
@allure.title("BRD 3.0 /departments: table has Branch column")
def test_departments_table_has_branch_column(
    client_admin_page: Page, settings: Settings
) -> None:
    departments = _open_departments(client_admin_page, settings)
    expect(departments.column_header("Филиал")).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.positive
@allure.title("BRD 3.0 /departments: create dialog opens")
def test_department_create_dialog_opens(
    client_admin_page: Page, settings: Settings
) -> None:
    departments = _open_departments(client_admin_page, settings)
    departments.click_add()
    dialog = DepartmentCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    expect(dialog.name_input).to_be_visible()
    expect(dialog.code_input).to_be_visible()
    expect(dialog.parent_combo).to_be_visible()


@pytest.mark.creates_data
@pytest.mark.skip(reason="Department create mutates recon tenant; needs dedicated data setup")
@pytest.mark.positive
@allure.title("BRD 3.0 /departments: create child department succeeds")
def test_department_create_with_parent_succeeds(
    client_admin_page: Page, settings: Settings
) -> None:
    name = f"{E2E_PREFIX} Подразделение {secrets.token_hex(3)}"
    departments = _open_departments(client_admin_page, settings)
    departments.click_add()
    dialog = DepartmentCreateDialog(client_admin_page)
    dialog.fill_name(name).fill_code(f"E2E-{secrets.token_hex(3)}").submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    departments.search(name)
    expect(departments.row_by_name(name)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.negative
@allure.title("BRD 3.0 /departments: empty name is rejected")
def test_department_create_empty_name_rejected(
    client_admin_page: Page, settings: Settings
) -> None:
    departments = _open_departments(client_admin_page, settings)
    departments.click_add()
    dialog = DepartmentCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.submit()
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.skip(reason="BUG-015: branch combobox absent in DepartmentCreateDialog UI")
@pytest.mark.negative
@allure.title("BUG-015 sentinel: department create should support branch selection")
def test_department_create_with_branch_selection() -> None:
    """BRD 3.0 expects branch selection; current UI has no branch field."""
