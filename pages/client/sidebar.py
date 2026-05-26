from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t

ADMIN_NAV: tuple[tuple[str, str | None, str, str], ...] = (
    ("Рабочее место", None, t("client.sidebar.link_home"), "/home"),
    ("Мой кабинет", None, t("client.sidebar.subgroup_my_cabinet"), ""),
    ("Документооборот", None, t("client.sidebar.subgroup_docflow"), ""),
    ("Документооборот", None, "Согласование", ""),
    ("Администрирование", None, "Компания", "/organization"),
    ("Администрирование", None, t("client.sidebar.link_members"), "/members"),
)

SECTION_NAMES: tuple[str, ...] = (
    t("client.sidebar.section_workspace"),
    t("client.sidebar.section_documents"),
    t("client.sidebar.section_dictionaries"),
    t("client.sidebar.section_orgstructure"),
    t("client.sidebar.section_settings"),
)
SUBGROUP_NAMES: tuple[str, ...] = (
    t("client.sidebar.subgroup_my_cabinet"),
    t("client.sidebar.subgroup_docflow"),
    t("client.sidebar.subgroup_orgstructure"),
    t("client.sidebar.subgroup_settings"),
)

# Backward-compatible alias for older tests during migration.
GROUP_NAMES = SUBGROUP_NAMES


class ClientSidebar:
    def __init__(self, page: Page) -> None:
        self.page = page
        self._nav: Locator = page.get_by_role("navigation").first
        self._lang_button: Locator = page.get_by_role(
            "button", name="Switch language to O'zbekcha"
        )
        self._theme_button: Locator = page.get_by_role("button", name="Toggle theme")
        self._user_menu_trigger: Locator = page.get_by_role("button", name="User menu")

    @property
    def nav(self) -> Locator:
        return self._nav

    def link(self, label: str) -> Locator:
        return self._nav.get_by_role("link", name=label, exact=True).or_(
            self._nav.get_by_role("button", name=label, exact=True)
        ).first

    def section_header(self, name: str) -> Locator:
        aria_button = self._nav.locator(f'[role="button"][aria-label="{name}"]').first
        role_button = self._nav.get_by_role("button", name=name, exact=True).first
        return aria_button.or_(role_button).first

    def subgroup_button(self, name: str) -> Locator:
        aria_button = self._nav.locator(f'button[aria-label="{name}"]').first
        role_button = self._nav.get_by_role("button", name=name, exact=True).first
        return aria_button.or_(role_button).first

    def group_button(self, name: str) -> Locator:
        return self.subgroup_button(name)

    def expand_subgroup(self, name: str) -> Self:
        btn = self.subgroup_button(name)
        if btn.count() == 0:
            return self
        expanded = btn.get_attribute("aria-expanded")
        if expanded != "true":
            btn.scroll_into_view_if_needed()
            btn.click()
        return self

    def expand_group(self, name: str) -> Self:
        return self.expand_subgroup(name)

    def expand_all_subgroups(self) -> Self:
        for name in SECTION_NAMES:
            self.expand_subgroup(name)
        for name in SUBGROUP_NAMES:
            self.expand_subgroup(name)
        return self

    def expand_all(self) -> Self:
        return self.expand_all_subgroups()

    @property
    def user_menu_trigger(self) -> Locator:
        return self._user_menu_trigger

    def open_user_menu(self) -> Self:
        self._user_menu_trigger.click()
        return self

    def menu_item(self, name: str) -> Locator:
        return self.page.get_by_role("menuitem", name=name, exact=True)

    def click_settings(self) -> Self:
        self.menu_item(t("client.sidebar.user_menu_settings")).click()
        return self

    def click_logout(self) -> Self:
        self.menu_item(t("client.sidebar.user_menu_logout")).click()
        return self

    @property
    def lang_button(self) -> Locator:
        return self._lang_button

    @property
    def theme_button(self) -> Locator:
        return self._theme_button
