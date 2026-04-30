from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class OrganizationPage(BasePage):
    URL_PATH = "/organization"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.organization.title"), level=4
        )
        self._section_basic: Locator = page.get_by_role(
            "heading", name=t("client.organization.section_basic"), level=6
        )
        self._section_integration: Locator = page.get_by_role(
            "heading", name=t("client.organization.section_integration"), level=6
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def section_basic(self) -> Locator:
        return self._section_basic

    @property
    def section_integration(self) -> Locator:
        return self._section_integration

    def integration_key_value(self) -> Locator:
        # Ключ — это <code> элемент рядом с label "Ключ интеграции 1С"
        return self.page.locator("code").last


class IntegrationPage(BasePage):
    URL_PATH = "/integration"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.integration.title"), level=4
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    def integration_key_code(self) -> Locator:
        return self.page.locator("code").first


class OrgPositionsPage(BasePage):
    URL_PATH = "/org-positions"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.org_positions.title"), level=4
        )
        # alert на странице: "Создание позиций выполняется через интеграцию с 1С"
        self._alert_1c_only: Locator = page.get_by_role("alert").filter(
            has_text=t("client.org_positions.alert_1c_only")
        )
        self._table: Locator = page.get_by_role("table").last

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def alert_1c_only(self) -> Locator:
        return self._alert_1c_only

    @property
    def table(self) -> Locator:
        return self._table
