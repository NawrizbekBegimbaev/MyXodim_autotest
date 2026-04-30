"""Inbox + Организация + Интеграция + Штатные позиции — view-only страницы."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.inbox_page import InboxPage
from pages.client.organization_page import (
    IntegrationPage,
    OrganizationPage,
    OrgPositionsPage,
)

# ---------- Inbox ----------


@pytest.mark.positive
@allure.title("Inbox: открывается, показан heading и табы статусов")
def test_inbox_page_opens(
    client_admin_page: Page, settings: Settings
) -> None:
    page = InboxPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.search_input).to_be_visible(timeout=settings.expect_timeout)
    for tab in ["Все", "Черновик", "В работе", "Завершён"]:
        expect(page.status_tab(tab)).to_be_visible()


@pytest.mark.positive
@allure.title("Inbox: переключение табов не ломает страницу")
def test_inbox_tab_switching(
    client_admin_page: Page, settings: Settings
) -> None:
    page = InboxPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    page.status_tab("Завершён").click()
    client_admin_page.wait_for_timeout(800)
    expect(page.heading).to_be_visible()
    page.status_tab("Все").click()
    client_admin_page.wait_for_timeout(500)
    expect(page.heading).to_be_visible()


# ---------- Organization ----------


@pytest.mark.positive
@allure.title("Organization: страница содержит основные секции")
def test_organization_page_shows_sections(
    client_admin_page: Page, settings: Settings
) -> None:
    page = OrganizationPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.section_basic).to_be_visible()
    expect(page.section_integration).to_be_visible()


@pytest.mark.positive
@allure.title("Organization: ключ интеграции в формате bh_live_<32hex>")
def test_organization_shows_integration_key(
    client_admin_page: Page, settings: Settings
) -> None:
    page = OrganizationPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    # Ключ может быть в формате bh_live_... или key-... (legacy)
    key_locator = client_admin_page.get_by_text(re.compile(r"(bh_live_[a-f0-9]{32}|key-[a-f0-9]+)"))
    expect(key_locator.first).to_be_visible(timeout=settings.expect_timeout)


# ---------- Integration ----------


@pytest.mark.positive
@allure.title("Integration: страница открывается, ключ показан")
def test_integration_page_shows_key(
    client_admin_page: Page, settings: Settings
) -> None:
    page = IntegrationPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    key_locator = client_admin_page.get_by_text(re.compile(r"(bh_live_[a-f0-9]{32}|key-[a-f0-9]+)"))
    expect(key_locator.first).to_be_visible(timeout=settings.expect_timeout)


# ---------- Org-positions ----------


@pytest.mark.positive
@allure.title("Org-positions: alert о 1С-only показан")
def test_org_positions_shows_1c_only_alert(
    client_admin_page: Page, settings: Settings
) -> None:
    page = OrgPositionsPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.alert_1c_only).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Org-positions: таблица колонок видна (даже если данных нет)")
def test_org_positions_table_columns_visible(
    client_admin_page: Page, settings: Settings
) -> None:
    page = OrgPositionsPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    for col in ["Название", "Отдел", "Должность", "Сотрудники", "Действия"]:
        expect(page.table.get_by_role("columnheader", name=col)).to_be_visible()
