"""RBAC по системным ролям Client UI (BRD §3.5).

Sidebar с 2026-05-03 разнесён по группам (Документооборот / Оргструктура /
Настройки), см. pages/client/sidebar.py.

CRUD-тесты (приглашение сотрудника + проверка под его аккаунтом) помечены
@pytest.mark.creates_data — запускаются по явному запросу. Read-only тесты
работают всегда.
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
from pages.client.sidebar import ADMIN_NAV, ClientSidebar

# ============================================================
# Read-only sidebar / access tests
# ============================================================


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("RBAC Администратор: видит все ключевые пункты меню (BRD §3.5)")
def test_admin_sees_all_menu_sections(
    client_admin_page: Page, settings: Settings
) -> None:
    page = client_admin_page
    page.goto(f"{settings.client_url}/dashboard", wait_until="networkidle")

    sidebar = ClientSidebar(page).expand_all()

    for _group, label, _path in ADMIN_NAV:
        expect(sidebar.link(label).first).to_be_visible(
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
    expect(
        page.get_by_role("button").filter(has_text="Администратор").first
    ).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.rbac
@pytest.mark.negative
@allure.title("RBAC: Администратор имеет доступ к /integration (контроль для BUG-011)")
def test_admin_can_access_integration(
    client_admin_page: Page, settings: Settings
) -> None:
    """Администратор должен иметь доступ к /integration. Это контрольный
    тест, чтобы быть уверенным что BUG-011 проявляется именно у не-admin
    ролей, а не глобальная блокировка.
    """
    page = client_admin_page
    page.goto(f"{settings.client_url}/integration", wait_until="networkidle")
    # /integration с 2026-05-03 — hub-страница со списком интеграций
    # (1C / Bitrix24 / Налоговая). Heading стал просто "Интеграция".
    expect(
        page.get_by_role("heading", name="Интеграция", level=4)
    ).to_be_visible(timeout=settings.nav_timeout)
    # Карточка 1C должна присутствовать в hub'е
    expect(page.get_by_role("heading", name="1C", level=6)).to_be_visible()


@pytest.mark.rbac
@pytest.mark.positive
@allure.title("RBAC: Администратор может зайти на каждую страницу управления (URL)")
@pytest.mark.parametrize(
    "path,heading",
    [
        ("/members", "Пользователи"),
        ("/positions", "Должности"),
        ("/org-positions", "Штатные позиции"),
        ("/templates", "Шаблоны"),
        ("/branches", "Филиалы"),
        ("/departments", "Отделы"),
        ("/routes", "Шаблоны маршрутов"),
        ("/categories", "Категории"),
        ("/organization", "Настройки организации"),
        ("/integration", "Интеграция"),
    ],
)
def test_admin_has_access_to_section(
    client_admin_page: Page, settings: Settings, path: str, heading: str
) -> None:
    client_admin_page.goto(
        f"{settings.client_url}{path}", wait_until="networkidle"
    )
    expect(
        client_admin_page.get_by_role("heading", name=heading, level=4).first
    ).to_be_visible(timeout=settings.nav_timeout)


# ============================================================
# CRUD-тесты ниже создают сотрудника через UI и логинятся под ним.
# Помечены creates_data — пускаются по явному запросу.
# ============================================================


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


@pytest.mark.creates_data
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


@pytest.mark.creates_data
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

    expect(
        fresh_browser_page.get_by_role("button").filter(has_text="Сотрудник").first
    ).to_be_visible(timeout=settings.expect_timeout)
    expect(
        fresh_browser_page.get_by_role("button").filter(has_text="Администратор")
    ).to_have_count(0)


@pytest.mark.creates_data
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
    # Не-admin не должен видеть hub /integration: ни heading, ни карточку 1C
    expect(
        fresh_browser_page.get_by_role("heading", name="Интеграция", level=4)
    ).not_to_be_visible(timeout=settings.expect_timeout)
    expect(
        fresh_browser_page.get_by_role("heading", name="1C", level=6)
    ).not_to_be_visible()


@pytest.mark.creates_data
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
    expect(
        fresh_browser_page.get_by_role("heading", name="Роли и права", level=4)
    ).not_to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.creates_data
@pytest.mark.rbac
@pytest.mark.positive
@allure.title("RBAC FINANSIST: sidebar скрывает админ-разделы (UI-уровень корректно)")
def test_finansist_sidebar_hides_admin_sections(
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

    sidebar = ClientSidebar(fresh_browser_page)
    # Группа "Оргструктура" вообще не должна быть видна не-admin'у
    expect(sidebar.group_button("Оргструктура")).to_have_count(0)
    # Точечно проверяем что отдельные admin-only ссылки отсутствуют
    for hidden in ("Пользователи", "Должности", "Категории", "Филиалы", "Отделы"):
        expect(sidebar.link(hidden)).to_have_count(0)
