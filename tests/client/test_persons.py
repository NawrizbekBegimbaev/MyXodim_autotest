import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.person_create_dialog import PersonCreateDialog
from pages.client.persons_page import PersonsPage


@pytest.mark.positive
@allure.title("/persons: heading, columns, search and add dialog")
def test_persons_page_layout_and_add_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    page = PersonsPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.add_button).to_be_visible(timeout=settings.expect_timeout)
    expect(page.search).to_be_visible()
    for col in PersonsPage.COLUMNS:
        expect(page.column_header(col)).to_be_visible()

    page.click_add()
    dialog = PersonCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
