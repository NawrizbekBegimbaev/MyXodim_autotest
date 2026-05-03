"""Маршруты /routes — минимальное покрытие (default config 1 шаг).

Полный конструктор шагов (drag&drop / add step) — отдельный пакет тестов
после стабилизации UI; пока тестируем что маршрут с дефолтным 1 шагом
сохраняется и виден в списке.
"""

from __future__ import annotations

import re
import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.routes_page import RouteEditorPage, RoutesPage


def _open(page: Page, settings: Settings) -> RoutesPage:
    rt = RoutesPage(page).goto(settings.client_url)
    expect(rt.heading).to_be_visible(timeout=settings.nav_timeout)
    return rt


def _fresh_name() -> str:
    return f"{E2E_PREFIX} Route {secrets.token_hex(3)}"


# Все тесты в файле мутируют состояние через UI (CRUD-формы).
pytestmark = pytest.mark.creates_data


@pytest.mark.positive
@allure.title("Routes: создание маршрута с дефолтным 1 шагом → виден в списке")
def test_route_create_with_default_step_appears_in_list(
    client_admin_page: Page, settings: Settings
) -> None:
    name = _fresh_name()
    rt = _open(client_admin_page, settings)
    rt.click_create()
    expect(client_admin_page).to_have_url(
        re.compile(r"/routes/new"), timeout=settings.nav_timeout
    )
    editor = RouteEditorPage(client_admin_page)
    expect(editor.save_button).to_be_visible(timeout=settings.nav_timeout)
    editor.fill_name(name).fill_description("Тестовое описание").save()
    client_admin_page.wait_for_timeout(3_000)
    # Возвращаемся в список и ищем
    rt = _open(client_admin_page, settings)
    rt.search(name)
    client_admin_page.wait_for_timeout(1_500)
    expect(rt.row_by_name(name)).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("Routes: страница списка имеет search и кнопку Создать")
def test_routes_list_has_create_and_search(
    client_admin_page: Page, settings: Settings
) -> None:
    rt = _open(client_admin_page, settings)
    expect(rt.create_button).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Routes: кнопка 'Назад' с editor возвращает на /routes")
def test_route_editor_back_button_returns_to_list(
    client_admin_page: Page, settings: Settings
) -> None:
    rt = _open(client_admin_page, settings)
    rt.click_create()
    editor = RouteEditorPage(client_admin_page)
    expect(editor.back_button).to_be_visible(timeout=settings.expect_timeout)
    editor.back_button.click()
    expect(client_admin_page).to_have_url(re.compile(r"/routes(\?|$)"), timeout=settings.nav_timeout)
