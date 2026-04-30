from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class TemplatesPage(BasePage):
    URL_PATH = "/templates"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.templates.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.templates.add_button")
        )

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    def click_add(self) -> Self:
        self._add_button.click()
        return self


class TemplateCreateDialog(BasePage):
    """Шаг 1 двухэтапного создания шаблона. После submit фронт открывает
    окно загрузки PDF (не тестируется здесь).
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.templates.create_dialog_title")
        )
        self._title_input: Locator = self._dialog.get_by_role(
            "textbox", name=t("client.templates.field_title")
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.templates.create_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.templates.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def fill_title(self, title: str) -> Self:
        self._title_input.fill(title)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self


class TemplateUploadDialog(BasePage):
    """Step 2: диалог 'Загрузка PDF' (открывается после Create в step 1)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.templates.upload_dialog_title")
        )
        self._skip: Locator = self._dialog.get_by_role(
            "button", name=t("client.templates.upload_skip"), exact=True
        )
        self._finish: Locator = self._dialog.get_by_role(
            "button", name=t("client.templates.upload_finish"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    @property
    def skip_button(self) -> Locator:
        return self._skip

    @property
    def finish_button(self) -> Locator:
        return self._finish

    def click_skip(self) -> Self:
        self._skip.click()
        return self

    def upload_file(self, file_path: str) -> Self:
        file_input = self._dialog.locator("input[type='file']")
        file_input.set_input_files(file_path)
        return self
