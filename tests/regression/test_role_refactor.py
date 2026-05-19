"""Регрессии под BHUB role-refactor (BRD §2.3): 4 системные роли.

Read-only часть:
  ✅ /roles — ровно 4 системные роли (Сотрудник/Менеджер/Директор/Администратор)
  ✅ Старые роли (Юрист/Финансист/Кадровик/HR) отсутствуют в /members
  ✅ Каждая системная роль имеет лейбл "Системная"

CRUD часть (creates_data, заморожена пока — TODO для разморозки):
  ⏳ Default role нового сотрудника = "Сотрудник" (BRD §2.3 правило 1)
  ⏳ Только Admin может назначить Director/Manager/Admin (правило 2)
  ⏳ Last Administrator не удаляется (правило 3)
  ⏳ Permission enforcement: каждая роль видит свой набор sidebar пунктов
  ⏳ Прямой URL под не-Admin → 403/redirect (BUG-011 регрессия)

Связь с другими тестами:
  - test_finansist_cannot_access_*_directly (test_rbac.py) — устарели,
    роли FINANSIST больше нет. После migrations переписать на
    Сотрудник/Менеджер/Директор.
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings

SYSTEM_ROLES: tuple[str, ...] = (
    "Сотрудник",
    "Менеджер",
    "Директор",
    "Администратор",
)

# Старые роли которые ДОЛЖНЫ быть мигрированы (по AC задачи)
LEGACY_ROLES: tuple[object, ...] = (
    "Юрист",
    "Финансист",
    pytest.param(
        "Кадровик",
        marks=pytest.mark.xfail(
            reason="Open data-migration bug: dev /members всё ещё содержит legacy role 'Кадровик'",
            strict=True,
        ),
    ),
    "Бухгалтер",
    "HR",
    "FINANSIST",
    "LAWYER",
)


# ============================================================
# Read-only checks (выполняются на каждом регрессионном прогоне)
# ============================================================


@pytest.mark.regression
@pytest.mark.positive
@allure.title("BHUB-roles: /roles содержит 4 системные роли (BRD §2.3)")
@pytest.mark.parametrize("role_name", SYSTEM_ROLES)
def test_system_roles_present_in_roles_page(
    client_admin_page: Page, settings: Settings, role_name: str
) -> None:
    """Все 4 системные роли (Сотрудник/Менеджер/Директор/Администратор)
    должны присутствовать в /roles с лейблом "Системная"."""
    page = client_admin_page
    page.goto(f"{settings.client_url}/roles", wait_until="networkidle")
    expect(page.get_by_role("heading", name="Роли и права", level=4)).to_be_visible(
        timeout=settings.expect_timeout
    )
    row = page.get_by_role("row").filter(has_text=role_name).first
    expect(row).to_be_visible(timeout=settings.expect_timeout)
    # На системной роли должен быть лейбл "Системная"
    expect(row.get_by_text("Системная")).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
@allure.title("BHUB-roles: старые роли (Юрист/Финансист/Кадровик) удалены")
@pytest.mark.parametrize("legacy_role", LEGACY_ROLES)
def test_legacy_roles_not_in_members_table(
    client_admin_page: Page, settings: Settings, legacy_role: str
) -> None:
    """После DB migration старые роли не должны встречаться ни у одного
    юзера в /members. Проверяем поиском — счётчик 0."""
    page = client_admin_page
    page.goto(
        f"{settings.client_url}/members?page=1&size=100&search=",
        wait_until="networkidle",
    )
    table = page.get_by_role("table").first
    expect(table).to_be_visible(timeout=settings.expect_timeout)
    # Exact-match cell в колонке "Роль". `has_text` ловит подстроку
    # ("HR" совпадал бы например с "iconHR-svg" — был flake-баг), поэтому
    # ищем cell с точным текстом legacy_role.
    legacy_cells = table.get_by_role("cell", name=legacy_role, exact=True)
    assert legacy_cells.count() == 0, (
        f"Найдены {legacy_cells.count()} cell'ов со старой ролью {legacy_role!r} — "
        "миграция не прошла. BRD §2.3 требует Сотрудник."
    )


@pytest.mark.regression
@pytest.mark.positive
@allure.title("BHUB-roles: системных ролей ровно 4 (никто не добавил пятую)")
def test_exactly_four_system_roles(
    client_admin_page: Page, settings: Settings
) -> None:
    """В /roles должно быть ровно 4 строки с лейблом 'Системная'.
    Если кто-то добавит 5-ю системную (Бухгалтер обратно) — заметим.
    Кастомные ('Пользовательская') не считаем.
    """
    page = client_admin_page
    page.goto(f"{settings.client_url}/roles", wait_until="networkidle")
    table = page.get_by_role("table").first
    expect(table).to_be_visible(timeout=settings.expect_timeout)
    system_rows = table.get_by_role("row").filter(has_text="Системная")
    assert system_rows.count() == 4, (
        f"Ожидали ровно 4 системные роли, найдено {system_rows.count()}. "
        f"BRD §2.3 — Сотрудник/Менеджер/Директор/Администратор."
    )


@pytest.mark.regression
@pytest.mark.positive
@allure.title("BHUB-roles: Администратор имеет максимальный набор permissions")
def test_administrator_has_full_permissions(
    client_admin_page: Page, settings: Settings
) -> None:
    """В таблице ролей рядом с Администратором должны быть все домены:
    Документооборот, Кадры, Финансы, Настройки. Это контраст с другими
    ролями (Менеджер не видит Финансы, Директор — большинство; Сотрудник
    — только базовое)."""
    page = client_admin_page
    page.goto(f"{settings.client_url}/roles", wait_until="networkidle")
    table = page.get_by_role("table").first
    admin_row = table.get_by_role("row").filter(has_text="Администратор").first
    expect(admin_row).to_be_visible(timeout=settings.expect_timeout)
    # У Администратора все 4 домена должны упоминаться
    for domain in ("Документооборот", "Кадры", "Финансы", "Настройки"):
        expect(admin_row).to_contain_text(domain)


# ============================================================
# CRUD checks (creates_data — заморожены до разморозки и фикса BUG-016)
# ============================================================


pytestmark_crud = [pytest.mark.creates_data, pytest.mark.skip(
    reason="CRUD-тесты ролей заморожены: (1) creates_data, (2) BUG-016 "
    "Admin auth блокер. Разморозить когда: A) появится maintenance "
    "cleanup; B) починят BUG-016 либо дадут [E2E] non-admin тестовые "
    "телефоны для permission-проверок без impersonation."
)]


@pytest.mark.creates_data
@pytest.mark.skip(reason="См. pytestmark_crud (creates_data + BUG-016)")
@allure.title("BHUB-roles: новый сотрудник без указания роли получает 'Сотрудник'")
def test_new_member_default_role_is_employee() -> None:
    """BRD §2.3 правило 1: default role = Сотрудник для всех новых.

    План:
      1. Открыть /members → "Добавить сотрудника"
      2. Заполнить только обязательные поля БЕЗ выбора роли
      3. Submit
      4. Найти созданного юзера в списке → колонка "Роль" = "Сотрудник"
    """
    raise NotImplementedError("Заготовка — реализовать после разморозки CRUD")


@pytest.mark.creates_data
@pytest.mark.skip(reason="См. pytestmark_crud")
@allure.title("BHUB-roles: только Admin может назначить Director/Manager/Admin")
def test_only_admin_can_assign_director_manager_admin() -> None:
    """BRD §2.3 правило 2.

    План:
      1. Залогиниться как Менеджер (test phone TBD)
      2. Открыть /members → попробовать создать юзера с ролью Директор
         → option должен быть disabled / отсутствовать
      3. Залогиниться как Администратор → option доступен
    """
    raise NotImplementedError


@pytest.mark.creates_data
@pytest.mark.skip(reason="ОПАСНО — может разрушить стенд. См. pytestmark_crud")
@allure.title("BHUB-roles: нельзя удалить последнего Администратора")
def test_cannot_remove_last_administrator() -> None:
    """BRD §2.3 правило 3.

    ВНИМАНИЕ: тест опасный — если backend bug, мы реально удалим всех
    админов и stenstd сломается. Делать ТОЛЬКО на изолированной test-org
    (созданной фикстурой mock1c_company). Никогда — на main TeamQa.

    План:
      1. Создать орг через mock1c_company (1 admin внутри по факту)
      2. Войти этим admin'ом
      3. Попробовать сделать себе disable / поменять роль на Сотрудник
      4. Backend должен вернуть 4xx + UI alert
    """
    raise NotImplementedError


@pytest.mark.creates_data
@pytest.mark.skip(reason="См. pytestmark_crud")
@allure.title("BHUB-roles: каждая роль видит свой набор sidebar пунктов")
def test_sidebar_visibility_per_role() -> None:
    """BRD §2.3 + §3.5 permission matrix.

    План (parametrize по 4 ролям):
      - Сотрудник: только Inbox, Мои документы, Шаблоны
      - Менеджер: + Оргструктура (без Финансов)
      - Директор: + видит всё кроме Настроек
      - Администратор: всё
    """
    raise NotImplementedError


@pytest.mark.creates_data
@pytest.mark.skip(reason="См. pytestmark_crud + BUG-011 ещё не пофиксен")
@allure.title("BHUB-roles: прямой URL под не-Admin → 403/redirect (BUG-011)")
def test_non_admin_direct_url_blocked() -> None:
    """Регрессия BUG-011: Сотрудник/Менеджер/Директор не должны открывать
    /integration / /roles / /members по прямой ссылке без меню.
    """
    raise NotImplementedError
