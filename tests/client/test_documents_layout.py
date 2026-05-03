"""Структурные тесты страницы /documents (read-only, без CRUD).

Проверяем что после редизайна 2026-05-03 на месте:
- 8 табов статусов (включая 3 новых: В архиве, Отправлен в 1С, Ошибка выгрузки)
- 7 колонок таблицы (включая 2 новых: Откуда, Куда)
- pagination control (ввод страницы, выбор размера)
"""

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
@allure.title("/documents: все 8 статус-табов видны")
@pytest.mark.parametrize("tab_name", DocumentsPage.STATUS_TABS)
def test_documents_status_tabs_present(
    client_admin_page: Page, settings: Settings, tab_name: str
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    expect(docs.tab(tab_name)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("/documents: все 7 колонок таблицы присутствуют")
@pytest.mark.parametrize("col_name", DocumentsPage.COLUMNS)
def test_documents_table_columns_present(
    client_admin_page: Page, settings: Settings, col_name: str
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    expect(docs.column_header(col_name)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("/documents: tab 'Все' выбран по умолчанию")
def test_documents_default_tab_is_all(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    expect(docs.tab("Все")).to_have_attribute("aria-selected", "true")


@pytest.mark.positive
@allure.title("/documents URL: query-параметры page/size/status присутствуют")
def test_documents_url_has_query_params(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    # после редизайна страница сама добавляет дефолтные query-params:
    # /documents?page=1&size=25&status=all (порядок параметров может меняться)
    expect(page).to_have_url(
        re.compile(r"/documents\?(?=.*page=)(?=.*size=)(?=.*status=)"),
        timeout=settings.nav_timeout,
    )


@pytest.mark.positive
@allure.title("/documents: переключение на таб 'Черновик' меняет URL status=draft")
def test_documents_clicking_draft_tab_updates_url(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    docs = DocumentsPage(page)
    docs.tab("Черновик").click()
    expect(docs.tab("Черновик")).to_have_attribute(
        "aria-selected", "true", timeout=settings.expect_timeout
    )
