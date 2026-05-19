"""Inbox + Организация + Интеграция + Штатные позиции — view-only страницы.

Обновлено 2026-05-18 после редизайна:
- /organization: табы "Данные"/"Филиалы", без секции Интеграция
- /integration: hub с карточками провайдеров (1C/Bitrix24/Налоговая)
- /org-positions: создание только через 1C, есть 1C-only alert
"""

from __future__ import annotations

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
@allure.title("Inbox: открывается, показан heading, toolbar и columns")
def test_inbox_page_opens(
    client_admin_page: Page, settings: Settings
) -> None:
    page = InboxPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.search_input).to_be_visible(timeout=settings.expect_timeout)
    expect(page.history_button).to_be_visible()
    for column in InboxPage.COLUMNS:
        expect(page.column_header(column)).to_be_visible()


@pytest.mark.positive
@allure.title("Inbox: date range fields accept input")
def test_inbox_date_range_fields_accept_input(
    client_admin_page: Page, settings: Settings
) -> None:
    page = InboxPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    page.fill_date_range("2026-05-01", "2026-05-18")
    expect(page.heading).to_be_visible()


# ---------- Organization ----------


@pytest.mark.positive
@allure.title("Organization: heading + секция 'Основные данные'")
def test_organization_page_shows_heading_and_basic_section(
    client_admin_page: Page, settings: Settings
) -> None:
    page = OrganizationPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.section_basic).to_be_visible()


@pytest.mark.positive
@allure.title("Organization: 2 таба — 'Данные' (selected) и 'Филиалы'")
def test_organization_has_data_and_branches_tabs(
    client_admin_page: Page, settings: Settings
) -> None:
    page = OrganizationPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    for name in OrganizationPage.TABS:
        expect(page.tab(name)).to_be_visible(timeout=settings.expect_timeout)
    expect(page.tab("Данные")).to_have_attribute("aria-selected", "true")


# ---------- Integration ----------


@pytest.mark.positive
@allure.title("Integration: hub-страница с heading 'Интеграция'")
def test_integration_page_renders_as_hub(
    client_admin_page: Page, settings: Settings
) -> None:
    page = IntegrationPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("Integration: карточка 1C активна с кнопкой 'Настроить'")
def test_integration_1c_card_has_configure_button(
    client_admin_page: Page, settings: Settings
) -> None:
    page = IntegrationPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.provider_card("1C")).to_be_visible()
    expect(page.configure_button_for("1C")).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.positive
@allure.title("Integration: hub имеет 3 фильтр-таба (Все/Подключено/Не подключено)")
def test_integration_hub_has_filter_tabs(
    client_admin_page: Page, settings: Settings
) -> None:
    page = IntegrationPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    for tab in ("Все", "Подключено", "Не подключено"):
        expect(page.tablist.get_by_role("tab", name=tab, exact=True)).to_be_visible()


# ---------- Org-positions ----------


@pytest.mark.positive
@pytest.mark.xfail(reason="Current /org-positions UI has no 1C-only alert", strict=False)
@allure.title("Org-positions: ручное создание заблокировано — есть 1C-only alert")
def test_org_positions_has_1c_only_alert(
    client_admin_page: Page, settings: Settings
) -> None:
    page = OrgPositionsPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.alert_1c_only).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Org-positions: 2 view-tab'а (Список/Иерархия)")
def test_org_positions_has_view_tabs(
    client_admin_page: Page, settings: Settings
) -> None:
    page = OrgPositionsPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    for name in OrgPositionsPage.VIEW_TABS:
        expect(page.view_tab(name)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Org-positions: все 6 колонок таблицы видны")
@pytest.mark.parametrize("col_name", OrgPositionsPage.COLUMNS)
def test_org_positions_table_columns_visible(
    client_admin_page: Page, settings: Settings, col_name: str
) -> None:
    page = OrgPositionsPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.column_header(col_name)).to_be_visible(
        timeout=settings.expect_timeout
    )
