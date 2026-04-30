"""Inbox actions — empty state + tabs (полный flow approve/reject требует
существующего документа в очереди и покрывается главным E2E)."""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.inbox_page import InboxPage


def _open_inbox(page: Page, settings: Settings) -> InboxPage:
    inbox = InboxPage(page).goto(settings.client_url)
    expect(inbox.heading).to_be_visible(timeout=settings.nav_timeout)
    return inbox


@pytest.mark.positive
@allure.title("Inbox: search не ломает страницу при пустом результате")
def test_inbox_search_no_match_does_not_crash(
    client_admin_page: Page, settings: Settings
) -> None:
    inbox = _open_inbox(client_admin_page, settings)
    inbox.search_input.fill("__no_such_doc_xyz_98765__")
    client_admin_page.wait_for_timeout(1_500)
    # heading и таблица всё ещё видны
    expect(inbox.heading).to_be_visible()


@pytest.mark.positive
@pytest.mark.parametrize(
    "tab",
    [
        pytest.param("Все", id="all"),
        pytest.param("Черновик", id="draft"),
        pytest.param("В работе", id="in-progress"),
        pytest.param("Завершён", id="completed"),
        pytest.param("Отклонён", id="rejected"),
        pytest.param("Отправлен в 1С", id="sent-to-1c"),
    ],
)
@allure.title("Inbox: переключение таба '{tab}' не ломает страницу")
def test_inbox_tab_switch_does_not_crash(
    client_admin_page: Page, settings: Settings, tab: str
) -> None:
    inbox = _open_inbox(client_admin_page, settings)
    inbox.status_tab(tab).click()
    client_admin_page.wait_for_timeout(800)
    expect(inbox.heading).to_be_visible()


@pytest.mark.positive
@allure.title("Inbox: search-input принимает ввод")
def test_inbox_search_input_accepts_text(
    client_admin_page: Page, settings: Settings
) -> None:
    inbox = _open_inbox(client_admin_page, settings)
    inbox.search_input.fill("test query")
    expect(inbox.search_input).to_have_value("test query")
    inbox.search_input.fill("")
    expect(inbox.search_input).to_have_value("")
