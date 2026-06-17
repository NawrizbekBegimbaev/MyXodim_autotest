"""Mock 1C UI — connect by integration key and push reference data.

Mock 1C auto-generates a mock dataset (job titles «Инициатор/Кадровик/…»,
persons «Иванова Елена/…», employees). «Отправить все» pushes a whole entity
type to the connected company.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage

# Push routes in dependency order.
PUSH_ROUTES: dict[str, str] = {
    "Организации": "/organizations",
    "Подразделения": "/departments",
    "Должности": "/positions",
    "Физлица": "/persons",
    "Сотрудники": "/employees",
}


class Mock1cPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self.base_url = base_url
        self.key_input: Locator = page.get_by_placeholder("bh_live_...")
        self.save_button: Locator = page.get_by_role("button", name="Сохранить")
        self.connected_marker: Locator = page.get_by_text("Подключено").first
        self.push_all_button: Locator = page.get_by_role("button", name="Отправить все")

    def connect(self, key: str) -> Mock1cPage:
        self.goto(f"{self.base_url}/")
        self.key_input.fill(key)
        self.save_button.click()
        self.connected_marker.wait_for(state="visible", timeout=15_000)
        return self

    def push_all(self, route: str) -> None:
        self.goto(f"{self.base_url}{route}")
        self.push_all_button.wait_for(state="visible", timeout=15_000)
        self.push_all_button.click()
