"""UC-3.6 negative + boundary создания сотрудника в Client UI.

Bg-009: фронт молчит на 409 → проверяем что диалог не закрылся (success).
"""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Dialog, Page, expect

from config.settings import Settings
from data import phone_pool
from pages.client.member_create_dialog import MemberCreateDialog
from pages.client.members_page import MembersPage


def _open_create_dialog(
    client_admin_page: Page, settings: Settings
) -> tuple[MembersPage, MemberCreateDialog]:
    members = MembersPage(client_admin_page).goto(settings.client_url)
    members.click_add()
    dialog = MemberCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    return members, dialog


def _expect_dialog_stays(dialog: MemberCreateDialog, settings: Settings) -> None:
    """После submit диалог НЕ закрылся — фронт получил ошибку (или валидация заблокировала)."""
    dialog.page.wait_for_timeout(2_500)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.negative
@allure.title("UC-3.6 neg: дубль телефона → 409, диалог остаётся + error отображается")
def test_member_create_with_duplicate_phone_shows_error(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    """Бэк возвращает 409 MEMBER_PHONE_DUPLICATE. После фикса BUG-009 фронт
    показывает пользователю сообщение об ошибке.
    """
    members, dialog = _open_create_dialog(client_admin_page, settings)
    phone = random_test_phone
    suffix = secrets.token_hex(3)
    dialog.fill_required(
        first_name="Якорь",
        last_name=f"[E2E] Anchor {suffix}",
        phone=phone,
        role="Сотрудник",
    )
    dialog.submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)

    # Второй create с дубль-телефоном
    members.click_add()
    dialog2 = MemberCreateDialog(client_admin_page)
    expect(dialog2.dialog).to_be_visible()
    dialog2.fill_required(
        first_name="Дубль",
        last_name=f"[E2E] Dup {suffix}",
        phone=phone,
        role="Администратор",
    )
    dialog2.submit()
    _expect_dialog_stays(dialog2, settings)
    # После фикса BUG-009 фронт показывает error на странице
    body = client_admin_page.locator("body").inner_text()
    assert (
        "уже" in body.lower() or "дубл" in body.lower() or "сущест" in body.lower()
    ), f"Ожидали сообщение об ошибке дубля, но в body нет таких слов. Фрагмент: {body[:400]}"


@pytest.mark.negative
@allure.title("UC-3.6 neg: пустые обязательные поля → submit заблокирован, диалог открыт")
def test_member_create_with_empty_required_fields_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    _, dialog = _open_create_dialog(client_admin_page, settings)
    # ничего не заполняем
    dialog.submit()
    _expect_dialog_stays(dialog, settings)


@pytest.mark.negative
@allure.title("UC-3.6 neg: телефон без +998 префикса → диалог остаётся")
def test_member_create_with_phone_without_prefix_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    _, dialog = _open_create_dialog(client_admin_page, settings)
    dialog.fill_required(
        first_name="Тест",
        last_name="[E2E] NoPrefix",
        phone="901234567",  # без +998
        role="Сотрудник",
    )
    dialog.submit()
    _expect_dialog_stays(dialog, settings)


@pytest.mark.negative
@pytest.mark.parametrize(
    "phone",
    [
        pytest.param("+998abcdefghi", id="letters"),
        pytest.param("+99812", id="too-short"),
        pytest.param("+998901234567890123", id="too-long"),
    ],
)
@allure.title("UC-3.6 neg phone variant: '{phone}' → диалог остаётся")
def test_member_create_with_invalid_phone_format_stays_on_dialog(
    client_admin_page: Page, settings: Settings, phone: str
) -> None:
    _, dialog = _open_create_dialog(client_admin_page, settings)
    dialog.fill_required(
        first_name="Тест", last_name="[E2E] Phone", phone=phone, role="Сотрудник"
    )
    dialog.submit()
    _expect_dialog_stays(dialog, settings)


@pytest.mark.negative
@allure.title("UC-3.6 neg: роль не выбрана → submit blocked")
def test_member_create_without_role_stays_on_dialog(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    _, dialog = _open_create_dialog(client_admin_page, settings)
    # Заполняем все кроме роли
    dialog._first_name.fill("Тест")
    dialog._last_name.fill("[E2E] NoRole")
    dialog._phone.fill(random_test_phone)
    dialog.submit()
    _expect_dialog_stays(dialog, settings)


@pytest.mark.positive
@allure.title("UC-3.6: Cancel закрывает диалог без создания")
def test_member_create_cancel_closes_dialog_without_creation(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    members, dialog = _open_create_dialog(client_admin_page, settings)
    suffix = secrets.token_hex(3)
    dialog.fill_required(
        first_name="Отменён",
        last_name=f"[E2E] Cancel {suffix}",
        phone=random_test_phone,
        role="Сотрудник",
    )
    dialog.cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    # Сотрудник не создан — поиск по телефону не находит
    members.search(random_test_phone)
    client_admin_page.wait_for_timeout(1_500)
    expect(members.row_by_phone(random_test_phone)).not_to_be_visible()


# ---------- Boundary ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "first_name",
    [
        pytest.param("X" * 500, id="too-long"),
        pytest.param("Имя!@#", id="special-chars"),
        pytest.param("Имя123", id="digits"),
        pytest.param("<script>alert(1)</script>", id="xss-payload"),
    ],
)
@allure.title("UC-3.6 boundary Имя: '{first_name}' → диалог остаётся / без alert")
def test_member_create_first_name_boundary(
    client_admin_page: Page,
    settings: Settings,
    random_test_phone: str,
    first_name: str,
) -> None:
    """Boundary имени. XSS-вариант проверяет что dialog не выполнил скрипт."""
    page = client_admin_page
    dialog_seen: list[str] = []

    def on_dialog(d: Dialog) -> None:
        dialog_seen.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)

    _, dialog = _open_create_dialog(page, settings)
    dialog.fill_required(
        first_name=first_name,
        last_name="[E2E] Boundary",
        phone=random_test_phone,
        role="Сотрудник",
    )
    dialog.submit()
    page.wait_for_timeout(2_000)
    # Главное — XSS не выполнился; success/fail не критичен
    assert dialog_seen == [], f"XSS payload вызвал dialog: {dialog_seen}"


@pytest.mark.positive
@allure.title("UC-3.6: создание с разными ролями (parametrize)")
@pytest.mark.parametrize(
    "role",
    [
        pytest.param("Сотрудник", id="employee"),
        pytest.param("Администратор", id="administrator"),
    ],
)
def test_member_create_with_different_roles_succeeds(
    client_admin_page: Page,
    settings: Settings,
    role: str,
) -> None:
    """Создаём сотрудника с указанной ролью, ожидаем success (диалог закрылся)."""
    phone = phone_pool.random_test_phone()
    suffix = secrets.token_hex(3)
    members, dialog = _open_create_dialog(client_admin_page, settings)
    dialog.fill_required(
        first_name="Роль",
        last_name=f"[E2E] {role} {suffix}",
        phone=phone,
        role=role,
    )
    dialog.submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    # Видна в списке
    members.search(phone)
    expect(members.row_by_phone(phone)).to_be_visible(timeout=settings.expect_timeout)
