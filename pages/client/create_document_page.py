"""Client UI document create page (/documents/create).

- Pick a template ("Вид документа").
- Build a one-step approval route (executor + action «Согласовать»).
- Submit for approval ("Отправить на согласование").
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class CreateDocumentPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.heading: Locator = page.get_by_role("heading", name="Создать новый документ")
        # MUI Autocomplete labelled "Вид документа" (target the combobox input,
        # not the listbox which shares the same accessible name).
        self.template_input: Locator = page.get_by_role("combobox", name="Вид документа")
        self.add_step_button: Locator = page.get_by_role("button", name="+ Добавить").first
        self.executor_input: Locator = page.get_by_role("combobox", name="Исполнитель")
        self.coordinate_action: Locator = page.get_by_role("button", name="Согласовать").first
        self.save_draft_button: Locator = page.get_by_role("button", name="Сохранить как черновик")
        # Submit lives in a sticky bar (outside <main>), found at page level.
        self.submit_button: Locator = page.get_by_role("button", name="Отправить на согласование")

    def open(self) -> CreateDocumentPage:
        self.goto(f"{self.base_url}/documents/create")
        return self

    def select_template(self, name: str) -> None:
        self.template_input.click()
        self.template_input.fill(name)
        self.page.get_by_role("option", name=name, exact=True).first.click()

    def add_approval_step(self, executor_name: str) -> None:
        """Add one route step: executor + action «Согласовать» (no signing).

        The step row re-renders while the template workflow resolves, so we wait
        for it to settle, set the executor first (which stabilises the row), then
        switch the action.
        """
        self.add_step_button.click()
        # Wait for the step row to render and settle.
        self.executor_input.wait_for(state="visible", timeout=15_000)
        self.executor_input.click()
        self.page.get_by_role("option", name=executor_name, exact=True).first.click()
        # Default action is «Подписать»; switch to «Согласовать» (no EIMZO).
        # Retry through transient re-render detachments.
        for _ in range(5):
            try:
                if self.coordinate_action.get_attribute("aria-pressed") == "true":
                    break
                self.coordinate_action.click(timeout=5_000)
                break
            except Exception:
                self.page.wait_for_timeout(700)

    def save_as_draft(self) -> None:
        self.save_draft_button.click()

    def submit_for_approval(self) -> None:
        self.submit_button.click()
