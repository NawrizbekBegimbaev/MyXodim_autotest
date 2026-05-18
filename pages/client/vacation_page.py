from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class VacationPage(BasePage):
    """Vacation page. Current dev UI shows an empty state."""

    URL_PATH = "/vacation"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._empty: Locator = page.get_by_text(t("client.vacation.empty"), exact=True)

    @property
    def empty(self) -> Locator:
        return self._empty
