import re

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class HomePage(BasePage):
    """Client UI workspace landing at /home."""

    URL_PATH = "/home"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._greeting: Locator = page.get_by_role("heading", level=1)
        self._widget_payslip: Locator = page.get_by_role(
            "button", name=re.compile(rf"^{re.escape(t('client.home.widget_payslip'))}")
        ).first
        self._widget_vacation: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_vacation"), level=6
        )
        self._widget_schedule: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_schedule"), level=6
        )
        self._widget_my_docs: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_my_docs"), level=6
        )
        self._widget_my_tasks: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_my_tasks"), level=6
        )

    @property
    def greeting(self) -> Locator:
        return self._greeting

    @property
    def widget_payslip(self) -> Locator:
        return self._widget_payslip

    @property
    def widget_vacation(self) -> Locator:
        return self._widget_vacation

    @property
    def widget_schedule(self) -> Locator:
        return self._widget_schedule

    @property
    def widget_my_docs(self) -> Locator:
        return self._widget_my_docs

    @property
    def widget_my_tasks(self) -> Locator:
        return self._widget_my_tasks
