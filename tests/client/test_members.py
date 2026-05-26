"""BRD 3.0 Сотрудники (/members) validation sentinels."""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.member_create_dialog import MemberCreateDialog
from pages.client.members_page import MembersPage


def _open_create_dialog(
    client_admin_page: Page, settings: Settings
) -> MemberCreateDialog:
    members = MembersPage(client_admin_page).goto(settings.client_url)
    expect(members.heading).to_be_visible(timeout=settings.nav_timeout)
    members.click_add()
    dialog = MemberCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    return dialog


@pytest.mark.negative
@allure.title("BRD 3.0 /members: PИНФЛ is required")
def test_member_create_without_pinfl_rejected(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    dialog = _open_create_dialog(client_admin_page, settings)
    dialog.fill_required(
        first_name="Тест",
        last_name="[E2E] NoPinfl",
        phone=random_test_phone,
        role="Сотрудник",
    )
    dialog.submit()
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.skip(reason="BUG-014: jobTitle not required in /members create UI")
@pytest.mark.negative
@allure.title("BUG-014 sentinel: jobTitle should be required per BRD 3.6")
def test_member_create_without_jobtitle_rejected_per_brd_3_6() -> None:
    """BRD 3.6 requires Должность; current UI allows it empty."""


@pytest.mark.skip(reason="BUG-014: department not required in /members create UI")
@pytest.mark.negative
@allure.title("BUG-014 sentinel: department should be required per BRD 3.6")
def test_member_create_without_department_rejected_per_brd_3_6() -> None:
    """BRD 3.6 requires Подразделение; current UI allows it empty."""


@pytest.mark.skip(reason="BUG-014: jobTitle/department not required in UI")
@pytest.mark.negative
@allure.title("BUG-014 sentinel: member dialog should mark jobTitle required")
def test_member_create_dialog_has_required_jobtitle_per_brd_3_6() -> None:
    """Должность должна быть required (звёздочка + validation)."""
