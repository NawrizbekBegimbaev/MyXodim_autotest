"""UC-3.5b Маршруты — конструктор шагов: настройки step через side-panel."""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.routes_page import RouteEditorPage, RoutesPage


def _open_editor(page: Page, settings: Settings) -> RouteEditorPage:
    rt = RoutesPage(page).goto(settings.client_url)
    expect(rt.heading).to_be_visible(timeout=settings.nav_timeout)
    rt.click_create()
    editor = RouteEditorPage(page)
    expect(editor.save_button).to_be_visible(timeout=settings.nav_timeout)
    return editor


def _fresh_route() -> str:
    return f"{E2E_PREFIX} CtorRoute {secrets.token_hex(3)}"


# Все тесты в файле мутируют состояние через UI (CRUD-формы).
pytestmark = pytest.mark.creates_data


@pytest.mark.positive
@allure.title("Routes constructor: click default step → открывается panel 'Настройки шага'")
def test_route_step_click_opens_settings_panel(
    client_admin_page: Page, settings: Settings
) -> None:
    editor = _open_editor(client_admin_page, settings)
    panel = editor.click_default_step()
    expect(panel.panel_title).to_be_visible(timeout=settings.expect_timeout)
    expect(panel.name_input).to_be_visible()
    expect(panel.delete_button).to_be_visible()


@pytest.mark.positive
@allure.title("Routes constructor: close-кнопка panel → панель закрывается")
def test_route_step_panel_close_button(
    client_admin_page: Page, settings: Settings
) -> None:
    editor = _open_editor(client_admin_page, settings)
    panel = editor.click_default_step()
    expect(panel.panel_title).to_be_visible(timeout=settings.expect_timeout)
    panel.close()
    client_admin_page.wait_for_timeout(800)
    expect(panel.panel_title).not_to_be_visible()


@pytest.mark.positive
@allure.title("Routes constructor: смена типа действия (Простое утверждение → ЭЦП подпись)")
def test_route_step_change_action_type(
    client_admin_page: Page, settings: Settings
) -> None:
    editor = _open_editor(client_admin_page, settings)
    panel = editor.click_default_step()
    expect(panel.panel_title).to_be_visible(timeout=settings.expect_timeout)
    panel.click_action("ЭЦП подпись")
    client_admin_page.wait_for_timeout(800)
    # Смена ничего не сломала — panel остался
    expect(panel.panel_title).to_be_visible()


@pytest.mark.positive
@allure.title("Routes constructor: задать имя и срок шага → save маршрута проходит")
def test_route_step_fill_name_and_duration_then_save(
    client_admin_page: Page, settings: Settings
) -> None:
    route_name = _fresh_route()
    editor = _open_editor(client_admin_page, settings)
    editor.fill_name(route_name).fill_description("E2E ctor")

    panel = editor.click_default_step()
    expect(panel.panel_title).to_be_visible(timeout=settings.expect_timeout)
    panel.fill_name("[E2E] Шаг согласования")
    panel.set_duration_days(5)
    panel.close()
    client_admin_page.wait_for_timeout(500)

    editor.save()
    client_admin_page.wait_for_timeout(3_000)

    rt = RoutesPage(client_admin_page).goto(settings.client_url)
    expect(rt.heading).to_be_visible(timeout=settings.nav_timeout)
    rt.search(route_name)
    client_admin_page.wait_for_timeout(1_500)
    expect(rt.row_by_name(route_name)).to_be_visible(timeout=settings.nav_timeout)
