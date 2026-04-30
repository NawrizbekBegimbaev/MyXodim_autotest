"""Глобальные фикстуры. См. CLAUDE.md §10 (storage_state) и §11 (параллельность)."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from config.settings import Settings
from data import phone_pool
from data.constants import (
    AUTH_DIR,
    CLIENT_ADMIN_STATE_FILE,
    SUPER_ADMIN_STATE_FILE,
    TEST_OTP,
)
from pages.admin.login_page import AdminLoginPage
from pages.client.login_page import ClientLoginPage
from pages.client.otp_page import OtpPage
from pages.client.select_organization_page import SelectOrganizationPage


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict[str, Any]) -> dict[str, Any]:
    """По умолчанию используем bundled Chromium (для smoke/CI).

    Для EIMZO-тестов фикстура `eimzo_browser_args` подменяет channel на системный Chrome.
    """
    return {**browser_type_launch_args}


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict[str, Any], settings: Settings
) -> dict[str, Any]:
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "locale": "ru-RU",
        "timezone_id": "Asia/Tashkent",
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def super_admin_state(browser: Browser, settings: Settings) -> str:
    """UI-логин Super Admin один раз за сессию, сохраняем storage_state.

    Используется во всех тестах кроме главного E2E (где пользователи создаются внутри теста).
    """
    Path(AUTH_DIR).mkdir(exist_ok=True)
    state_path = SUPER_ADMIN_STATE_FILE
    # Свежий UI-логин каждой pytest-сессии — JWT в файле может протухнуть
    # за время между прогонами (TTL ~1 час).
    Path(state_path).unlink(missing_ok=True)

    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        timezone_id="Asia/Tashkent",
        ignore_https_errors=True,
    )
    import re

    from playwright.sync_api import expect as _expect

    page = ctx.new_page()
    AdminLoginPage(page).goto(settings.admin_url).login(
        settings.super_admin_phone, settings.super_admin_password
    )
    page.wait_for_url(re.compile(r"^(?!.*\blogin\b).*"), timeout=settings.nav_timeout)
    _expect(page.get_by_role("heading", name="Admin User")).to_be_visible(
        timeout=settings.nav_timeout
    )
    page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
    ctx.storage_state(path=state_path)
    ctx.close()
    return state_path


@pytest.fixture
def super_admin_context(
    browser: Browser, super_admin_state: str, browser_context_args: dict[str, Any]
) -> Iterator[BrowserContext]:
    ctx = browser.new_context(**browser_context_args, storage_state=super_admin_state)
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
def super_admin_live_context(
    browser: Browser, settings: Settings
) -> Iterator[BrowserContext]:
    """Session-scope context с живым UI-логином Super Admin.

    Используется в UC-4.2/4.3 (просмотр и toggle компаний) — там storage_state
    не работает: /tenants не рендерит таблицу при load с восстановленной
    сессией, хотя при свежем UI-логине грузит сразу. Возможно связано с BUG-008.
    """
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        timezone_id="Asia/Tashkent",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    AdminLoginPage(page).goto(settings.admin_url).login(
        settings.super_admin_phone, settings.super_admin_password
    )
    page.wait_for_url("**/dashboard", timeout=settings.nav_timeout)
    page.close()
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
def client_admin_state(browser: Browser, settings: Settings) -> str:
    """UI-логин Client UI Администратора в существующей орг + storage_state.

    Используется для positive тестов в существующей орг (пока BUG-001 блокирует
    создание новых компаний). См. CLAUDE.md §10.
    """
    Path(AUTH_DIR).mkdir(exist_ok=True)
    state_path = CLIENT_ADMIN_STATE_FILE
    Path(state_path).unlink(missing_ok=True)

    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        timezone_id="Asia/Tashkent",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    ClientLoginPage(page).goto(settings.client_url).enter_phone(
        settings.client_smoke_phone
    ).submit()
    OtpPage(page).enter_code(TEST_OTP).submit()
    page.wait_for_url("**/tenant-select", timeout=settings.nav_timeout)
    SelectOrganizationPage(page).select(settings.client_smoke_org)
    page.wait_for_url("**/dashboard", timeout=settings.nav_timeout)
    ctx.storage_state(path=state_path)
    ctx.close()
    return state_path


@pytest.fixture
def client_admin_context(
    browser: Browser, client_admin_state: str, browser_context_args: dict[str, Any]
) -> Iterator[BrowserContext]:
    ctx = browser.new_context(**browser_context_args, storage_state=client_admin_state)
    yield ctx
    ctx.close()


@pytest.fixture
def client_admin_page(client_admin_context: BrowserContext) -> Iterator[Page]:
    page = client_admin_context.new_page()
    yield page
    page.close()


def _create_company_via_ui(
    browser: Browser, super_admin_state: str, settings: Settings, prefix: str
) -> dict[str, str]:
    """Утилита: создаёт компанию через UI и возвращает её данные.

    Используется session-scope фикстурами (anchor_company, disable_target_company).
    """
    import secrets as _s
    import uuid as _u

    from pages.admin.create_company_page import CompanyCreatedView, CreateCompanyPage

    suffix = _u.uuid4().hex[:6]
    data = {
        "name": f"{prefix} {suffix}",
        "slug": f"{prefix.strip('[]').strip().lower().replace(' ', '-')}-{suffix}",
        "inn": "".join(str(_s.randbelow(10)) for _ in range(9)),
        "first_name": "Якорь",
        "last_name": "Тестовый",
        "phone_local": f"905{''.join(str(_s.randbelow(10)) for _ in range(7))}",
        "pinfl": f"{_s.randbelow(6) + 1}{''.join(str(_s.randbelow(10)) for _ in range(13))}",
    }
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        timezone_id="Asia/Tashkent",
        ignore_https_errors=True,
        storage_state=super_admin_state,
    )
    page = ctx.new_page()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"]).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    ).submit()
    from playwright.sync_api import expect

    expect(CompanyCreatedView(page).heading).to_be_visible(timeout=settings.nav_timeout)
    ctx.close()
    return data


@pytest.fixture(scope="session")
def anchor_company(browser: Browser, super_admin_state: str, settings: Settings) -> dict[str, str]:
    """Якорная компания для negative-тестов UC-4.1 (дубли ИНН/slug/телефон/ПИНФЛ)."""
    return _create_company_via_ui(browser, super_admin_state, settings, prefix="[E2E anchor]")


@pytest.fixture(scope="session")
def disable_target_company(
    browser: Browser, super_admin_state: str, settings: Settings
) -> dict[str, str]:
    """Отдельная компания для UC-4.3 (toggle disable/enable). Не пересекается с anchor."""
    return _create_company_via_ui(browser, super_admin_state, settings, prefix="[E2E disable]")


@pytest.fixture(scope="session")
def mock1c_company(
    browser: Browser, super_admin_state: str, settings: Settings
) -> dict[str, str]:
    """Компания для Mock 1C интеграции — содержит integrationKey + tenantId.

    Создаётся через Admin UI и парсит success-page для извлечения ключа.
    Возвращает данные company + integration_key + tenant_id + admin_user_id.
    """
    import re as _re
    import secrets as _s
    import uuid as _u

    from pages.admin.create_company_page import CompanyCreatedView, CreateCompanyPage

    suffix = _u.uuid4().hex[:6]
    data = {
        "name": f"[E2E mock1c] {suffix}",
        "slug": f"e2e-m1c-{suffix}",
        "inn": "".join(str(_s.randbelow(10)) for _ in range(9)),
        "first_name": "Якорь",
        "last_name": "Моков",
        # 9 цифр (90 + 7 random) — Client UI login требует строго 9, Admin тоже примет
        "phone_local": f"90{''.join(str(_s.randbelow(10)) for _ in range(7))}",
        "pinfl": f"{_s.randbelow(6) + 1}{''.join(str(_s.randbelow(10)) for _ in range(13))}",
    }
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        timezone_id="Asia/Tashkent",
        ignore_https_errors=True,
        storage_state=super_admin_state,
    )
    page = ctx.new_page()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"]).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    ).submit()

    from playwright.sync_api import expect as _expect

    success = CompanyCreatedView(page)
    _expect(success.heading).to_be_visible(timeout=settings.nav_timeout)
    body = page.locator("body").inner_text()
    key_match = _re.search(r"bh_live_[a-f0-9]{32}", body)
    uuids = _re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", body)
    if not key_match or len(uuids) < 2:
        ctx.close()
        raise RuntimeError("integrationKey/tenantId/adminUserId не найдены на success-page")
    data["integration_key"] = key_match.group(0)
    data["tenant_id"] = uuids[0]
    data["admin_user_id"] = uuids[1]
    data["phone_full"] = f"+998{data['phone_local']}"
    ctx.close()
    return data


@pytest.fixture
def phone_from_pool(settings: Settings) -> Iterator[str]:
    """Атомарно выдаёт свободный тестовый телефон, возвращает в пул в teardown.

    Использовать ТОЛЬКО там где телефон не сохраняется в БД (логин существующего юзера,
    проверка валидации формы без submit). Для creating-тестов используй
    `random_test_phone` — те телефоны одноразовые и переиспользовать нельзя.
    """
    with phone_pool.lease(settings.phone_pool_start, settings.phone_pool_size) as phone:
        yield phone


@pytest.fixture
def random_test_phone() -> str:
    """Рандомный одноразовый телефон для creating-тестов (см. data.phone_pool)."""
    return phone_pool.random_test_phone()
