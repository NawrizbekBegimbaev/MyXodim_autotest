from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class InboxPage(BasePage):
    URL_PATH = "/inbox"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.inbox.title"), level=4
        )
        self._search: Locator = page.get_by_role(
            "textbox", name=t("client.inbox.search_placeholder")
        )
        self._table: Locator = page.get_by_role("table").last

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def search_input(self) -> Locator:
        return self._search

    @property
    def table(self) -> Locator:
        return self._table

    def status_tab(self, name: str) -> Locator:
        return self.page.get_by_role("tab", name=name, exact=True)
