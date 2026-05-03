"""Роли /roles в Client UI."""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.roles_page import RoleCreateDialog, RolesPage


def _open(page: Page, settings: Settings) -> RolesPage:
    rl = RolesPage(page).goto(settings.client_url)
    expect(rl.heading).to_be_visible(timeout=settings.nav_timeout)
    return rl


def _fresh_title() -> str:
    return f"{E2E_PREFIX} Role {secrets.token_hex(3)}"


# Все тесты в файле мутируют состояние через UI (CRUD-формы).
pytestmark = pytest.mark.creates_data


@pytest.mark.positive
@allure.title("Roles: создание роли → видна в списке после reload")
def test_role_create_appears_in_list_after_reload(
    client_admin_page: Page, settings: Settings
) -> None:
    """Имя роли может быть нормализовано фронтом (uppercase, без spec-chars).
    После create делаем reload чтобы таблица перерисовалась с новой ролью.
    """
    suffix = "".join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(6))
    title = f"E2EROLE{suffix}"
    description = "Описание для регрессионного теста"
    rl = _open(client_admin_page, settings)
    rl.click_add()
    dialog = RoleCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill(title=title, description=description).submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    client_admin_page.reload(wait_until="networkidle")
    client_admin_page.wait_for_timeout(2_500)
    # Снимаем snapshot для отладки если упадёт
    body = client_admin_page.locator("body").inner_text()
    assert title in body, f"Имя '{title}' не найдено в body. Фрагмент: {body[:500]}"


@pytest.mark.positive
@allure.title("Roles: Cancel закрывает диалог без создания")
def test_role_create_cancel_does_not_create(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title()
    rl = _open(client_admin_page, settings)
    rl.click_add()
    dialog = RoleCreateDialog(client_admin_page)
    dialog.fill(title=title, description="cancel").cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    client_admin_page.wait_for_timeout(1_500)
    expect(rl.row_by_title(title.upper())).not_to_be_visible()


@pytest.mark.negative
@allure.title("Roles neg: пустое название → диалог остаётся")
def test_role_create_empty_title_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    rl = _open(client_admin_page, settings)
    rl.click_add()
    dialog = RoleCreateDialog(client_admin_page)
    dialog.fill(title="", description="desc").submit()
    client_admin_page.wait_for_timeout(2_000)
    expect(dialog.dialog).to_be_visible()


@pytest.mark.negative
@allure.title("Roles neg: пустое описание → диалог остаётся (фронт-валидация)")
def test_role_create_empty_description_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    rl = _open(client_admin_page, settings)
    rl.click_add()
    dialog = RoleCreateDialog(client_admin_page)
    dialog.fill(title=_fresh_title(), description="").submit()
    client_admin_page.wait_for_timeout(2_000)
    expect(dialog.dialog).to_be_visible()
