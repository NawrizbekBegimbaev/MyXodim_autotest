import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.vacation_page import VacationPage


@pytest.mark.positive
@allure.title("/vacation: empty state is visible")
def test_vacation_empty_state(client_admin_page: Page, settings: Settings) -> None:
    page = VacationPage(client_admin_page).goto(settings.client_url)
    expect(page.empty).to_be_visible(timeout=settings.nav_timeout)
