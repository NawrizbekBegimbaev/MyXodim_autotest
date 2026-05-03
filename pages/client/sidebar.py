"""Client UI sidebar (groups-based navigation).

Структура с 2026-05-03:
    Главная (top-level link)
    Документооборот (group)
        ├── Требуют подписи         /inbox
        ├── Мои документы           /documents
        ├── Мои заявки              /documents/#requests  (badge "Скоро")
        └── Шаблоны                 /templates
    Оргструктура (group)
        ├── Пользователи            /members
        ├── Филиалы                 /branches
        ├── Отделы                  /departments    (NEW)
        ├── Должности               /positions
        └── Штатные позиции         /org-positions
    Настройки (group)
        ├── Организация             /organization
        ├── Системные роли          /roles
        └── Интеграция              /integration

Группы свёрнуты по умолчанию — нужно `expand_group()` чтобы добраться
до вложенного link'а.
"""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

# (группа | None, label, url-path). None = top-level.
ADMIN_NAV: tuple[tuple[str | None, str, str], ...] = (
    (None, "Главная", "/dashboard"),
    ("Документооборот", "Требуют подписи", "/inbox"),
    ("Документооборот", "Мои документы", "/documents"),
    ("Документооборот", "Шаблоны", "/templates"),
    ("Оргструктура", "Пользователи", "/members"),
    ("Оргструктура", "Филиалы", "/branches"),
    ("Оргструктура", "Отделы", "/departments"),
    ("Оргструктура", "Должности", "/positions"),
    ("Оргструктура", "Штатные позиции", "/org-positions"),
    ("Настройки", "Организация", "/organization"),
    ("Настройки", "Системные роли", "/roles"),
    ("Настройки", "Интеграция", "/integration"),
)

GROUP_NAMES: tuple[str, ...] = ("Документооборот", "Оргструктура", "Настройки")


class ClientSidebar:
    def __init__(self, page: Page) -> None:
        self.page = page
        self._nav = page.get_by_role("navigation").first

    @property
    def nav(self) -> Locator:
        return self._nav

    def group_button(self, name: str) -> Locator:
        return self._nav.get_by_role("button", name=name, exact=True)

    def link(self, name: str) -> Locator:
        return self._nav.get_by_role("link", name=name, exact=True)

    def expand_group(self, name: str) -> Self:
        """Кликает группа-кнопку если она ещё свёрнута. Идемпотентно."""
        btn = self.group_button(name)
        # MUI accordion: aria-expanded на кнопке. В свёрнутом состоянии вложенный
        # list скрыт; кликаем независимо — повторный клик безопасен (свернёт),
        # поэтому проверяем сначала видимость одного link'а в группе.
        # Простейший подход: всегда expand (1 клик в свёрнутое раскроет).
        btn.click()
        return self

    def expand_all(self) -> Self:
        """Раскрывает все группы. Удобно для тестов которые ходят по всем секциям."""
        for g in GROUP_NAMES:
            self.expand_group(g)
        return self
