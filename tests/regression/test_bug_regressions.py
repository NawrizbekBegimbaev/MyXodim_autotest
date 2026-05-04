"""Регрессионные тесты на открытые баги Huly.

Каждый тест помечен `@pytest.mark.xfail(strict=True)` с reason'ом — баги
открыты, тест должен ПАДАТЬ. Когда фронт-команда фиксит — тест пойдёт XPASS,
strict=True пометит ХPASS как ОШИБКУ → мы автоматически узнаем о фиксе на
очередном прогоне и снимем xfail.

Каналы про баги:
- Huly = primary tracker
- Bussiness/Bugs.txt = staging-копия со steps + evidence
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import BrowserContext, Page, Request, expect

from config.settings import Settings
from pages.admin.login_page import AdminLoginPage

# ============================================================
# BUG-014: Mixed UZ/RU локаль — UZ-вкрапления на RU-страницах
# ============================================================


@pytest.mark.regression
@pytest.mark.xfail(
    strict=True,
    reason="BUG-014: heading /admins на UZ ('Adminlar') в RU-локали. "
    "Должен быть 'Администраторы' или эквивалент.",
)
@allure.title("BUG-014: /admins — heading должен быть на RU, не UZ")
def test_bug014_admins_heading_should_be_ru(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    # Когда BUG-014 пофиксят — будет heading на RU. Сейчас "Adminlar".
    expect(
        page.get_by_role("heading", level=4).filter(
            has_text=re.compile(r"^Администратор", re.IGNORECASE)
        )
    ).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.regression
@pytest.mark.xfail(
    strict=True,
    reason="BUG-014: колонки таблицы /admins на UZ (Ism/Telefon/Holat/Yaratilgan). "
    "Должны быть на RU.",
)
@allure.title("BUG-014: /admins — колонки должны быть на RU")
def test_bug014_admins_columns_should_be_ru(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    table = page.get_by_role("table").first
    # Хотя бы одна RU-колонка должна быть. Сейчас все UZ → fail → xfail.
    for ru_col in ("Имя", "Телефон", "Статус", "Создан"):
        expect(table.get_by_role("columnheader", name=ru_col, exact=True)).to_be_visible(
            timeout=settings.expect_timeout
        )


@pytest.mark.regression
@pytest.mark.xfail(
    strict=True,
    reason="BUG-014: sidebar header кнопки 'Yopish' / 'Yashirish' на UZ в RU UI. "
    "Должны быть 'Закрыть' / 'Скрыть'.",
)
@allure.title("BUG-014: Client UI sidebar header — кнопки на RU")
def test_bug014_client_sidebar_header_buttons_ru(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/dashboard", wait_until="networkidle")
    # Когда фикс — должны быть RU-варианты "Закрыть"/"Скрыть".
    expect(
        page.get_by_role("button", name=re.compile(r"^(Закрыть|Скрыть)$"))
    ).to_have_count(2, timeout=settings.expect_timeout)


# ============================================================
# BUG-015: Admin UI шлёт phone без `+` префикса
# ============================================================


@pytest.mark.regression
@allure.title("BUG-015 (FIXED 2026-05-04): Admin login phone начинается с '+' в request body")
def test_bug015_admin_login_request_phone_has_plus_prefix(
    page: Page, settings: Settings
) -> None:
    """Бывший xfail. Закрыт коммитом 646e016 (BHUB-96 на dev) —
    фронт canonicalize'ит phone в '+998<9 цифр>' перед отправкой.
    Тест остался как regression-страж: если кто-то снова сломает
    нормализацию, тест поймает.

    Перехватываем POST /admin/auth/login и читаем request body."""
    captured: dict[str, str] = {}

    def _capture(request: Request) -> None:
        if "/api/v1/admin/auth/login" in request.url and request.method == "POST":
            captured["body"] = request.post_data or ""

    page.on("request", _capture)

    # Юзер вводит локальные 9 цифр (без префикса). settings.super_admin_phone
    # хранится в формате "+998XXXXXXXXX" — вырезаем prefix.
    local_phone = settings.super_admin_phone.removeprefix("+998")
    AdminLoginPage(page).goto(settings.admin_url).enter_credentials(
        local_phone, settings.super_admin_password
    ).submit()

    # Ждём что запрос ушёл (status может быть 200 или 401 — нам важен только body)
    page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)

    assert "body" in captured, "Запрос на /admin/auth/login не был перехвачен"
    body = captured["body"]
    # Ожидаемое корректное поведение — phone начинается с '+'
    match = re.search(r'"phone"\s*:\s*"([^"]+)"', body)
    assert match, f"phone не найден в request body: {body[:200]}"
    phone = match.group(1)
    assert phone.startswith("+"), (
        f"BUG-015: phone отправлен без '+' префикса: {phone!r} в body {body[:200]}"
    )
