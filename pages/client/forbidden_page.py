from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class ForbiddenPage(BasePage):
    """Client UI 403 page."""

    URL_PATH = "/forbidden"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.forbidden.title"), level=4
        )
        self._home_button: Locator = page.get_by_role(
            "button", name=t("client.forbidden.home_button"), exact=True
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def home_button(self) -> Locator:
        return self._home_button

    def message_for_section(self, section: str) -> Locator:
        return self.page.get_by_text(
            t("client.forbidden.message_template").format(section), exact=True
        )
