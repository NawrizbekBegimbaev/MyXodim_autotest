"""Admin login boundary — телефон/пароль варианты, не покрытые в test_login_negative."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Browser, expect

from config.settings import Settings
from pages.admin.login_page import AdminLoginPage


@pytest.fixture
def fresh_login_page(browser: Browser, settings: Settings) -> AdminLoginPage:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    return AdminLoginPage(page).goto(settings.admin_url)


def _stays_on_login(login: AdminLoginPage, settings: Settings) -> None:
    expect(login.page).to_have_url(re.compile(r"/login"), timeout=settings.expect_timeout)


@pytest.mark.negative
@pytest.mark.parametrize(
    "phone",
    [
        pytest.param("+998 99 123 4567", id="spaces"),
        pytest.param("+998-99-123-45-67", id="hyphens"),
        pytest.param("(+998) 991234567", id="parens"),
        pytest.param("998991234567", id="no-plus"),
        pytest.param("+99899123456789012", id="too-long"),
        pytest.param("  +998991234567  ", id="leading-trailing-spaces"),
        pytest.param("+998٩٩١٢٣٤٥٦٧", id="unicode-arabic-digits"),
    ],
)
@allure.title("Login boundary phone: '{phone}' → форма остаётся на /login")
def test_admin_login_with_phone_variant_stays_on_login(
    fresh_login_page: AdminLoginPage, settings: Settings, phone: str
) -> None:
    fresh_login_page.login(phone, "any-password")
    _stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@allure.title("Login boundary: только телефон без пароля → форма остаётся")
def test_admin_login_with_only_phone_stays_on_login(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.page.get_by_role("textbox", name="Телефон").fill(settings.super_admin_phone)
    fresh_login_page.submit_button.click()
    _stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@allure.title("Login boundary: только пароль без телефона → форма остаётся")
def test_admin_login_with_only_password_stays_on_login(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.page.get_by_role("textbox", name="Пароль").fill("anything")
    fresh_login_page.submit_button.click()
    _stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@pytest.mark.parametrize(
    "password",
    [
        pytest.param("!@#$%^&*()", id="special-chars"),
        pytest.param("a\tb\nc", id="tab-newline"),
        pytest.param(" " * 50, id="only-spaces"),
        pytest.param("  admin123  ", id="leading-trailing-spaces"),
    ],
)
@allure.title("Login boundary password: '{password}' → форма остаётся")
def test_admin_login_with_password_variant_stays_on_login(
    fresh_login_page: AdminLoginPage, settings: Settings, password: str
) -> None:
    fresh_login_page.login(settings.super_admin_phone, password)
    _stays_on_login(fresh_login_page, settings)
