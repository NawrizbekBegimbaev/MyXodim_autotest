import re
from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class OrganizationsPage(BasePage):
    """Список организаций (в UI — "Компании") в Admin UI."""

    URL_PATH = "/tenants"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role("heading", name="Компании", level=4)
        self._create_button: Locator = page.get_by_role("button", name=t("org.create_button"))
        self._search: Locator = page.get_by_role("textbox", name="Поиск...")
        # main-обёртка иногда не находится (race условие при init), используем напрямую
        self._table: Locator = page.get_by_role("table").last

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def create_button(self) -> Locator:
        return self._create_button

    @property
    def table(self) -> Locator:
        return self._table

    def click_create(self) -> Self:
        self._create_button.click()
        return self

    def search(self, query: str) -> Self:
        """Фильтр через UI. С 2026-05-03 (BUG-007 fixed) поиск идёт через
        бэк по query-параметру `search=`, не client-side."""
        self._search.fill(query)
        return self

    def goto_with_search(self, base_url: str, query: str) -> Self:
        """Применить фильтр через URL query (без UI-debounce — стабильнее в тестах)."""
        self.page.goto(f"{base_url.rstrip('/')}{self.URL_PATH}?search={query}")
        self.wait_loaded()
        return self

    def row_by_name(self, name: str) -> Locator:
        return self._table.get_by_role("row").filter(has_text=name)

    def organization_status(self, name: str) -> Locator:
        return self.row_by_name(name).get_by_text(t("org.status_active"))

    def total_companies_text(self) -> Locator:
        # paragraph вида "10 компаний" / "1 компания" — счётчик под heading
        return self.page.get_by_text(re.compile(r"\d+\s+компани"))

    def empty_state(self) -> Locator:
        return self.page.get_by_text("Компании не найдены")

    def disable_toggle_for(self, name: str) -> Locator:
        """MUI Switch с aria-label="Отключить" в строке активной компании.

        Внутри это `<input role="switch">` обёрнутый в span с aria-label.
        Playwright `get_by_label` находит по этой aria-label."""
        return self.row_by_name(name).get_by_label("Отключить", exact=True)

    def enable_toggle_for(self, name: str) -> Locator:
        """MUI Switch с aria-label="Включить" в строке отключённой компании."""
        return self.row_by_name(name).get_by_label("Включить", exact=True)

    def toggle_subscription_for(self, name: str) -> Self:
        """Кликает MUI Switch (Отключить/Включить) в строке.

        aria-label на span-обёртке Switch'а указывает что произойдёт при
        клике: "Отключить" если активна, "Включить" если отключена.
        """
        row = self.row_by_name(name)
        toggle = row.get_by_label(re.compile(r"^(Отключить|Включить)$"))
        with self.page.expect_response(
            lambda r: (
                "/api/v1/admin/tenants/" in r.url
                and r.request.method == "POST"
                and (r.url.endswith("/enable") or r.url.endswith("/disable"))
            ),
            timeout=15_000,
        ):
            toggle.click()
        return self
