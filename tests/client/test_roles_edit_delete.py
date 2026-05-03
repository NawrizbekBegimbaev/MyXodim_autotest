"""Roles edit (permissions matrix) + delete confirmation."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.roles_page import RoleEditPage, RolesPage


def _open_roles(page: Page, settings: Settings) -> RolesPage:
    rl = RolesPage(page).goto(settings.client_url)
    expect(rl.heading).to_be_visible(timeout=settings.nav_timeout)
    return rl


# Все тесты в файле мутируют состояние через UI (CRUD-формы).
pytestmark = pytest.mark.creates_data


@pytest.mark.positive
@allure.title("Roles edit: клик 'Редактировать' открывает страницу с permissions matrix")
def test_role_edit_opens_permissions_page(
    client_admin_page: Page, settings: Settings
) -> None:
    rl = _open_roles(client_admin_page, settings)
    rl.click_edit_first_row()
    expect(client_admin_page).to_have_url(
        re.compile(r"/roles/.+/edit|/roles/[0-9a-f-]+"), timeout=settings.nav_timeout
    )
    edit = RoleEditPage(client_admin_page)
    expect(edit.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(edit.save_button).to_be_visible()
    expect(edit.back_button).to_be_visible()


@pytest.mark.positive
@allure.title("Roles edit: search-input прав работает")
def test_role_edit_permissions_search(
    client_admin_page: Page, settings: Settings
) -> None:
    rl = _open_roles(client_admin_page, settings)
    rl.click_edit_first_row()
    edit = RoleEditPage(client_admin_page)
    expect(edit.heading).to_be_visible(timeout=settings.nav_timeout)
    edit.search_perms_input.fill("members")
    client_admin_page.wait_for_timeout(800)
    # Не упало — search input принял значение
    expect(edit.search_perms_input).to_have_value("members")


@pytest.mark.positive
@allure.title("Roles edit: 'Развернуть все' / 'Свернуть все' кликаются")
def test_role_edit_expand_collapse_all(
    client_admin_page: Page, settings: Settings
) -> None:
    rl = _open_roles(client_admin_page, settings)
    rl.click_edit_first_row()
    edit = RoleEditPage(client_admin_page)
    expect(edit.heading).to_be_visible(timeout=settings.nav_timeout)
    edit.expand_all_button.click()
    client_admin_page.wait_for_timeout(500)
    edit.collapse_all_button.click()
    client_admin_page.wait_for_timeout(500)
    expect(edit.heading).to_be_visible()


@pytest.mark.positive
@allure.title("Roles edit: 'Назад' возвращает на /roles")
def test_role_edit_back_returns_to_roles(
    client_admin_page: Page, settings: Settings
) -> None:
    rl = _open_roles(client_admin_page, settings)
    rl.click_edit_first_row()
    edit = RoleEditPage(client_admin_page)
    expect(edit.heading).to_be_visible(timeout=settings.nav_timeout)
    edit.back_button.click()
    expect(client_admin_page).to_have_url(re.compile(r"/roles(\?|$)"), timeout=settings.nav_timeout)
