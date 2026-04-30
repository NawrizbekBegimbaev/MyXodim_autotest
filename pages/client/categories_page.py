from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class CategoriesPage(BasePage):
    """Категории документов в Client UI (/categories) — tree-view."""

    URL_PATH = "/categories"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.categories.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.categories.add_button")
        )
        self._tree_heading: Locator = page.get_by_role(
            "heading", name=t("client.categories.tree_heading"), level=6
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def tree_heading(self) -> Locator:
        return self._tree_heading

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def category_node(self, title: str) -> Locator:
        """Узел категории по названию (отображается в карточке + дереве, берём first)."""
        return self.page.get_by_text(title, exact=True).first


class CategoryCreateDialog(BasePage):
    """Модалка 'Добавить категорию' — Название + (опц.) Родительская категория."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.categories.create_dialog_title")
        )
        self._title_input: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.categories.field_title")
        )
        self._parent_combo: Locator = self._dialog.get_by_role(
            "combobox", name=t("client.categories.field_parent")
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.categories.create_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.categories.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def fill_title(self, title: str) -> Self:
        self._title_input.fill(title)
        return self

    def select_parent(self, parent_title: str) -> Self:
        """MUI Select: click → option из listbox."""
        self._parent_combo.click()
        self.page.get_by_role("listbox").get_by_role(
            "option", name=parent_title, exact=True
        ).click()
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
