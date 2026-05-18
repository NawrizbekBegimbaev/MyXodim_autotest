from playwright.sync_api import Locator, Page

from data.i18n import t


class ClientBanner:
    """Top banner with breadcrumb and action buttons."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self._banner: Locator = page.get_by_role("banner").first
        self._help_button: Locator = self._banner.get_by_role(
            "button", name=t("client.banner.help")
        )
        self._notifications_button: Locator = self._banner.get_by_role(
            "button", name=t("client.banner.notifications")
        )
        self._settings_button: Locator = self._banner.get_by_role(
            "button", name=t("client.banner.settings")
        )

    @property
    def banner(self) -> Locator:
        return self._banner

    @property
    def help_button(self) -> Locator:
        return self._help_button

    @property
    def notifications_button(self) -> Locator:
        return self._notifications_button

    @property
    def settings_button(self) -> Locator:
        return self._settings_button

    def breadcrumb_section(self) -> Locator:
        return self._banner.locator("p").first

    def breadcrumb_page(self) -> Locator:
        return self._banner.locator("p").last
