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
@allure.title("BUG-014 (FIXED 2026-05-04): /admins heading на RU 'Администраторы'")
def test_bug014_admins_heading_should_be_ru(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    """Бывший xfail. Закрыт в i18n-batch коммитах: Adminlar → Администраторы.
    Тест остался регрессионным стражем."""
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    expect(
        page.get_by_role("heading", level=4).filter(
            has_text=re.compile(r"^Администратор", re.IGNORECASE)
        )
    ).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.regression
@allure.title("BUG-014 (FIXED 2026-05-04): /admins колонки на RU")
def test_bug014_admins_columns_should_be_ru(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    """Бывший xfail. Колонки переведены: Ism/Telefon/Holat/Yaratilgan
    → Имя/Телефон/Статус/Создан."""
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/admins", wait_until="networkidle")
    table = page.get_by_role("table").first
    for ru_col in ("Имя", "Телефон", "Статус", "Создан"):
        expect(table.get_by_role("columnheader", name=ru_col, exact=True)).to_be_visible(
            timeout=settings.expect_timeout
        )


@pytest.mark.regression
@allure.title("BUG-014 (PARTIAL FIX 2026-05-04): Client sidebar header кнопки на RU")
def test_bug014_client_sidebar_header_buttons_ru(
    client_admin_page: Page, settings: Settings
) -> None:
    """Бывший xfail. Закрыт серией i18n-коммитов на dev:
    Yopish/Yashirish → Свернуть/Скрыть (фронт перевёл как 'collapse',
    не буквальное 'close', поэтому regex принимает оба варианта).

    BUG-014 на /admins (Adminlar/колонки) ещё открыт — этот тест
    проверяет только Client UI sidebar, не весь BUG-014."""
    page = client_admin_page
    page.goto(f"{settings.client_url}/dashboard", wait_until="networkidle")
    # Принимаем оба корректных RU-варианта: 'Свернуть' (collapse) или 'Закрыть' (close).
    expect(
        page.get_by_role("button", name=re.compile(r"^(Свернуть|Закрыть|Скрыть)$"))
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
