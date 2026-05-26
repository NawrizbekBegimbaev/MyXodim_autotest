import re

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


@pytest.mark.smoke
@pytest.mark.positive
@allure.title("BRD 3.0 /home: payslip widget navigates to /payslip")
def test_home_widgets_navigation_to_payslip(
    client_admin_page: Page, settings: Settings
) -> None:
    home = HomePage(client_admin_page).goto(settings.client_url)
    home.goto_payslip()
    expect(client_admin_page).to_have_url(re.compile(r"/payslip$"))


@pytest.mark.positive
@allure.title("BRD 3.0 /home: vacation widget navigates to /vacation")
def test_home_widgets_navigation_to_vacation(
    client_admin_page: Page, settings: Settings
) -> None:
    home = HomePage(client_admin_page).goto(settings.client_url)
    home.goto_vacation()
    expect(client_admin_page).to_have_url(re.compile(r"/vacation$"))


@pytest.mark.positive
@allure.title("BRD 3.0 /home: schedule widget navigates to /work-schedule")
def test_home_widgets_navigation_to_schedule(
    client_admin_page: Page, settings: Settings
) -> None:
    home = HomePage(client_admin_page).goto(settings.client_url)
    home.goto_schedule()
    expect(client_admin_page).to_have_url(re.compile(r"/work-schedule$"))


@pytest.mark.positive
@allure.title("BRD 3.0 /home: My documents widget has 4 status counters")
def test_home_my_documents_widget_has_4_status_counters(
    client_admin_page: Page, settings: Settings
) -> None:
    home = HomePage(client_admin_page).goto(settings.client_url)
    expect(home.my_docs_in_work).to_be_visible()
    expect(home.my_docs_pending).to_be_visible()
    expect(home.my_docs_completed).to_be_visible()
    expect(home.my_docs_rejected).to_be_visible()


@pytest.mark.positive
@allure.title("BRD 3.0 /home: My tasks widget has 3 status counters")
def test_home_my_tasks_widget_has_3_status_counters(
    client_admin_page: Page, settings: Settings
) -> None:
    home = HomePage(client_admin_page).goto(settings.client_url)
    expect(home.my_tasks_pending).to_be_visible()
    expect(home.my_tasks_approved).to_be_visible()
    expect(home.my_tasks_rejected).to_be_visible()
