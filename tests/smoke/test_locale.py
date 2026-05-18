"""Smoke: переключатель локали меняет UI-тексты.

Дефолт стенда — RU. UZ переключается через языковую кнопку:
- Admin UI: button "change language" — toggle ru/uz
- Client UI: button "Switch language to O'zbekcha" / "Switch language to Русский" — toggle RU/UZ

Эти тесты проверяют что переключатель РАБОТАЕТ. Где он не работает на
конкретных элементах (Adminlar, Foydalanuvchilar etc.) — отдельные xfail
в tests/regression/test_bug_regressions.py.
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import BrowserContext, Page, expect

from config.settings import Settings
from pages.admin.login_page import AdminLoginPage
from pages.client.login_page import ClientLoginPage
from pages.components.locale_switcher import AdminLocaleSwitcher, ClientLocaleSwitcher

# ============================================================
# Admin UI
# ============================================================


@pytest.mark.smoke
@pytest.mark.needs_admin_creds
@pytest.mark.skip(reason="BUG-029 admin auth broken")
@allure.title("Admin UI: переключатель локали меняет ru ↔ uz")
def test_admin_locale_toggle_changes_button_label(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    switcher = AdminLocaleSwitcher(page)
    expect(switcher.button).to_be_visible(timeout=settings.expect_timeout)

    # Стартовое состояние — ru (дефолт стенда)
    assert switcher.current() == "ru", f"Ожидали ru, текущая: {switcher.current()!r}"

    switcher.switch_to("uz")
    assert switcher.current() == "uz"

    switcher.switch_to("ru")
    assert switcher.current() == "ru"


@pytest.mark.smoke
@pytest.mark.needs_admin_creds
@pytest.mark.skip(reason="BUG-029 admin auth broken")
@allure.title("Admin UI: переключение на uz меняет heading дашборда RU→UZ")
def test_admin_locale_uz_changes_dashboard_heading(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")

    # RU: "Дашборд"
    expect(page.get_by_role("heading", name="Дашборд", level=4)).to_be_visible(
        timeout=settings.expect_timeout
    )

    AdminLocaleSwitcher(page).switch_to("uz")

    # UZ: "Bosh sahifa"
    expect(page.get_by_role("heading", name="Bosh sahifa", level=4)).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.smoke
@pytest.mark.needs_admin_creds
@pytest.mark.skip(reason="BUG-029 admin auth broken")
@allure.title("Admin UI: переключение локали меняет sidebar nav-ссылки")
def test_admin_locale_uz_changes_sidebar_links(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    nav = page.get_by_role("navigation").first

    # RU: "Дашборд", "Компании"
    expect(nav.get_by_role("link", name="Дашборд", exact=True)).to_be_visible()
    expect(nav.get_by_role("link", name="Компании", exact=True)).to_be_visible()

    AdminLocaleSwitcher(page).switch_to("uz")

    # UZ: "Bosh sahifa", "Kompaniyalar"
    expect(
        nav.get_by_role("link", name="Bosh sahifa", exact=True)
    ).to_be_visible(timeout=settings.expect_timeout)
    expect(
        nav.get_by_role("link", name="Kompaniyalar", exact=True)
    ).to_be_visible()


# ============================================================
# Client UI
# ============================================================


@pytest.mark.smoke
@allure.title("Client UI: переключатель локали меняет RU ↔ UZ")
def test_client_locale_toggle_changes_button_label(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    switcher = ClientLocaleSwitcher(page)
    expect(switcher.button).to_be_visible(timeout=settings.expect_timeout)

    assert switcher.current() == "RU", f"Ожидали RU, текущая: {switcher.current()!r}"

    switcher.switch_to("UZ")
    assert switcher.current() == "UZ"

    switcher.switch_to("RU")
    assert switcher.current() == "RU"


@pytest.mark.smoke
@allure.title("Client UI: переключение на UZ меняет heading /documents")
def test_client_locale_uz_changes_documents_heading(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")

    expect(page.get_by_role("heading", name="Документы", level=4)).to_be_visible(
        timeout=settings.expect_timeout
    )

    ClientLocaleSwitcher(page).switch_to("UZ")

    expect(page.get_by_role("heading", name="Hujjatlar", level=4)).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.smoke
@allure.title("Client UI: /documents остаётся на UZ после переключения")
def test_client_locale_uz_keeps_documents_page_translated(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")

    ClientLocaleSwitcher(page).switch_to("UZ")

    expect(page.get_by_role("heading", name="Hujjatlar", level=4)).to_be_visible(
        timeout=settings.expect_timeout
    )


# ============================================================
# Login страницы (без auth, доступны до логина)
# ============================================================


@pytest.mark.smoke
@allure.title("Admin /login: переключатель локали есть до логина")
def test_admin_login_page_has_locale_toggle(
    page: Page, settings: Settings
) -> None:
    AdminLoginPage(page).goto(settings.admin_url)
    # Локаль-кнопка может быть на login странице (Admin/Client разнятся).
    # Если её нет — fallback после логина.
    btn = page.get_by_role("button", name="change language")
    if btn.count() == 0:
        pytest.skip("Admin /login без локаль-переключателя — он только в авторизованном UI")
    expect(btn).to_be_visible()


@pytest.mark.smoke
@allure.title("Client /login: страница рендерится в RU по дефолту")
def test_client_login_page_default_locale_is_ru(
    page: Page, settings: Settings
) -> None:
    """Дефолтная локаль на Client login — RU. UZ-вариант через перезагрузку
    с уже сохранённой UZ-сессией (сюда не лезем).
    """
    ClientLoginPage(page).goto(settings.client_url)
    expect(
        page.get_by_role("heading", name="Добро пожаловать в BusinessHub", level=5)
    ).to_be_visible(timeout=settings.expect_timeout)
