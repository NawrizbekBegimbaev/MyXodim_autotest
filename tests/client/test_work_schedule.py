import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.work_schedule_page import WorkSchedulePage


@pytest.mark.positive
@allure.title("/work-schedule: empty state is visible")
def test_work_schedule_empty_state(
    client_admin_page: Page, settings: Settings
) -> None:
    page = WorkSchedulePage(client_admin_page).goto(settings.client_url)
    expect(page.empty).to_be_visible(timeout=settings.nav_timeout)
