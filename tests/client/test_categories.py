"""Категории /categories в Client UI — CRUD + boundary."""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Dialog, Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.categories_page import CategoriesPage, CategoryCreateDialog


def _open(page: Page, settings: Settings) -> CategoriesPage:
    cats = CategoriesPage(page).goto(settings.client_url)
    expect(cats.heading).to_be_visible(timeout=settings.nav_timeout)
    return cats


def _fresh_title(prefix: str = "Cat") -> str:
    return f"{E2E_PREFIX} {prefix} {secrets.token_hex(3)}"


# ---------- Positive ----------


@pytest.mark.positive
@allure.title("Categories: создание корневой категории → видна в дереве")
def test_category_create_root_appears_in_tree(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title()
    cats = _open(client_admin_page, settings)
    cats.click_add()
    dialog = CategoryCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_title(title).submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    expect(cats.category_node(title)).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("Categories: создание дочерней категории под существующим родителем")
def test_category_create_child_under_parent(
    client_admin_page: Page, settings: Settings
) -> None:
    parent = _fresh_title("Parent")
    child = _fresh_title("Child")

    cats = _open(client_admin_page, settings)
    # Сначала родителя — ждём что нода появилась в дереве, иначе select_parent её не найдёт
    cats.click_add()
    CategoryCreateDialog(client_admin_page).fill_title(parent).submit()
    expect(cats.category_node(parent)).to_be_visible(timeout=settings.nav_timeout)

    # Теперь дочернюю
    cats.click_add()
    dialog2 = CategoryCreateDialog(client_admin_page)
    expect(dialog2.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog2.fill_title(child).select_parent(parent).submit()
    expect(dialog2.dialog).to_be_hidden(timeout=settings.expect_timeout)
    expect(cats.category_node(child)).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("Categories: heading 'Древовидная структура' виден")
def test_categories_tree_heading_visible(
    client_admin_page: Page, settings: Settings
) -> None:
    cats = _open(client_admin_page, settings)
    expect(cats.tree_heading).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Categories: Cancel закрывает диалог без создания")
def test_category_create_cancel_does_not_create(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title("Cancel")
    cats = _open(client_admin_page, settings)
    cats.click_add()
    dialog = CategoryCreateDialog(client_admin_page)
    dialog.fill_title(title).cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    expect(cats.category_node(title)).not_to_be_visible()


# ---------- Negative ----------


@pytest.mark.negative
@allure.title("Categories neg: пустое название → submit blocked / dialog stays")
def test_category_create_with_empty_title_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    cats = _open(client_admin_page, settings)
    cats.click_add()
    dialog = CategoryCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.submit()
    # без названия submit заблокирован/отклонён — диалог остаётся (expect ретраится)
    expect(dialog.dialog).to_be_visible()


# ---------- Boundary ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "title",
    [
        pytest.param("X" * 500, id="too-long"),
        pytest.param("   ", id="only-spaces"),
        pytest.param("<script>alert(1)</script>", id="xss-payload"),
        pytest.param("'; DROP TABLE categories; --", id="sqli-payload"),
    ],
)
@allure.title("Categories boundary: '{title}' — ничего не падает / payload не выполнен")
def test_category_create_boundary_title(
    client_admin_page: Page, settings: Settings, title: str
) -> None:
    page = client_admin_page
    dialogs: list[str] = []

    def on_dialog(d: Dialog) -> None:
        dialogs.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)

    cats = _open(page, settings)
    cats.click_add()
    dialog = CategoryCreateDialog(page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_title(title).submit()
    # XSS/SQLi: даём 2s браузеру выполнить пейлоад если фронт уязвим.
    page.wait_for_timeout(2_000)
    assert dialogs == [], f"Payload вызвал JS dialog: {dialogs}"
