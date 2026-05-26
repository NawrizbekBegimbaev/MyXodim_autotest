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
    expect(panel.panel_title).not_to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Routes constructor: смена типа действия (Простое утверждение → ЭЦП подпись)")
def test_route_step_change_action_type(
    client_admin_page: Page, settings: Settings
) -> None:
    editor = _open_editor(client_admin_page, settings)
    panel = editor.click_default_step()
    expect(panel.panel_title).to_be_visible(timeout=settings.expect_timeout)
    panel.click_action("ЭЦП подпись")
    # Смена ничего не сломала — panel остался
    expect(panel.panel_title).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("BRD 3.0 Routes: target combo has Role, Employee, Department options")
def test_route_step_target_combo_has_role_employee_department_options(
    client_admin_page: Page, settings: Settings
) -> None:
    editor = _open_editor(client_admin_page, settings)
    panel = editor.click_default_step()
    panel.target_type_combobox.click()
    for option in ("Роль для согласований", "Сотрудник", "Подразделение"):
        expect(panel.target_option(option)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.creates_data
@pytest.mark.needs_invitees
@pytest.mark.skip(reason="Requires department fixture and route save data setup")
@pytest.mark.positive
@allure.title("BRD 3.0 Routes: department target can be saved")
def test_route_step_with_department_target_succeeds(
    client_admin_page: Page, settings: Settings
) -> None:
    route_name = _fresh_route()
    editor = _open_editor(client_admin_page, settings)
    editor.fill_name(route_name)
    panel = editor.click_default_step()
    panel.select_target_department("[E2E] Подразделение")
    panel.close()
    editor.save()
    expect(RoutesPage(client_admin_page).goto(settings.client_url).heading).to_be_visible(
        timeout=settings.nav_timeout
    )


@pytest.mark.skip(reason="DOC-004: Position target removed from BRD 3.0 route builder")
@pytest.mark.negative
@allure.title("DOC-004 sentinel: route step with Position target")
def test_route_step_with_position_target() -> None:
    """Позиция как route target удалена; оставить skip до финального PO решения."""


@pytest.mark.creates_data
@pytest.mark.needs_invitees
@pytest.mark.skip(reason="Route constructor save requires workflow targets/invitees; deferred")
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
