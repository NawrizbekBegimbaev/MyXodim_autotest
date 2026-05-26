"""UC-3.7 Должности (/positions) — CRUD + boundary в Client UI."""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.position_dialogs import (
    PositionCreateDialog,
    PositionDeleteConfirmDialog,
    PositionEditDialog,
)
from pages.client.positions_page import PositionsPage

MUTATES_RECON_TENANT = pytest.mark.skip(
    reason="Position CRUD mutates recon tenant; deferred until dedicated data setup"
)


def _open_positions(page: Page, settings: Settings) -> PositionsPage:
    pos = PositionsPage(page).goto(settings.client_url)
    expect(pos.heading).to_be_visible(timeout=settings.nav_timeout)
    return pos


def _fresh_title(prefix: str = "Должн") -> str:
    return f"{E2E_PREFIX} {prefix} {secrets.token_hex(3)}"


# ---------- Positive ----------


@pytest.mark.smoke
@pytest.mark.positive
@allure.title("BRD 3.0 /positions: table has Code and Created date columns")
def test_positions_table_has_code_and_date_columns(
    client_admin_page: Page, settings: Settings
) -> None:
    pos = _open_positions(client_admin_page, settings)
    for column in PositionsPage.COLUMNS:
        expect(pos.column_header(column)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("BRD 3.0 /positions: code filter accepts input")
def test_positions_filter_by_code(client_admin_page: Page, settings: Settings) -> None:
    pos = _open_positions(client_admin_page, settings)
    pos.filter_by_code("E2E-CODE")
    expect(pos.code_filter).to_have_value("E2E-CODE")


@pytest.mark.positive
@allure.title("BRD 3.0 /positions: date range filters accept input")
def test_positions_filter_by_date_range(
    client_admin_page: Page, settings: Settings
) -> None:
    pos = _open_positions(client_admin_page, settings)
    pos.filter_by_date_range("2026-05-01", "2026-05-26")
    expect(pos.date_from_filter).to_have_value("2026-05-01")
    expect(pos.date_to_filter).to_have_value("2026-05-26")


@pytest.mark.positive
@allure.title("BRD 3.0 /positions: reset clears query filters")
def test_positions_reset_filters_clears_query(
    client_admin_page: Page, settings: Settings
) -> None:
    pos = _open_positions(client_admin_page, settings)
    pos.search("E2E").filter_by_code("E2E-CODE").reset_filters()
    expect(pos.search_input).to_have_value("")
    expect(pos.code_filter).to_have_value("")


@pytest.mark.skip(reason="Needs existing position fixture with row action in recon tenant")
@pytest.mark.positive
@allure.title("BRD 3.0 /positions: row action opens detail card")
def test_positions_open_card_navigates_to_detail(
    client_admin_page: Page, settings: Settings
) -> None:
    pos = _open_positions(client_admin_page, settings)
    pos.open_card("Директор")
    expect(client_admin_page).to_have_url(r"/positions/.+")


@MUTATES_RECON_TENANT
@pytest.mark.positive
@allure.title("UC-3.7: создание должности → появляется в списке")
def test_position_create_appears_in_list(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title()
    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    dialog = PositionCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_title(title).submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    pos.search(title)
    expect(pos.row_by_title(title)).to_be_visible(timeout=settings.expect_timeout)


@MUTATES_RECON_TENANT
@pytest.mark.positive
@allure.title("UC-3.7 edit: меняем название должности")
def test_position_edit_updates_title(
    client_admin_page: Page, settings: Settings
) -> None:
    initial = _fresh_title("Init")
    updated = f"{initial} (upd)"

    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    PositionCreateDialog(client_admin_page).fill_title(initial).submit()
    pos.search(initial)
    expect(pos.row_by_title(initial)).to_be_visible(timeout=settings.nav_timeout)

    pos.click_edit_for(initial)
    edit = PositionEditDialog(client_admin_page)
    expect(edit.dialog).to_be_visible(timeout=settings.expect_timeout)
    edit.fill_title(updated).submit()
    expect(edit.dialog).to_be_hidden(timeout=settings.expect_timeout)

    pos.search(updated)
    expect(pos.row_by_title(updated)).to_be_visible(timeout=settings.nav_timeout)


@MUTATES_RECON_TENANT
@pytest.mark.positive
@allure.title("UC-3.7 delete: подтверждение → должность исчезает")
def test_position_delete_with_confirmation_removes_row(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title("Del")
    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    PositionCreateDialog(client_admin_page).fill_title(title).submit()
    pos.search(title)
    expect(pos.row_by_title(title)).to_be_visible(timeout=settings.nav_timeout)

    pos.click_delete_for(title)
    confirm = PositionDeleteConfirmDialog(client_admin_page)
    expect(confirm.dialog).to_be_visible(timeout=settings.expect_timeout)
    confirm.confirm()
    expect(confirm.dialog).to_be_hidden(timeout=settings.expect_timeout)

    pos.search(title)
    # not_to_be_visible имеет встроенный retry до expect_timeout
    expect(pos.row_by_title(title)).not_to_be_visible()


@MUTATES_RECON_TENANT
@pytest.mark.positive
@allure.title("UC-3.7 delete: Cancel в confirmation → должность остаётся")
def test_position_delete_cancel_keeps_row(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title("Keep")
    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    PositionCreateDialog(client_admin_page).fill_title(title).submit()
    pos.search(title)
    expect(pos.row_by_title(title)).to_be_visible(timeout=settings.nav_timeout)

    pos.click_delete_for(title)
    confirm = PositionDeleteConfirmDialog(client_admin_page)
    confirm.cancel()
    expect(confirm.dialog).to_be_hidden(timeout=settings.expect_timeout)

    pos.search(title)
    expect(pos.row_by_title(title)).to_be_visible(timeout=settings.expect_timeout)


@MUTATES_RECON_TENANT
@pytest.mark.positive
@allure.title("UC-3.7 search: фильтр по названию")
def test_positions_search_filters_list(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title("Search")
    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    PositionCreateDialog(client_admin_page).fill_title(title).submit()

    pos.search(title)
    expect(pos.row_by_title(title)).to_be_visible(timeout=settings.nav_timeout)


# ---------- Negative ----------


@MUTATES_RECON_TENANT
@pytest.mark.negative
@allure.title("UC-3.7 neg: пустое название → submit blocked / диалог остаётся")
def test_position_create_with_empty_title_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    dialog = PositionCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.submit()
    # без названия submit заблокирован — диалог остаётся (expect ретраится)
    expect(dialog.dialog).to_be_visible()


@MUTATES_RECON_TENANT
@pytest.mark.positive
@allure.title("UC-3.7: повторное создание с тем же названием — поведение фронта (smoke check)")
def test_position_create_with_duplicate_title_does_not_crash(
    client_admin_page: Page, settings: Settings
) -> None:
    """По BRD §3.7 имя должности уникально, но точное поведение фронта на дубль
    не задокументировано. Тест проверяет только что страница не падает.
    """
    title = _fresh_title("Dup")
    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    dialog1 = PositionCreateDialog(client_admin_page)
    expect(dialog1.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog1.fill_title(title).submit()
    # ждём первого создания: либо диалог закрылся (успех), либо строка появилась
    expect(dialog1.dialog).to_be_hidden(timeout=settings.nav_timeout)

    pos.click_add()
    dialog2 = PositionCreateDialog(client_admin_page)
    expect(dialog2.dialog).to_be_visible(timeout=settings.nav_timeout)
    dialog2.fill_title(title).submit()
    # Не assert'им конкретное поведение — главное что нет crash
    expect(pos.heading).to_be_visible()


@MUTATES_RECON_TENANT
@pytest.mark.negative
@allure.title("BRD 3.0 /positions: duplicate code is rejected")
def test_position_create_duplicate_code_rejected(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title("DupCode")
    code = f"E2E-{secrets.token_hex(3)}"
    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    PositionCreateDialog(client_admin_page).fill_title(title).fill_code(code).submit()
    pos.click_add()
    dialog = PositionCreateDialog(client_admin_page)
    dialog.fill_title(f"{title} copy").fill_code(code).submit()
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)


@MUTATES_RECON_TENANT
@pytest.mark.positive
@allure.title("UC-3.7: Cancel закрывает диалог без создания")
def test_position_create_cancel_does_not_create(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title("Cancel")
    pos = _open_positions(client_admin_page, settings)
    pos.click_add()
    dialog = PositionCreateDialog(client_admin_page)
    dialog.fill_title(title).cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    pos.search(title)
    expect(pos.row_by_title(title)).not_to_be_visible()


# ---------- Boundary ----------


@MUTATES_RECON_TENANT
@pytest.mark.negative
@pytest.mark.parametrize(
    "title",
    [
        pytest.param("X" * 500, id="too-long"),
        pytest.param("   ", id="only-spaces"),
        pytest.param("<script>alert(1)</script>", id="xss-payload"),
        pytest.param("'; DROP TABLE positions; --", id="sqli-payload"),
    ],
)
@allure.title("UC-3.7 boundary: '{title}' не приводит к alert/dialog/crash")
def test_position_create_boundary_title(
    client_admin_page: Page, settings: Settings, title: str
) -> None:
    """XSS/SQLi не должны выполняться. Диалог не упал."""
    from playwright.sync_api import Dialog

    page = client_admin_page
    dialogs: list[str] = []

    def on_dialog(d: Dialog) -> None:
        dialogs.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)

    pos = _open_positions(page, settings)
    pos.click_add()
    dialog = PositionCreateDialog(page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_title(title).submit()
    # XSS/SQLi: даём 2s браузеру выполнить пейлоад если фронт уязвим.
    # Это не sync-wait, это таймер на потенциальное async выполнение.
    page.wait_for_timeout(2_000)
    assert dialogs == [], f"Payload вызвал JS dialog: {dialogs}"
