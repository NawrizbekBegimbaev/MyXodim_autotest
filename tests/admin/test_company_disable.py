"""UC-4.3: Включение / отключение компании в Admin UI.

BRD §4.3. В UI колонка "Действия" — switch (toggle): checked=Активна,
unchecked=Отключена. API: POST /api/v1/admin/tenants/{id}/{enable|disable}.
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import BrowserContext, expect

from config.settings import Settings
from pages.admin.organizations_page import OrganizationsPage


def _open_list(ctx: BrowserContext, settings: Settings) -> OrganizationsPage:
    page = ctx.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    page.wait_for_timeout(1_500)
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    page.wait_for_timeout(2_500)
    orgs = OrganizationsPage(page)
    expect(orgs.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(orgs.table.get_by_role("row").nth(1)).to_be_visible(timeout=settings.nav_timeout)
    return orgs


@pytest.mark.positive
@allure.title("UC-4.3: отключить активную компанию → статус 'Отключена'")
def test_disable_active_company_changes_status_to_disabled(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    disable_target_company: dict[str, str],
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    name = disable_target_company["name"]

    with allure.step("Находим компанию и фильтруем по slug"):
        orgs.search(disable_target_company["slug"])
        expect(orgs.row_by_name(name)).to_be_visible(timeout=settings.nav_timeout)

    with allure.step("Кликаем switch — disable"):
        orgs.toggle_subscription_for(name)

    with allure.step("Статус компании = 'Отключена'"):
        row = orgs.row_by_name(name)
        expect(row).to_contain_text("Отключена", timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("UC-4.3: включить отключённую компанию → статус 'Активна'")
def test_enable_disabled_company_changes_status_to_active(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    disable_target_company: dict[str, str],
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    name = disable_target_company["name"]

    with allure.step("Находим компанию"):
        orgs.search(disable_target_company["slug"])
        expect(orgs.row_by_name(name)).to_be_visible(timeout=settings.nav_timeout)

    # Если предыдущий тест отключил — этот клик включит. Если не отключил — отключит.
    # Идемпотентность недостижима через UI без проверки состояния, поэтому
    # тест-провайдер сам должен гарантировать порядок (см. xfail-reason).
    with allure.step("Кликаем switch (toggle обратно)"):
        orgs.toggle_subscription_for(name)

    with allure.step("Статус компании = 'Активна'"):
        row = orgs.row_by_name(name)
        expect(row).to_contain_text("Активна", timeout=settings.nav_timeout)
