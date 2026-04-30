"""Search variants для /tenants — case insensitive, по разным полям."""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import BrowserContext, Dialog, expect

from config.settings import Settings
from pages.admin.organizations_page import OrganizationsPage


def _open_list(ctx: BrowserContext, settings: Settings) -> OrganizationsPage:
    page = ctx.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    page.wait_for_timeout(1_000)
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    page.wait_for_timeout(2_500)
    orgs = OrganizationsPage(page)
    expect(orgs.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(orgs.table.get_by_role("row").nth(1)).to_be_visible(timeout=settings.nav_timeout)
    return orgs


@pytest.mark.positive
@allure.title("UC-4.2 search by name (а не slug)")
def test_search_by_name(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    anchor_company: dict[str, str],
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    # Используем уникальный 6-hex-suffix из имени (anchor name = "[E2E anchor] {suffix}")
    suffix = anchor_company["name"].split()[-1]
    orgs.search(suffix)
    expect(orgs.row_by_name(anchor_company["name"])).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("UC-4.2 search by INN")
def test_search_by_inn(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    anchor_company: dict[str, str],
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    orgs.search(anchor_company["inn"])
    expect(orgs.row_by_name(anchor_company["name"])).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("UC-4.2 search case-insensitive по slug (UPPER)")
def test_search_case_insensitive(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    anchor_company: dict[str, str],
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    orgs.search(anchor_company["slug"].upper())
    expect(orgs.row_by_name(anchor_company["name"])).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("UC-4.2 search trim whitespace в query")
def test_search_with_leading_trailing_spaces(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    anchor_company: dict[str, str],
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    orgs.search(f"  {anchor_company['slug']}  ")
    expect(orgs.row_by_name(anchor_company["name"])).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.negative
@allure.title("UC-4.2 search не существующая строка → empty-state")
def test_search_no_match_for_nonexistent_query(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    orgs.search("__not_exist_xyz_qwerty_98765__")
    expect(orgs.empty_state()).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.negative
@pytest.mark.parametrize(
    "query",
    [
        pytest.param("<script>alert(1)</script>", id="xss-payload"),
        pytest.param("'; DROP TABLE tenants; --", id="sqli-payload"),
    ],
)
@allure.title("UC-4.2 search: payload '{query}' не выполняется")
def test_search_special_payload_does_not_execute(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    query: str,
) -> None:
    """Фронт может либо escape'ить, либо отбрасывать спецсимволы — оба варианта
    приемлемы, главное чтобы payload не выполнился (нет dialog).
    """
    orgs = _open_list(super_admin_live_context, settings)
    page = orgs.page
    dialog_seen: list[str] = []

    def on_dialog(d: Dialog) -> None:
        dialog_seen.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)

    orgs.search(query)
    page.wait_for_timeout(1_500)
    assert dialog_seen == [], f"XSS/SQL payload вызвал dialog: {dialog_seen}"
