import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.payslip_page import PayslipPage


@pytest.mark.positive
@allure.title("/payslip: empty payslip placeholder is visible")
def test_payslip_empty_state(client_admin_page: Page, settings: Settings) -> None:
    page = PayslipPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(page.placeholder).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.skip(reason="BUG-019: GET /hr/payslips/latest returns 500 on empty data")
@pytest.mark.regression
def test_payslip_page_does_not_crash_on_backend_500() -> None:
    """Sentinel BUG-019: UI should not crash when latest endpoint returns 500."""
