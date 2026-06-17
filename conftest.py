"""Shared fixtures for the MyXodim 29-case sanity suite.

Run model (mirrors the manual sanity walkthrough):
  1. Platform admin logs into Admin UI once (session).
  2. A fresh [SANITY] company + its admin are created via Admin UI (case 4).
     A fresh company gives naturally-clean directories (case 6).
  3. We log into Client UI once as that new admin (one OTP — staging rate-limits
     a phone to one OTP request / ~60s) and reuse the authenticated page for all
     client cases (5, 6, 8-29).
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect

from config.sanity_data import SanityTenantData
from config.settings import settings
from pages.admin.create_company_page import CreateCompanyPage, CreatedTenant
from pages.admin.login_page import AdminLoginPage
from pages.client.login_page import ClientLoginPage

expect.set_options(timeout=15_000)

CONTEXT_ARGS: dict = {
    "viewport": {"width": 1440, "height": 900},
    "locale": "ru-RU",
    "timezone_id": "Asia/Tashkent",
    "ignore_https_errors": True,
}


@pytest.fixture(scope="session")
def cfg():
    return settings


@pytest.fixture
def browser_context_args(browser_context_args: dict) -> dict:
    return {**browser_context_args, **CONTEXT_ARGS}


def _traced_context(browser: Browser, name: str) -> BrowserContext:
    ctx = browser.new_context(**CONTEXT_ARGS)
    ctx.tracing.start(screenshots=True, snapshots=True, sources=True, title=name)
    return ctx


def _save_trace(ctx: BrowserContext, name: str) -> None:
    os.makedirs("test-results", exist_ok=True)
    ctx.tracing.stop(path=f"test-results/{name}-trace.zip")
    ctx.close()


@pytest.fixture(scope="session")
def admin_page(browser: Browser) -> Iterator[Page]:
    """Admin UI logged in as the platform admin (session-scoped)."""
    ctx = _traced_context(browser, "admin")
    page = ctx.new_page()
    AdminLoginPage(page, settings.admin_url).login(settings.admin_phone, settings.admin_password)
    expect(page).to_have_url(_re(r"/dashboard"), timeout=30_000)
    yield page
    _save_trace(ctx, "admin")


@pytest.fixture(scope="session")
def sanity_tenant(admin_page: Page) -> CreatedTenant:
    """Create a fresh [SANITY] company + admin via Admin UI (case 4)."""
    data = SanityTenantData()
    create = CreateCompanyPage(admin_page, settings.admin_url).open()
    create.fill(data).submit()
    expect(create.success_marker).to_be_visible(timeout=30_000)
    return create.read_result(data)


@pytest.fixture(scope="session")
def admin_client_context(browser: Browser) -> Iterator[BrowserContext]:
    ctx = _traced_context(browser, "client-admin")
    yield ctx
    _save_trace(ctx, "client-admin")


@pytest.fixture(scope="session")
def admin_client_page(admin_client_context: BrowserContext, sanity_tenant: CreatedTenant) -> Page:
    """Client UI logged in as the freshly-created company admin (one OTP/run)."""
    page = admin_client_context.new_page()
    ClientLoginPage(page, settings.client_url).login(sanity_tenant.admin_phone, settings.test_otp)
    expect(page).to_have_url(_re(r"/home"), timeout=30_000)
    expect(page.get_by_role("heading", name="Добро пожаловать")).to_be_visible(timeout=30_000)
    return page


@pytest.fixture(scope="session")
def employee_client_context(browser: Browser) -> Iterator[BrowserContext]:
    ctx = _traced_context(browser, "client-employee")
    yield ctx
    _save_trace(ctx, "client-employee")


@pytest.fixture(scope="session")
def employee_client_page(employee_client_context: BrowserContext) -> Page:
    """Client UI logged in as a known EMPLOYEE-role user (restricted access)."""
    page = employee_client_context.new_page()
    ClientLoginPage(page, settings.client_url).login(
        settings.client_employee_phone, settings.test_otp
    )
    expect(page).to_have_url(_re(r"/home"), timeout=30_000)
    return page


def _re(pattern: str):
    import re

    return re.compile(pattern)
