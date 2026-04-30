"""Client UI login negative + security + session — аналог Admin login negative."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Browser, Dialog, expect

from config.settings import Settings
from data.constants import TEST_OTP
from pages.client.login_page import ClientLoginPage
from pages.client.otp_page import OtpPage


@pytest.fixture
def fresh_client_login(browser: Browser, settings: Settings) -> ClientLoginPage:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    return ClientLoginPage(page).goto(settings.client_url)


def _stays_on_login(login: ClientLoginPage, settings: Settings) -> None:
    expect(login.page).to_have_url(re.compile(r"/login"), timeout=settings.expect_timeout)


# ---------- Phone form negative ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "phone",
    [
        pytest.param("abcdefghi", id="letters"),
        pytest.param("123", id="too-short"),
        pytest.param("90 12 34 567", id="spaces"),
        pytest.param("90-12-34-567", id="hyphens"),
        pytest.param("00000000", id="too-short-zeros"),
    ],
)
@allure.title("Client login phone variant: '{phone}' → форма остаётся")
def test_client_login_phone_variant_stays_on_login(
    fresh_client_login: ClientLoginPage, settings: Settings, phone: str
) -> None:
    fresh_client_login.enter_phone(phone).submit()
    _stays_on_login(fresh_client_login, settings)


@pytest.mark.negative
@allure.title("Client login: пустой телефон → submit заблокирован / форма остаётся")
def test_client_login_empty_phone_stays_on_login(
    fresh_client_login: ClientLoginPage, settings: Settings
) -> None:
    fresh_client_login.submit_button.click()
    _stays_on_login(fresh_client_login, settings)


@pytest.mark.negative
@allure.title("Client login security: XSS-payload в телефоне → не исполнен")
def test_client_login_xss_payload_does_not_execute(
    fresh_client_login: ClientLoginPage, settings: Settings
) -> None:
    page = fresh_client_login.page
    dialog_seen: list[str] = []

    def on_dialog(d: Dialog) -> None:
        dialog_seen.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)

    fresh_client_login.enter_phone("<script>alert(1)</script>").submit()
    _stays_on_login(fresh_client_login, settings)
    assert dialog_seen == [], f"XSS вызвал dialog: {dialog_seen}"


# ---------- OTP step negative ----------


@pytest.mark.negative
@allure.title("Client OTP: невалидный код (пусто) → форма остаётся")
def test_client_otp_empty_code_stays(
    fresh_client_login: ClientLoginPage, settings: Settings
) -> None:
    fresh_client_login.enter_phone(settings.client_smoke_phone).submit()
    otp = OtpPage(fresh_client_login.page)
    fresh_client_login.page.wait_for_timeout(2_000)
    otp.submit()
    _stays_on_login(fresh_client_login, settings)


@pytest.mark.negative
@pytest.mark.parametrize(
    "code",
    [
        pytest.param("12345", id="too-short"),
        pytest.param("abcdef", id="letters"),
    ],
)
@allure.title("Client OTP: неверный формат '{code}' → форма остаётся")
def test_client_otp_invalid_format_stays(
    fresh_client_login: ClientLoginPage, settings: Settings, code: str
) -> None:
    fresh_client_login.enter_phone(settings.client_smoke_phone).submit()
    otp = OtpPage(fresh_client_login.page)
    fresh_client_login.page.wait_for_timeout(2_000)
    otp.enter_code(code).submit()
    fresh_client_login.page.wait_for_timeout(1_500)
    _stays_on_login(fresh_client_login, settings)


# ---------- Session / direct URL ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/dashboard", id="dashboard"),
        pytest.param("/members", id="members"),
        pytest.param("/positions", id="positions"),
        pytest.param("/documents", id="documents"),
        pytest.param("/inbox", id="inbox"),
    ],
)
@allure.title("Client direct URL '{path}' без auth → редирект на /login")
def test_client_direct_url_without_auth_redirects(
    browser: Browser, settings: Settings, path: str
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900}, ignore_https_errors=True
    )
    page = ctx.new_page()
    page.goto(f"{settings.client_url}{path}", wait_until="networkidle")
    expect(page).to_have_url(re.compile(r"/login"), timeout=settings.nav_timeout)
    ctx.close()


@pytest.mark.positive
@allure.title("Client session: refresh после логина — сессия сохраняется")
def test_client_dashboard_refresh_keeps_session(
    browser: Browser, settings: Settings
) -> None:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    ClientLoginPage(page).goto(settings.client_url).enter_phone(
        settings.client_smoke_phone
    ).submit()
    OtpPage(page).enter_code(TEST_OTP).submit()
    page.wait_for_url("**/tenant-select", timeout=settings.nav_timeout)
    page.reload(wait_until="networkidle")
    expect(page).to_have_url(re.compile(r"/(tenant-select|dashboard)"), timeout=settings.nav_timeout)
    ctx.close()
