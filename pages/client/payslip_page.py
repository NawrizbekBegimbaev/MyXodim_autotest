from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class PayslipPage(BasePage):
    """Payslips page. Current dev UI is an empty/placeholder state."""

    URL_PATH = "/payslip"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.payslip.title"), level=6
        )
        self._empty: Locator = page.get_by_text(t("client.payslip.empty"), exact=True)
        self._placeholder: Locator = page.get_by_text(
            t("client.payslip.placeholder"), exact=True
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def empty(self) -> Locator:
        return self._empty

    @property
    def placeholder(self) -> Locator:
        return self._placeholder
