"""Client UI: разделы /organization, /integration, /org-positions.

Редизайн 2026-05-03:
- /organization — табы "Данные"/"Филиалы". Секция "Интеграция" убрана,
  ключ переехал в /integration → "Настроить" по карточке 1C.
- /integration — hub-страница со списком интеграций (1C/Bitrix24/Налоговая).
  Heading "Интеграция" (без "с 1С"). Ключ — за кликом "Настроить".
- /org-positions — теперь поддерживает РУЧНОЕ создание позиций
  (кнопка "+ Добавить позицию"). Alert "1C-only" убран. Новые табы
  "Список"/"Иерархия". Новая колонка "При вакантности".
"""

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class OrganizationPage(BasePage):
    URL_PATH = "/organization"

    # Tabs появились 2026-05-03 — view modes для оргданных
    TABS: tuple[str, ...] = ("Данные", "Филиалы")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.organization.title"), level=4
        )
        self._section_basic: Locator = page.get_by_role(
            "heading", name=t("client.organization.section_basic"), level=6
        )
        self._tablist: Locator = page.get_by_role("tablist").first

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def section_basic(self) -> Locator:
        return self._section_basic

    @property
    def tablist(self) -> Locator:
        return self._tablist

    def tab(self, name: str) -> Locator:
        return self._tablist.get_by_role("tab", name=name, exact=True)


class IntegrationPage(BasePage):
    """Hub-страница интеграций. Heading "Интеграция", карточки 1C/Bitrix24/Налоговая.

    Чтобы получить ключ интеграции 1С, нужно кликнуть "Настроить" на
    карточке 1C — открывается отдельная панель настройки.
    """

    URL_PATH = "/integration"
    PROVIDERS: tuple[str, ...] = ("1C", "Bitrix24", "Налоговая система")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name="Интеграция", level=4
        )
        self._tablist: Locator = page.get_by_role("tablist").first

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def tablist(self) -> Locator:
        return self._tablist

    def provider_card(self, name: str) -> Locator:
        return self.page.get_by_role("heading", name=name, level=6)

    def configure_button_for(self, name: str) -> Locator:
        """Кнопка "Настроить" в карточке провайдера."""
        # Карточка как DIV с heading и button. Берём ближайший button к heading.
        # Простой путь: ищем все button "Настроить" — для активных провайдеров
        # она единственная (Bitrix24/Налоговая помечены "Скоро" и не имеют кнопки).
        return self.page.get_by_role("button", name="Настроить", exact=True)


class OrgPositionsPage(BasePage):
    """Штатные позиции.

    С 2026-05-03 — поддерживает ручное создание (была 1C-only).
    Alert "Создание позиций выполняется через интеграцию с 1С" удалён.
    """

    URL_PATH = "/org-positions"

    COLUMNS: tuple[str, ...] = (
        "Название",
        "Отдел",
        "Должность",
        "Сотрудники",
        "При вакантности",
        "Действия",
    )

    VIEW_TABS: tuple[str, ...] = ("Список", "Иерархия")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.org_positions.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name="+ Добавить позицию"
        )
        self._search_input: Locator = page.get_by_role(
            "textbox", name="Поиск по названию…"
        )
        self._table: Locator = page.get_by_role("table").last
        self._tablist: Locator = page.get_by_role("tablist").first

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def add_button(self) -> Locator:
        return self._add_button

    @property
    def search_input(self) -> Locator:
        return self._search_input

    @property
    def table(self) -> Locator:
        return self._table

    @property
    def tablist(self) -> Locator:
        return self._tablist

    def view_tab(self, name: str) -> Locator:
        return self._tablist.get_by_role("tab", name=name, exact=True)

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)
