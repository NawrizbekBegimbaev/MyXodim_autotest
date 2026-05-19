import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.home_page import HomePage


@pytest.mark.positive
@allure.title("/home: greeting and workspace widgets are visible")
def test_home_page_widgets_visible(client_admin_page: Page, settings: Settings) -> None:
    page = HomePage(client_admin_page).goto(settings.client_url)
    expect(page.greeting).to_be_visible(timeout=settings.nav_timeout)
    expect(page.widget_payslip).to_be_visible(timeout=settings.expect_timeout)
    expect(page.widget_vacation).to_be_visible()
    expect(page.widget_schedule).to_be_visible()
    expect(page.widget_my_docs).to_be_visible()
    expect(page.widget_my_tasks).to_be_visible()
