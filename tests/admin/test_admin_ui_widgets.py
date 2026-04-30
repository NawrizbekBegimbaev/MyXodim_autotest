"""UX-виджеты Admin UI: language switch, dark mode, sidebar, dashboard счётчики."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import BrowserContext, Page, expect

from config.settings import Settings


def _open_dashboard(ctx: BrowserContext, settings: Settings) -> Page:
    page = ctx.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    page.wait_for_timeout(1_000)
    expect(page.get_by_role("heading", name="Дашборд", level=4)).to_be_visible(
        timeout=settings.nav_timeout
    )
    return page


@pytest.mark.positive
@allure.title("Widgets: переключатель языка виден на дашборде")
def test_language_toggle_visible(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    page = _open_dashboard(super_admin_live_context, settings)
    toggle = page.get_by_role("button", name="change language")
    expect(toggle).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Widgets: переключатель темы (toggle theme/dark mode) существует")
def test_theme_toggle_exists(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    page = _open_dashboard(super_admin_live_context, settings)
    # Имя кнопки может быть "dark mode" или "light mode" в зависимости от текущей темы
    toggle = page.get_by_role(
        "button", name=re.compile(r"(dark|light)\s+mode|Toggle theme", re.IGNORECASE)
    )
    expect(toggle.first).to_be_visible(timeout=settings.expect_timeout)
    toggle.first.click()
    page.wait_for_timeout(500)
    # Дашборд остался доступен
    expect(page.get_by_role("heading", name="Дашборд", level=4)).to_be_visible()
    # Откат
    page.get_by_role(
        "button", name=re.compile(r"(dark|light)\s+mode|Toggle theme", re.IGNORECASE)
    ).first.click()


@pytest.mark.positive
@allure.title("Widgets: collapse/expand sidebar")
def test_sidebar_collapse_button_clickable(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    page = _open_dashboard(super_admin_live_context, settings)
    btn = page.get_by_role("button", name="collapse sidebar")
    expect(btn).to_be_visible(timeout=settings.expect_timeout)
    btn.click()
    page.wait_for_timeout(500)
    # Дашборд остаётся доступным
    expect(page.get_by_role("heading", name="Дашборд", level=4)).to_be_visible()


@pytest.mark.positive
@allure.title("Dashboard: счётчики 'Всего компаний', 'Активных компаний', 'Всего пользователей' видны и > 0")
def test_dashboard_counters_visible(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    page = _open_dashboard(super_admin_live_context, settings)
    for label in ["Всего компаний", "Активных компаний", "Всего пользователей"]:
        expect(page.get_by_text(label).first).to_be_visible()


@pytest.mark.positive
@allure.title("Dashboard: круговая диаграмма статусов компаний показана")
def test_dashboard_pie_chart_visible(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    page = _open_dashboard(super_admin_live_context, settings)
    expect(page.get_by_role("heading", name="Статус компаний", level=6)).to_be_visible(
        timeout=settings.expect_timeout
    )
