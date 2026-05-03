"""Inbox + Организация + Интеграция + Штатные позиции — view-only страницы.

Обновлено 2026-05-03 после редизайна:
- /organization: табы "Данные"/"Филиалы", без секции Интеграция
- /integration: hub с карточками провайдеров (1C/Bitrix24/Налоговая)
- /org-positions: ручное создание разрешено, без 1C-only alert,
  новая колонка "При вакантности"
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
    expect(page.heading).to_be_visible()
    page.status_tab("Все").click()
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
@allure.title("Org-positions: 2026-05-03 ручное создание разрешено — есть кнопка добавить")
def test_org_positions_has_add_button(
    client_admin_page: Page, settings: Settings
) -> None:
    """Раньше создание было 1C-only с alert'ом. Теперь — ручная кнопка."""
    page = OrgPositionsPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.add_button).to_be_visible(timeout=settings.expect_timeout)


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
