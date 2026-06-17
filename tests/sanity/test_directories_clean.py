"""Sanity case 6 — a fresh company's directories are clean before 1C import."""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.client.app_page import ClientAppPage

pytestmark = [pytest.mark.sanity, pytest.mark.client]

# Empty-state texts verified on a fresh [SANITY] company.
EMPTY = [
    ("/positions", "Должности не найдены"),
    ("/departments", "Подразделения не найдены"),
    ("/org-positions", "Позиции не найдены"),
    ("/routes", "Шаблоны маршрутов не найдены"),
]


@allure.title("6. Проверка до интеграции — справочники чистые")
@allure.description(
    "**Цель:** до интеграции с 1С справочники только что созданной компании пусты.\n\n"
    "**Окружение:** stage, Client UI. **Предусловие:** вход как админ свежей "
    "[SANITY]-компании (данные из 1С ещё не загружены).\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Войти как Администратор новой компании.\n"
    "2. Поочерёдно открыть `/positions`, `/departments`, `/org-positions`, `/routes`.\n"
    "3. На каждой странице проверить сообщение о пустом списке.\n\n"
    "**Ожидаемый результат:** все справочники показывают «… не найдены» (пусто)."
)
def test_directories_are_clean(admin_client_page: Page, cfg) -> None:
    app = ClientAppPage(admin_client_page, cfg.client_url)
    for route, empty_text in EMPTY:
        with allure.step(f"{route} пуст: «{empty_text}»"):
            app.open(route)
            expect(admin_client_page.get_by_text(empty_text)).to_be_visible()
