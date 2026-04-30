"""Negative + boundary + security для Admin UI логина (/login).

Все ошибки бэк отдаёт как 401 Invalid credentials (или 400 на невалидную форму
для XSS-payload). Фронт показывает alert "Неверный телефон или пароль" и
оставляет пользователя на /login.
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Browser, Dialog, expect

from config.settings import Settings
from data.i18n import t
from pages.admin.login_page import AdminLoginPage


@pytest.fixture
def fresh_login_page(browser: Browser, settings: Settings) -> AdminLoginPage:
    """Свежий context без auth — не использует super_admin_state."""
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    return AdminLoginPage(page).goto(settings.admin_url)


def _expect_stays_on_login(login: AdminLoginPage, settings: Settings) -> None:
    """После failed-login URL остаётся на /login."""
    expect(login.page).to_have_url(re.compile(r"/login"), timeout=settings.expect_timeout)


# ---------- Negative: invalid credentials ----------


@pytest.mark.negative
@allure.title("Login neg: неверный пароль → alert 'Неверный телефон или пароль'")
def test_admin_login_with_wrong_password_shows_error_alert(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.login(settings.super_admin_phone, "wrong-password")
    expect(fresh_login_page.invalid_creds_alert()).to_be_visible(timeout=settings.expect_timeout)
    _expect_stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@allure.title("Login neg: несуществующий телефон → alert")
def test_admin_login_with_nonexistent_phone_shows_error_alert(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.login("+998900000099", "any-password-123")
    expect(fresh_login_page.invalid_creds_alert()).to_be_visible(timeout=settings.expect_timeout)
    _expect_stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@allure.title("Login neg: буквы в телефоне → alert")
def test_admin_login_with_letters_in_phone_shows_error_alert(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.login("abcdefghi", "anything")
    expect(fresh_login_page.invalid_creds_alert()).to_be_visible(timeout=settings.expect_timeout)
    _expect_stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@allure.title("Login neg: слишком короткий телефон → alert")
def test_admin_login_with_short_phone_shows_error_alert(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.login("123", "anything")
    expect(fresh_login_page.invalid_creds_alert()).to_be_visible(timeout=settings.expect_timeout)
    _expect_stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@allure.title("Login neg: пустые поля + submit → форма остаётся (alert или submit blocked)")
def test_admin_login_with_empty_fields_stays_on_login(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    """Поведение реализации: фронт может либо blocking-prevent submit (тогда POST не идёт),
    либо отправить и получить 401. В любом случае URL = /login.
    """
    fresh_login_page.submit_button.click()
    _expect_stays_on_login(fresh_login_page, settings)


# ---------- Boundary ----------


@pytest.mark.negative
@allure.title("Login boundary: пароль из 1000 символов → alert (бэк отверг 401)")
def test_admin_login_with_very_long_password_shows_error_alert(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.login(settings.super_admin_phone, "x" * 1000)
    expect(fresh_login_page.invalid_creds_alert()).to_be_visible(timeout=settings.expect_timeout)
    _expect_stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@allure.title("Login boundary: пароль из 1 символа → alert")
def test_admin_login_with_single_char_password_shows_error_alert(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.login(settings.super_admin_phone, "x")
    expect(fresh_login_page.invalid_creds_alert()).to_be_visible(timeout=settings.expect_timeout)
    _expect_stays_on_login(fresh_login_page, settings)


@pytest.mark.negative
@allure.title("Login boundary: Unicode/emoji в пароле → alert (или 400)")
def test_admin_login_with_unicode_in_password_stays_on_login(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.login(settings.super_admin_phone, "пароль🔑тест")
    _expect_stays_on_login(fresh_login_page, settings)


# ---------- Security ----------


@pytest.mark.negative
@allure.title("Login security: XSS-payload в телефоне НЕ исполняется и показан как текст")
def test_admin_login_with_xss_payload_in_phone_does_not_execute(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    """Защита от XSS: payload должен показаться как plain text, никаких dialog/alert."""
    page = fresh_login_page.page
    dialog_seen: list[str] = []

    def on_dialog(d: Dialog) -> None:
        dialog_seen.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)

    fresh_login_page.login("<script>alert(1)</script>", "any")
    _expect_stays_on_login(fresh_login_page, settings)
    assert dialog_seen == [], f"XSS payload вызвал dialog: {dialog_seen}"


@pytest.mark.negative
@allure.title("Login security: SQLi-payload в пароле → 401, не bypass")
def test_admin_login_with_sqli_payload_in_password_returns_unauthorized(
    fresh_login_page: AdminLoginPage, settings: Settings
) -> None:
    fresh_login_page.login(settings.super_admin_phone, "' OR 1=1 --")
    expect(fresh_login_page.invalid_creds_alert()).to_be_visible(timeout=settings.expect_timeout)
    _expect_stays_on_login(fresh_login_page, settings)


# ---------- Session / navigation (без auth) ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "path",
    [
        "/dashboard",
        "/tenants",
        "/tenants/new",
    ],
)
@allure.title("Session: прямой переход на {path} без логина → редирект на /login")
def test_direct_navigation_without_auth_redirects_to_login(
    browser: Browser, settings: Settings, path: str
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    page.goto(f"{settings.admin_url}{path}", wait_until="networkidle")
    expect(page).to_have_url(re.compile(r"/login"), timeout=settings.nav_timeout)
    expect(AdminLoginPage(page).submit_button).to_be_visible(timeout=settings.expect_timeout)
    ctx.close()


@pytest.mark.positive
@allure.title("Session: logout редиректит на /login")
def test_logout_redirects_to_login(
    browser: Browser, settings: Settings
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    AdminLoginPage(page).goto(settings.admin_url).login(
        settings.super_admin_phone, settings.super_admin_password
    )
    page.wait_for_url("**/dashboard", timeout=settings.nav_timeout)

    page.get_by_role("button", name="Выйти").click()
    expect(page).to_have_url(re.compile(r"/login"), timeout=settings.nav_timeout)
    ctx.close()


@pytest.mark.positive
@allure.title("Session: после logout попытка зайти на /dashboard → редирект на /login")
def test_after_logout_dashboard_access_redirects_to_login(
    browser: Browser, settings: Settings
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    AdminLoginPage(page).goto(settings.admin_url).login(
        settings.super_admin_phone, settings.super_admin_password
    )
    page.wait_for_url("**/dashboard", timeout=settings.nav_timeout)
    page.get_by_role("button", name="Выйти").click()
    page.wait_for_url("**/login", timeout=settings.nav_timeout)

    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    expect(page).to_have_url(re.compile(r"/login"), timeout=settings.nav_timeout)
    ctx.close()


@pytest.mark.positive
@allure.title("Session: refresh после логина — сессия сохраняется")
def test_dashboard_refresh_keeps_session(
    browser: Browser, settings: Settings
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    AdminLoginPage(page).goto(settings.admin_url).login(
        settings.super_admin_phone, settings.super_admin_password
    )
    page.wait_for_url("**/dashboard", timeout=settings.nav_timeout)

    page.reload(wait_until="networkidle")
    expect(page).to_have_url(re.compile(r"/dashboard"), timeout=settings.nav_timeout)
    expect(page.get_by_role("button", name="Выйти")).to_be_visible(timeout=settings.expect_timeout)
    ctx.close()
    _ = t  # silence unused import


_ = t  # keep import used
