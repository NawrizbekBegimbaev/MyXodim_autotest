from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class DocumentsPage(BasePage):
    URL_PATH = "/documents"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.documents.title"), level=4
        )
        self._create_button: Locator = page.get_by_role(
            "button", name=t("client.documents.create_button")
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def create_button(self) -> Locator:
        return self._create_button

    def click_create(self) -> Self:
        self._create_button.click()
        return self


class DocumentCreateWizardPage(BasePage):
    """Шаги: Содержимое → Маршрут → Проверка. POM покрывает только step 1."""

    URL_PATH = "/documents/create"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.documents.create_page_title"), level=4
        )
        self._back_button: Locator = page.get_by_role(
            "button", name=t("client.documents.create_back"), exact=True
        )
        self._tab_template: Locator = page.get_by_role(
            "button", name=t("client.documents.tab_template"), exact=True
        )
        self._tab_freeform: Locator = page.get_by_role(
            "button", name=t("client.documents.tab_freeform"), exact=True
        )
        self._next_button: Locator = page.get_by_role(
            "button", name=t("client.documents.next_button"), exact=True
        )
        self._cancel_button: Locator = page.get_by_role(
            "button", name=t("client.documents.cancel_button"), exact=True
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def back_button(self) -> Locator:
        return self._back_button

    @property
    def tab_template(self) -> Locator:
        return self._tab_template

    @property
    def tab_freeform(self) -> Locator:
        return self._tab_freeform

    @property
    def next_button(self) -> Locator:
        return self._next_button

    @property
    def cancel_button(self) -> Locator:
        return self._cancel_button

    def select_first_template(self) -> Self:
        """Выбирает первый шаблон из списка (для wizard step 1)."""
        # Шаблоны — это <button> с heading[level=6]
        first_template = self.page.get_by_role("button").filter(
            has=self.page.get_by_role("heading", level=6)
        ).filter(has_text="INTERNAL").first
        first_template.click()
        return self

    def fill_title(self, title: str) -> Self:
        self.page.get_by_role(
            "textbox", name=t("client.documents.field_title")
        ).fill(title)
        return self

    def fill_content(self, content: str) -> Self:
        self.page.get_by_role(
            "textbox", name=t("client.documents.field_content")
        ).fill(content)
        return self

    def click_next(self) -> Self:
        self._next_button.click()
        return self

    # --- Step 2: Маршрут ---

    def select_route(self, label: str | None = None) -> Self:
        """Открывает combobox 'Маршрут' и выбирает первую non-placeholder
        опцию (если label не указан) или option с указанным текстом.
        """
        self.page.get_by_role("combobox", name=t("client.documents.field_route")).click()
        self.page.wait_for_timeout(400)
        if label is None:
            opts = self.page.get_by_role("option").all()
            non_placeholder = [
                o for o in opts if "Выберите" not in (o.text_content() or "")
            ]
            if not non_placeholder:
                raise RuntimeError("No active routes available")
            non_placeholder[0].click()
        else:
            self.page.get_by_role("option", name=label).first.click()
        self.page.wait_for_timeout(300)
        return self

    def select_target_branch_first(self) -> Self:
        """Выбирает первый branch в комбобоксе 'Целевой филиал'.

        UI: вторым combobox идёт филиал (без accessible name).
        """
        cbs = self.page.get_by_role("combobox").all()
        cbs[-1].click()
        self.page.wait_for_timeout(400)
        opts = self.page.get_by_role("option").all()
        non_placeholder = [
            o for o in opts if "Выберите" not in (o.text_content() or "")
        ]
        if not non_placeholder:
            raise RuntimeError("No branches available")
        non_placeholder[0].click()
        self.page.wait_for_timeout(300)
        return self

    # --- Step 3: Проверка ---

    @property
    def review_heading(self) -> Locator:
        return self.page.get_by_role(
            "heading", name=t("client.documents.review_heading"), level=6
        )

    @property
    def save_draft_button(self) -> Locator:
        return self.page.get_by_role(
            "button", name=t("client.documents.save_draft"), exact=True
        )

    @property
    def submit_route_button(self) -> Locator:
        return self.page.get_by_role(
            "button", name=t("client.documents.submit_route"), exact=True
        )

    def click_save_draft(self) -> Self:
        self.save_draft_button.click()
        return self

    def click_submit_route(self) -> Self:
        self.submit_route_button.click()
        return self
