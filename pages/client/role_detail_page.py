from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class RoleDetailPage(BasePage):
    """Role detail/edit page at /roles/{uuid}."""

    GROUPS: tuple[str, ...] = (
        t("client.roles.group_docflow"),
        t("client.roles.group_hr"),
        t("client.roles.group_finance"),
        t("client.roles.group_settings"),
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.roles.detail.heading"), level=4
        )
        self._back_button: Locator = page.get_by_role(
            "button", name=t("client.roles.detail.back"), exact=True
        )
        self._save_button: Locator = page.get_by_role(
            "button", name=t("client.roles.detail.save"), exact=True
        )
        self._expand_all: Locator = page.get_by_role(
            "button", name=t("client.roles.detail.expand_all"), exact=True
        )
        self._collapse_all: Locator = page.get_by_role(
            "button", name=t("client.roles.detail.collapse_all"), exact=True
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def back_button(self) -> Locator:
        return self._back_button

    @property
    def save_button(self) -> Locator:
        return self._save_button

    @property
    def expand_all_button(self) -> Locator:
        return self._expand_all

    @property
    def collapse_all_button(self) -> Locator:
        return self._collapse_all

    def group_summary(self, name: str) -> Locator:
        return self.page.get_by_role("button", name=name).first

    def total_summary(self) -> Locator:
        return self.page.get_by_text("Права доступа", exact=False)
