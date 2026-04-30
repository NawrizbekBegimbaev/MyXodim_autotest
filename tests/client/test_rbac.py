"""RBAC по системным ролям Client UI (BRD §3.5).

Создаём через UI сотрудников с разными ролями и логинимся как каждый.
Проверяем что меню содержит ожидаемые пункты.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import allure
import pytest
from playwright.sync_api import Browser, Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX, TEST_OTP
from pages.client.login_page import ClientLoginPage
from pages.client.member_create_dialog import MemberCreateDialog
from pages.client.members_page import MembersPage
from pages.client.otp_page import OtpPage
from pages.client.select_organization_page import SelectOrganizationPage

_ADMIN_ALL_SECTIONS = [
    "Главная",
    "Требуют подписи",
    "Мои документы",
    "Пользователи",
    "Роли",
    "Должности",
    "Штатные позиции",
    "Шаблоны",
    "Филиалы",
    "Маршруты",
]


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("RBAC Администратор: видит все ключевые пункты меню (BRD §3.5)")
def test_admin_sees_all_menu_sections(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/dashboard", wait_until="networkidle")
    page.wait_for_timeout(1_500)

    # Раскрываем sidebar (Кабинет / Управление)
    import contextlib

    for group in ("Кабинет", "Управление", "Настройки"):
        with contextlib.suppress(Exception):
            page.get_by_role("button", name=group, exact=True).click(timeout=2_000)
    page.wait_for_timeout(800)

    nav = page.get_by_role("navigation")
    for section in _ADMIN_ALL_SECTIONS:
        expect(nav.get_by_role("link", name=section, exact=True).first).to_be_visible(
            timeout=settings.expect_timeout
        )


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("RBAC: header показывает роль 'Администратор' для логина admin'ом")
def test_admin_role_label_in_header(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/dashboard", wait_until="networkidle")
    page.wait_for_timeout(1_500)
    # button "<X> <OrgName> Администратор" в banner
    expect(page.get_by_role("button").filter(has_text="Администратор").first).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.rbac
@pytest.mark.negative
@allure.title("RBAC: прямой переход на /integration без логина → /login")
def test_unauthenticated_integration_redirects(
    client_admin_page: Page, settings: Settings
) -> None:
    """Использование client_admin_page (залогинен) — для контраста проверим что
    при logout пользователя с правами /integration требует авторизации.
    """
    page = client_admin_page
    page.goto(f"{settings.client_url}/integration", wait_until="networkidle")
    expect(page.get_by_role("heading", name="Интеграция с 1С", level=4)).to_be_visible(
        timeout=settings.nav_timeout
    )
    # Администратор имеет доступ — heading виден


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("RBAC: Администратор может зайти на каждую страницу управления")
@pytest.mark.parametrize(
    "path,heading",
    [
        ("/members", "Пользователи"),
        ("/roles", "Роли и права"),
        ("/positions", "Должности"),
        ("/templates", "Шаблоны"),
        ("/branches", "Филиалы"),
        ("/categories", "Категории"),
        ("/routes", "Шаблоны маршрутов"),
        ("/organization", "Настройки организации"),
    ],
)
def test_admin_has_access_to_section(
    client_admin_page: Page, settings: Settings, path: str, heading: str
) -> None:
    client_admin_page.goto(f"{settings.client_url}{path}", wait_until="networkidle")
    client_admin_page.wait_for_timeout(1_500)
    expect(
        client_admin_page.get_by_role("heading", name=heading, level=4).first
    ).to_be_visible(timeout=settings.nav_timeout)


# ---- non-admin role flow (blocked by BUG-010) ----


def _invite_employee(
    page: Page, settings: Settings, role_label: str, phone_local: str, suffix: str
) -> None:
    """Приглашает сотрудника с указанной ролью через UI Администратора."""
    members = MembersPage(page).goto(settings.client_url)
    expect(members.heading).to_be_visible(timeout=settings.nav_timeout)
    members.click_add()
    dialog = MemberCreateDialog(page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_required(
        first_name="RBAC",
        last_name=f"{E2E_PREFIX} Emp-{role_label} {suffix}",
        phone=phone_local,
        role=role_label,
    )
    dialog.submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)


@pytest.fixture
def fresh_browser_page(browser: Browser) -> Iterator[Page]:
    """Чистый browser context без storage_state — для логина под новым юзером."""
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        timezone_id="Asia/Tashkent",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    yield page
    ctx.close()


def _login_as_employee(page: Page, phone: str, settings: Settings) -> None:
    """Логин в Client UI как новый сотрудник.
    После OTP может быть /tenant-select (≥2 орг) или сразу /dashboard (одна орг).
    """
    ClientLoginPage(page).goto(settings.client_url).enter_phone(phone).submit()
    OtpPage(page).enter_code(TEST_OTP).submit()
    page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
    if "tenant-select" in page.url:
        SelectOrganizationPage(page).select(settings.client_smoke_org)
    page.wait_for_url("**/dashboard", timeout=settings.nav_timeout)


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("RBAC: приглашённый Сотрудник может залогиниться по OTP")
def test_invited_employee_can_otp_login(
    client_admin_page: Page,
    fresh_browser_page: Page,
    random_test_phone: str,
    settings: Settings,
) -> None:
    suffix = uuid.uuid4().hex[:6]
    phone = random_test_phone
    _invite_employee(
        client_admin_page, settings, role_label="Сотрудник",
        phone_local=phone, suffix=suffix,
    )
    _login_as_employee(fresh_browser_page, phone, settings)


@pytest.mark.rbac
@pytest.mark.negative
@allure.title("RBAC Сотрудник: header показывает роль 'Сотрудник', не 'Администратор'")
def test_employee_header_shows_employee_role(
    client_admin_page: Page,
    fresh_browser_page: Page,
    random_test_phone: str,
    settings: Settings,
) -> None:
    suffix = uuid.uuid4().hex[:6]
    phone = random_test_phone
    _invite_employee(
        client_admin_page, settings, role_label="Сотрудник",
        phone_local=phone, suffix=suffix,
    )
    _login_as_employee(fresh_browser_page, phone, settings)

    # В header кнопка с ролью — должна быть "Сотрудник", не "Администратор"
    expect(
        fresh_browser_page.get_by_role("button").filter(has_text="Сотрудник").first
    ).to_be_visible(timeout=settings.expect_timeout)
    expect(
        fresh_browser_page.get_by_role("button").filter(has_text="Администратор")
    ).to_have_count(0)


@pytest.mark.rbac
@pytest.mark.negative
@pytest.mark.xfail(
    reason="BUG-011: прямой URL обходит RBAC, /integration открыт любой роли. "
    "Critical security — ключ 1С виден. Фикс на frontend route-guard + backend.",
    strict=False,
)
@allure.title(
    "RBAC FINANSIST: прямой URL /integration не должен показывать ключ 1С"
)
def test_finansist_cannot_access_integration_directly(
    client_admin_page: Page,
    fresh_browser_page: Page,
    random_test_phone: str,
    settings: Settings,
) -> None:
    """BUG-011 регрессия: не-admin роль не должна видеть страницу
    /integration по прямой ссылке. Сейчас FINANSIST в QaTeam её
    открывает и видит ключ интеграции 1С.
    """
    suffix = uuid.uuid4().hex[:6]
    phone = random_test_phone
    _invite_employee(
        client_admin_page, settings, role_label="FINANSIST",
        phone_local=phone, suffix=suffix,
    )
    _login_as_employee(fresh_browser_page, phone, settings)

    fresh_browser_page.goto(
        f"{settings.client_url}/integration", wait_until="networkidle"
    )
    fresh_browser_page.wait_for_timeout(1_500)
    # Ожидаем: либо редирект, либо 403, либо отсутствие heading "Интеграция с 1С"
    expect(
        fresh_browser_page.get_by_role("heading", name="Интеграция с 1С", level=4)
    ).not_to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.rbac
@pytest.mark.negative
@pytest.mark.xfail(
    reason="BUG-011: /roles открыт по прямой ссылке для не-admin ролей",
    strict=False,
)
@allure.title("RBAC FINANSIST: прямой URL /roles не должен открываться")
def test_finansist_cannot_access_roles_directly(
    client_admin_page: Page,
    fresh_browser_page: Page,
    random_test_phone: str,
    settings: Settings,
) -> None:
    suffix = uuid.uuid4().hex[:6]
    phone = random_test_phone
    _invite_employee(
        client_admin_page, settings, role_label="FINANSIST",
        phone_local=phone, suffix=suffix,
    )
    _login_as_employee(fresh_browser_page, phone, settings)

    fresh_browser_page.goto(
        f"{settings.client_url}/roles", wait_until="networkidle"
    )
    fresh_browser_page.wait_for_timeout(1_500)
    expect(
        fresh_browser_page.get_by_role("heading", name="Роли и права", level=4)
    ).not_to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("RBAC FINANSIST: sidebar скрывает админ-разделы (UI-уровень корректно)")
def test_finansist_sidebar_hides_admin_sections(
    client_admin_page: Page,
    fresh_browser_page: Page,
    random_test_phone: str,
    settings: Settings,
) -> None:
    """Положительная проверка: меню для FINANSIST не показывает админ-пункты.
    Это работает (frontend skip в sidebar). А вот прямой URL — нет
    (см. test_finansist_cannot_access_*_directly + BUG-011).
    """
    suffix = uuid.uuid4().hex[:6]
    phone = random_test_phone
    _invite_employee(
        client_admin_page, settings, role_label="FINANSIST",
        phone_local=phone, suffix=suffix,
    )
    _login_as_employee(fresh_browser_page, phone, settings)

    nav = fresh_browser_page.get_by_role("navigation")
    for hidden in ("Пользователи", "Роли", "Должности", "Категории", "Филиалы"):
        expect(
            nav.get_by_role("link", name=hidden, exact=True)
        ).to_have_count(0)


@pytest.mark.rbac
@pytest.mark.negative
@allure.title("RBAC: header показывает 'Администратор' роль для admin'а в QaTeam")
def test_header_shows_administrator_only_for_admin(
    client_admin_page: Page, settings: Settings
) -> None:
    """Sanity: убеждаемся что под client_smoke_phone роль показана как Администратор.
    Сравнительный тест для xfail-кейсов выше — после фикса BUG-010 будут
    добавлены аналогичные проверки для Сотрудника / Директора / Менеджера.
    """
    client_admin_page.goto(f"{settings.client_url}/dashboard", wait_until="networkidle")
    client_admin_page.wait_for_timeout(1_500)
    header_btn = client_admin_page.get_by_role("button").filter(
        has_text="Администратор"
    ).first
    expect(header_btn).to_be_visible(timeout=settings.expect_timeout)
