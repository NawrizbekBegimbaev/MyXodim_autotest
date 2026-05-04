"""Глобальные фикстуры. См. CLAUDE.md §10 (storage_state) и §11 (параллельность)."""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Browser, BrowserContext, ConsoleMessage, Page, Request, Response

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

# Игнор-паттерны для console — шум, не связанный с нашими багами. Расширяй по мере прогона.
# 4xx-ответы браузер логирует как console.error — но 4xx часто валидное negative-поведение
# и нам не нужен дубль с _on_response (который ловит 5xx отдельно).
_CONSOLE_IGNORE = (
    re.compile(r"ResizeObserver loop"),
    re.compile(r"Failed to load resource.*favicon"),
    re.compile(r"chrome-extension://"),
    # Browser-emitted "Failed to load resource: 4xx" — наш _on_response отдельно ловит 5xx
    re.compile(r"Failed to load resource: the server responded with a status of 4\d\d"),
    # CORS preflight noise на dev-стенде
    re.compile(r"Access to .* has been blocked by CORS"),
)

# Только бэкенды нашего dev-стенда — игнорируем 4xx/5xx от сторонних аналитики/CDN.
_BACKEND_HOST_PAT = re.compile(r"https?://(dev-hub-(?:api|admin|client)|dev-mock-1c)\.greatmall\.uz")


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


# Init-скрипт принудительно ставит RU-локаль в localStorage до любой загрузки.
# С 2026-05-04 фронт переехал на UZ default (commit 137196d) — без этого
# скрипта все тесты, которые ассертят RU-тексты, ломаются.
# Ключи: admin-lang (Admin UI), client-lang (Client UI). Фронт читает их
# при init и применяет локаль.
_FORCE_RU_LANG_SCRIPT = (
    "try {"
    "  localStorage.setItem('admin-lang', 'ru');"
    "  localStorage.setItem('client-lang', 'ru');"
    "} catch (e) { /* SecurityError on about:blank — игнор */ }"
)


@pytest.fixture(scope="session", autouse=True)
def _force_ru_lang() -> Iterator[None]:
    """Патчит Browser.new_context на всю сессию, чтобы каждый создаваемый
    контекст автоматически получал init_script с
    admin-lang=ru / client-lang=ru. Скрипт выполняется до любого app-кода
    и обеспечивает RU-локаль независимо от дефолта стенда.

    С 2026-05-04 фронт-команда переключила default на UZ — без этого
    патча все RU-ассерты ломаются.
    """
    from playwright.sync_api._generated import (
        Browser as _Browser,
    )

    original_new_context = _Browser.new_context

    import contextlib  # noqa: PLC0415

    def patched(self: Browser, **kwargs: Any) -> BrowserContext:
        ctx = original_new_context(self, **kwargs)
        with contextlib.suppress(Exception):
            ctx.add_init_script(_FORCE_RU_LANG_SCRIPT)
        return ctx

    _Browser.new_context = patched  # type: ignore[method-assign]
    try:
        yield
    finally:
        _Browser.new_context = original_new_context  # type: ignore[method-assign]


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


def _attach_console_guard(
    page: Page, errors: list[str], requests: dict[str, Request]
) -> None:
    """Цепляем listeners на page: console errors, pageerror, response 5xx, неудачные запросы.

    Все собирается в `errors` (для финального assert) и `requests` (last-known per URL,
    для логирования контекста при падении).
    """

    def _on_console(msg: ConsoleMessage) -> None:
        if msg.type != "error":
            return
        text = msg.text
        if any(p.search(text) for p in _CONSOLE_IGNORE):
            return
        errors.append(f"[console.error] {text}")

    def _on_pageerror(exc: Exception) -> None:
        # Нерасхваченные JS-исключения. Эти ВСЕГДА баг — никаких ignore.
        errors.append(f"[pageerror] {exc}")

    def _on_response(resp: Response) -> None:
        # Ловим только 5xx от наших бэков — это серверные баги.
        # 4xx могут быть валидным negative-кейсом, фиксируем но не валим.
        if resp.status < 500:
            return
        if not _BACKEND_HOST_PAT.search(resp.url):
            return
        errors.append(f"[5xx] {resp.status} {resp.request.method} {resp.url}")

    def _on_requestfailed(req: Request) -> None:
        if not _BACKEND_HOST_PAT.search(req.url):
            return
        # ERR_ABORTED — нормальное поведение когда страница навигирует и отменяет
        # in-flight запросы за ассетами. Не баг.
        failure = req.failure or ""
        if "ERR_ABORTED" in failure:
            return
        errors.append(f"[reqfailed] {req.method} {req.url} — {failure}")

    def _on_request(req: Request) -> None:
        requests[req.url] = req

    page.on("console", _on_console)
    page.on("pageerror", _on_pageerror)
    page.on("response", _on_response)
    page.on("requestfailed", _on_requestfailed)
    page.on("request", _on_request)


@pytest.fixture(autouse=True)
def _strict_console(request: pytest.FixtureRequest) -> Iterator[None]:
    """Автоматически вешает guard на все Page, открытые через стандартные фикстуры.

    Включается через ENV `BH_STRICT_CONSOLE=1` (по умолчанию soft — пишет в stderr).
    Тест может opt-out через маркер `@pytest.mark.allow_console_errors`.

    Стратегия:
    - Хук `BrowserContext.new_page` patch-им чтобы навешать listeners на каждый Page.
    - В teardown: если errors не пуст и нет маркера — fail (или warn если soft).
    """
    import os

    if request.node.get_closest_marker("allow_console_errors"):
        yield
        return

    errors: list[str] = []
    last_requests: dict[str, Request] = {}
    strict = os.environ.get("BH_STRICT_CONSOLE", "0") == "1"

    # Патчим методы создания page у всех BrowserContext'ов в этой сессии.
    # Делаем неинвазивно — оборачиваем оригинал.
    original_new_page = BrowserContext.new_page

    def patched_new_page(self: BrowserContext) -> Page:
        page = original_new_page(self)
        _attach_console_guard(page, errors, last_requests)
        return page

    BrowserContext.new_page = patched_new_page  # type: ignore[method-assign]
    try:
        yield
    finally:
        BrowserContext.new_page = original_new_page  # type: ignore[method-assign]
        if errors:
            summary = "\n  ".join(errors[:20])
            msg = f"Browser-side errors during test:\n  {summary}"
            if strict:
                pytest.fail(msg, pytrace=False)
            else:
                # Soft: пишем в stderr и attach к allure если есть
                import sys

                print(f"\n[console-guard] {msg}", file=sys.stderr)
                try:
                    import allure

                    allure.attach(
                        "\n".join(errors),
                        name="browser-errors",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                except ImportError:
                    pass


def _worker_id(request: pytest.FixtureRequest) -> str:
    """xdist-aware worker id ('gw0','gw1',... или 'master' при -p no:xdist)."""
    wi = getattr(request.config, "workerinput", None)
    return wi["workerid"] if wi else "master"


def _worker_state_path(base: str, worker: str) -> str:
    """Превращает '.auth/super_admin.json' → '.auth/super_admin-gw0.json'.

    Каждый xdist-воркер пишет в свой файл — иначе race на unlink/create.
    """
    if worker == "master":
        return base
    p = Path(base)
    return str(p.with_name(f"{p.stem}-{worker}{p.suffix}"))


@pytest.fixture(scope="session")
def super_admin_state(
    browser: Browser, settings: Settings, request: pytest.FixtureRequest
) -> str:
    """UI-логин Super Admin один раз за сессию, сохраняем storage_state.

    Используется во всех тестах кроме главного E2E (где пользователи создаются внутри теста).
    """
    Path(AUTH_DIR).mkdir(exist_ok=True)
    state_path = _worker_state_path(SUPER_ADMIN_STATE_FILE, _worker_id(request))
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
def client_admin_state(
    browser: Browser, settings: Settings, request: pytest.FixtureRequest
) -> str:
    """UI-логин Client UI Администратора в существующей орг + storage_state.

    Используется для positive тестов в существующей орг (пока BUG-001 блокирует
    создание новых компаний). См. CLAUDE.md §10.
    """
    Path(AUTH_DIR).mkdir(exist_ok=True)
    state_path = _worker_state_path(CLIENT_ADMIN_STATE_FILE, _worker_id(request))
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
    # После OTP две развилки: ≥2 орг → /tenant-select; одна орг → сразу /documents
    page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
    if "tenant-select" in page.url:
        SelectOrganizationPage(page).select(settings.client_smoke_org)
        page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
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
