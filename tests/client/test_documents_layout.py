"""Структурные тесты страницы /documents (read-only, без CRUD)."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.documents_page import DocumentsPage


@pytest.mark.positive
@allure.title("/documents: страница рендерится с heading и кнопкой 'Создать документ'")
def test_documents_page_renders_heading_and_create(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    expect(docs.heading).to_be_visible(timeout=settings.expect_timeout)
    expect(docs.create_button).to_be_visible()


@pytest.mark.positive
@allure.title("/documents: view-toggle Канбан/Таблица виден")
def test_documents_view_toggle_present(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    expect(docs.kanban_button).to_be_visible(timeout=settings.expect_timeout)
    expect(docs.table_button).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("/documents: все 6 колонок таблицы присутствуют")
@pytest.mark.parametrize("col_name", DocumentsPage.COLUMNS)
def test_documents_table_columns_present(
    client_admin_page: Page, settings: Settings, col_name: str
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    expect(docs.column_header(col_name)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("/documents: table view можно выбрать")
def test_documents_can_switch_to_table(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    docs.switch_to_table()
    expect(docs.table_button).to_have_attribute(
        "aria-pressed", "true", timeout=settings.expect_timeout
    )


@pytest.mark.positive
@allure.title("/documents URL: view query-param присутствует")
def test_documents_url_has_query_params(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    expect(page).to_have_url(
        re.compile(r"/documents(?:\?.*view=)?"),
        timeout=settings.nav_timeout,
    )


@pytest.mark.positive
@allure.title("/documents: переключение на kanban view")
def test_documents_clicking_kanban_updates_pressed_state(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    docs.switch_to_kanban()
    expect(docs.kanban_button).to_have_attribute(
        "aria-pressed", "true", timeout=settings.expect_timeout
    )
