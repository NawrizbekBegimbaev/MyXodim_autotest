"""UC-3.6: edit и disable/enable сотрудника в Client UI."""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.member_create_dialog import MemberCreateDialog
from pages.client.member_edit_dialog import MemberEditDialog
from pages.client.members_page import MembersPage


def _create_member_via_ui(
    client_admin_page: Page, settings: Settings, phone: str, last_name: str
) -> MembersPage:
    members = MembersPage(client_admin_page).goto(settings.client_url)
    members.click_add()
    dialog = MemberCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_required(
        first_name="Тест", last_name=last_name, phone=phone, role="Сотрудник"
    )
    dialog.submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    return members


@pytest.mark.positive
@allure.title("UC-3.6 edit: изменение фамилии существующего сотрудника")
def test_member_edit_last_name_updates_in_list(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    suffix = secrets.token_hex(3)
    initial_last = f"[E2E] Initial {suffix}"
    new_last = f"[E2E] Updated {suffix}"
    phone = random_test_phone

    members = _create_member_via_ui(client_admin_page, settings, phone, initial_last)
    members.search(phone)
    expect(members.row_by_phone(phone)).to_be_visible(timeout=settings.nav_timeout)

    # Открываем edit
    members.click_edit_for_phone(phone)
    edit = MemberEditDialog(client_admin_page)
    expect(edit.dialog).to_be_visible(timeout=settings.expect_timeout)

    # Меняем фамилию и сохраняем
    edit.update_last_name(new_last)
    edit.submit()
    expect(edit.dialog).to_be_hidden(timeout=settings.expect_timeout)

    # Возвращаемся в список — search по тому же телефону → видна новая фамилия
    members.search(phone)
    client_admin_page.wait_for_timeout(1_500)
    row = members.row_by_phone(phone)
    expect(row).to_contain_text(new_last, timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("UC-3.6 edit: Cancel не сохраняет изменения")
def test_member_edit_cancel_does_not_save(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    suffix = secrets.token_hex(3)
    initial_last = f"[E2E] Keep {suffix}"
    phone = random_test_phone

    members = _create_member_via_ui(client_admin_page, settings, phone, initial_last)
    members.search(phone)
    expect(members.row_by_phone(phone)).to_be_visible(timeout=settings.nav_timeout)

    members.click_edit_for_phone(phone)
    edit = MemberEditDialog(client_admin_page)
    expect(edit.dialog).to_be_visible(timeout=settings.expect_timeout)
    edit.update_last_name(f"[E2E] Discarded {suffix}")
    edit.cancel()
    expect(edit.dialog).to_be_hidden(timeout=settings.expect_timeout)

    members.search(phone)
    client_admin_page.wait_for_timeout(1_500)
    row = members.row_by_phone(phone)
    expect(row).to_contain_text(initial_last, timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("UC-3.6 disable: отключение активного сотрудника → статус Отключён")
def test_member_disable_changes_status(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    suffix = secrets.token_hex(3)
    phone = random_test_phone

    members = _create_member_via_ui(
        client_admin_page, settings, phone, f"[E2E] Disable {suffix}"
    )
    members.search(phone)
    expect(members.row_by_phone(phone)).to_be_visible(timeout=settings.nav_timeout)

    members.click_disable_for_phone(phone)
    client_admin_page.wait_for_timeout(2_000)

    members.search(phone)
    client_admin_page.wait_for_timeout(1_500)
    row = members.row_by_phone(phone)
    expect(row).to_contain_text("Отключён", timeout=settings.expect_timeout)


# ---------- Search ----------


@pytest.mark.positive
@allure.title("UC-3.6 search: поиск по телефону фильтрует список")
def test_members_search_by_phone_filters_list(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    suffix = secrets.token_hex(3)
    phone = random_test_phone
    last = f"[E2E] Search {suffix}"

    members = _create_member_via_ui(client_admin_page, settings, phone, last)
    members.search(phone)
    client_admin_page.wait_for_timeout(1_500)
    expect(members.row_by_phone(phone)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("UC-3.6 search: поиск по фамилии находит сотрудника")
def test_members_search_by_last_name_filters_list(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    suffix = secrets.token_hex(3)
    phone = random_test_phone
    last = f"[E2E] Search {suffix}"

    members = _create_member_via_ui(client_admin_page, settings, phone, last)
    members.search(suffix)
    client_admin_page.wait_for_timeout(1_500)
    expect(members.row_by_phone(phone)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.negative
@allure.title("UC-3.6 search: несуществующая строка → empty list")
def test_members_search_with_no_match_returns_empty(
    client_admin_page: Page, settings: Settings
) -> None:
    members = MembersPage(client_admin_page).goto(settings.client_url)
    expect(members.heading).to_be_visible(timeout=settings.nav_timeout)
    members.search("__no_such_member_xyz_98765__")
    client_admin_page.wait_for_timeout(1_500)
    # таблица показывает 0 data rows
    rows = members.table.get_by_role("row").all()
    # rows[0] = header; data rows должны быть пустые/empty-state
    assert len(rows) <= 2, f"Ожидали ≤2 row (header + опц. empty-state), получили {len(rows)}"
