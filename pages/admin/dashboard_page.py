from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class AdminDashboardPage(BasePage):
    """Главная Admin UI после логина (/dashboard)."""

    URL_PATH = "/dashboard"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._companies_nav_link: Locator = page.get_by_role(
            "link", name=t("nav.admin.companies")
        )
        self._add_company_button: Locator = page.get_by_role(
            "button", name=t("org.create_button")
        )
        self._logout_button: Locator = page.get_by_role("button", name=t("admin.logout"))

    @property
    def companies_link(self) -> Locator:
        return self._companies_nav_link

    @property
    def add_company_button(self) -> Locator:
        return self._add_company_button

    @property
    def logout_button(self) -> Locator:
        return self._logout_button
