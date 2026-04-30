"""Филиалы /branches в Client UI — CRUD + boundary."""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Dialog, Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.branches_page import BranchCreateDialog, BranchesPage


def _open(page: Page, settings: Settings) -> BranchesPage:
    br = BranchesPage(page).goto(settings.client_url)
    expect(br.heading).to_be_visible(timeout=settings.nav_timeout)
    return br


def _fresh_title(prefix: str = "Br") -> str:
    return f"{E2E_PREFIX} {prefix} {secrets.token_hex(3)}"


@pytest.mark.positive
@allure.title("Branches: создание филиала под head-office")
def test_branch_create_appears_in_tree(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title()
    br = _open(client_admin_page, settings)
    br.click_add()
    dialog = BranchCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_title(title).submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    client_admin_page.wait_for_timeout(1_500)
    expect(br.branch_node(title)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Branches: Cancel закрывает диалог без создания")
def test_branch_create_cancel_does_not_create(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title("Cancel")
    br = _open(client_admin_page, settings)
    br.click_add()
    dialog = BranchCreateDialog(client_admin_page)
    dialog.fill_title(title).cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    client_admin_page.wait_for_timeout(1_500)
    expect(br.branch_node(title)).not_to_be_visible()


@pytest.mark.negative
@allure.title("Branches neg: пустое название → диалог остаётся")
def test_branch_create_empty_title_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    br = _open(client_admin_page, settings)
    br.click_add()
    dialog = BranchCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.submit()
    client_admin_page.wait_for_timeout(2_000)
    expect(dialog.dialog).to_be_visible()


@pytest.mark.negative
@pytest.mark.parametrize(
    "title",
    [
        pytest.param("X" * 500, id="too-long"),
        pytest.param("   ", id="only-spaces"),
        pytest.param("<script>alert(1)</script>", id="xss-payload"),
        pytest.param("'; DROP TABLE branches; --", id="sqli-payload"),
    ],
)
@allure.title("Branches boundary: '{title}' — payload не выполнен")
def test_branch_create_boundary(
    client_admin_page: Page, settings: Settings, title: str
) -> None:
    page = client_admin_page
    dialogs: list[str] = []

    def on_dialog(d: Dialog) -> None:
        dialogs.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)

    br = _open(page, settings)
    br.click_add()
    dialog = BranchCreateDialog(page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_title(title).submit()
    page.wait_for_timeout(2_000)
    assert dialogs == [], f"Payload вызвал JS dialog: {dialogs}"
