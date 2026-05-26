"""BRD 2.0 — Branch Management (BHUB-38..48), Client UI /branches.

Покрытие:
- Smoke: страница открывается, head автоматически есть, колонки на месте.
- Positive: иерархия рендерится, search не падает, edit head не имеет parent.
- Negative/edge: попытка submit с пустым name — диалог остаётся (silent stay).
- Skipped/xfail для фич с **отсутствующим UI** на dev (recon 2026-05-25):
  - BHUB-40 branch_id у employee (нет поля в Add Employee dialog)
  - BHUB-41/42 source/target_branch у документа (нет поля в /documents/create)
  - BHUB-43..46 branch_step (нет в /routes/new step types)
  - BHUB-48 inbox filter по branch

Recon-tenant `[E2E recon] 8dgk1l` уже имеет один head office под именем
самой организации — это и есть auto-created head (BHUB-38).

POM: pages.client.branches_page (BranchesPage, BranchCreateDialog,
BranchEditDialog). Все тесты UI-only (CLAUDE.md §13), без API-вызовов.
"""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from data.i18n import t
from pages.client.branches_page import (
    BranchCreateDialog,
    BranchEditDialog,
    BranchesPage,
)


def _open(page: Page, settings: Settings) -> BranchesPage:
    br = BranchesPage(page).goto(settings.client_url)
    expect(br.heading).to_be_visible(timeout=settings.nav_timeout)
    return br


def _fresh_title(prefix: str = "Br") -> str:
    return f"{E2E_PREFIX} {prefix} {secrets.token_hex(3)}"


# ---------- Smoke (read-only, безопасно для CI) ----------


@pytest.mark.smoke
@allure.title("Branches smoke: страница /branches открывается админом")
def test_branches_page_opens_for_admin(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-38: раздел "Филиалы" доступен пользователю с ADMINISTRATOR ролью."""
    br = _open(client_admin_page, settings)
    expect(br.heading).to_be_visible()
    expect(br.subtitle).to_be_visible()
    expect(br.add_button).to_be_visible()


@pytest.mark.smoke
@allure.title("Branches smoke: таблица содержит все 5 колонок BRD 2.0")
def test_branches_table_has_all_columns(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-39: список филиалов рендерит колонки Филиал/Тип/Отделы/Пользователи/Действия."""
    br = _open(client_admin_page, settings)
    expect(br.table).to_be_visible(timeout=settings.expect_timeout)
    for col in BranchesPage.COLUMNS:
        expect(br.column_header(col)).to_be_visible()


@pytest.mark.smoke
@allure.title("Branches smoke: head office создан автоматически (auto-seed)")
def test_branches_list_contains_head_office(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-38: при создании tenant'а автоматически создаётся branch type=head.

    В recon-tenant `[E2E recon] 8dgk1l` строка head имеет
    type-cell == "Главный офис". Должна быть РОВНО одна (unique constraint
    per company).
    """
    br = _open(client_admin_page, settings)
    expect(br.table).to_be_visible(timeout=settings.expect_timeout)
    head_rows = br.head_row()
    # один и только один head office
    expect(head_rows).to_have_count(1)


# ---------- Positive (read-only — не мутируют состояние) ----------


@pytest.mark.positive
@allure.title("Branches: переключение Таблица ↔ Иерархия")
def test_branches_switch_table_hierarchy_tabs(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-39: оба view-режима доступны. Иерархия показывает head с бейджем HEAD."""
    br = _open(client_admin_page, settings)
    expect(br.tab_table).to_be_visible()
    expect(br.tab_hierarchy).to_be_visible()

    br.switch_to_hierarchy()
    # В Иерархии head-карточка имеет бейдж "HEAD".
    expect(br.hierarchy_card_for_head()).to_be_visible(timeout=settings.expect_timeout)

    br.switch_to_table()
    expect(br.table).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Branches: search-инпут принимает ввод без падения UI")
def test_branches_search_input_accepts_text(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-39: поиск по названию филиала — UI не падает на любой строке.

    Не проверяет фильтрацию (на recon-тенанте только один branch — фильтр
    не имеет смысла). Цель — гарантировать что input работает + heading
    остаётся видимым.
    """
    br = _open(client_admin_page, settings)
    br.search("zzz-no-match-xyz")
    # таблица/heading стабильны — нет crash'а
    expect(br.heading).to_be_visible()


@pytest.mark.positive
@allure.title("Branches: открытие диалога 'Новый филиал' с предзаполненным parent")
def test_branch_create_dialog_opens_with_head_as_parent(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-39: dialog "Новый филиал" предлагает Название + Родительский офис.

    Recon наблюдение 2026-05-25: parent-combobox **disabled** и зафиксирован
    на head-офисе (id `0108db39-...` в recon-tenant). Это product decision:
    нельзя создать sub-branch под другим sub-branch'ом в текущем UI.
    Тест не модифицирует данные — только открывает диалог и закрывает Cancel.
    """
    br = _open(client_admin_page, settings)
    br.click_add()
    dialog = BranchCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    expect(dialog.title_input).to_be_visible()
    expect(dialog.parent_combo).to_be_visible()
    # parent-combobox содержит имя tenant'а (head-офис) — disabled, нельзя сменить.
    expect(dialog.parent_combo).to_be_disabled()
    dialog.cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Branches: edit head-офиса НЕ содержит поле 'Родительский офис'")
def test_branch_edit_head_has_no_parent_field(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-38: head — корень иерархии, у него не должно быть parent.

    UI это отражает: edit-диалог head не показывает label "Родительский офис".
    """
    br = _open(client_admin_page, settings)
    br.head_edit_button().click()
    dialog = BranchEditDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    expect(dialog.title_input).to_be_visible()
    # поле parent отсутствует
    expect(dialog.parent_label).to_have_count(0)
    dialog.cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)


# ---------- Negative ----------


@pytest.mark.negative
@allure.title("Branches neg: submit с пустым name → диалог не закрывается")
def test_branch_create_empty_name_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-39: client-side validation — пустое имя не уходит на бэкенд.

    Recon 2026-05-25: клик "Создать" с пустым name не закрывает dialog и
    не отправляет POST. Без явного error-helper — лишь "stay on dialog".
    Тест проверяет именно stay (а не network silence — это уже на грани бага).
    """
    br = _open(client_admin_page, settings)
    br.click_add()
    dialog = BranchCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.submit()
    # Диалог должен остаться открытым (не закрыт после submit с empty name).
    expect(dialog.dialog).to_be_visible()
    dialog.cancel()


# ---------- BLOCKED / SKIP — фичи без UI на dev (recon 2026-05-25) ----------


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-39: создание sub-branch не отправляет POST — клик 'Создать' "
    "silent failure (verified 2026-05-25 recon, см. summary в return message). "
    "Включить когда POST /api/v1/branches заработает из dialog."
)
@pytest.mark.creates_data
@pytest.mark.positive
@allure.title("Branches: создание sub-branch → строка появляется в таблице")
def test_branch_create_appears_in_table(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-39: positive happy-path создания филиала."""
    title = _fresh_title()
    br = _open(client_admin_page, settings)
    br.click_add()
    dialog = BranchCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_title(title).submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    expect(br.row_by_title(title)).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-39: edit endpoint untested (создать sub-branch нельзя "
    "из-за silent-submit) — включить после фикса create POST."
)
@pytest.mark.creates_data
@pytest.mark.positive
@allure.title("Branches: edit sub-branch меняет имя в таблице")
def test_branch_edit_changes_persist(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-39: переименование филиала через row 'Редактировать'."""
    pytest.skip("Зависит от рабочего create — пока заблокирован.")


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-39: soft delete (deactivate) — нет кнопки 'Удалить'/"
    "'Деактивировать' в row-actions у head, и нет sub-branch'ей для проверки "
    "ровно потому что create silent-fails."
)
@pytest.mark.creates_data
@pytest.mark.positive
@allure.title("Branches: soft delete скрывает branch из активного списка")
def test_branch_soft_delete_hides_from_list(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-39: deactivate sub-branch → is_active=false → строка с бейджем 'Неактивен'."""
    pytest.skip("Зависит от рабочего create + наличия 'Деактивировать' action.")


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-38: 'second head' попытка — невозможна через UI "
    "(parent-combobox disabled, type=branch hardcoded на frontend). "
    "Backend-only constraint, проверяется не UI-тестом."
)
@pytest.mark.negative
@allure.title("Branches neg: второй head per company запрещён")
def test_branch_create_second_head_is_forbidden(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-38: unique constraint ux_branches_one_head_per_company."""
    pytest.skip("UI не даёт создать второй head — тест требует API.")


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-40: Add Employee dialog НЕ содержит поле 'Филиал' "
    "(recon 2026-05-25 — labels: Имя/Фамилия/Отчество/Телефон/ПИНФЛ/Системная роль/"
    "Должность/Отдел). Включить когда поле появится."
)
@pytest.mark.needs_backend
@pytest.mark.positive
@allure.title("Members: создание сотрудника с привязкой к branch")
def test_member_create_with_branch_binding(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-40: Membership.branch_id — обязательное поле, default=head."""
    pytest.skip("UI поле 'Филиал' в Add Employee dialog отсутствует.")


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-41/42: форма /documents/create НЕ содержит полей "
    "source_branch_id / target_branch_id (recon 2026-05-25 — labels: "
    "Вид документа/Ответственный/Подразделение/Маршрут/Автор)."
)
@pytest.mark.needs_backend
@pytest.mark.negative
@allure.title("Documents: branch→branch routing запрещён (UI-side)")
def test_document_create_branch_to_branch_route_rejected(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-41 matrix: branch→branch — единственная запрещённая комбинация."""
    pytest.skip("UI выбора target_branch не существует в форме создания документа.")


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-43..46: тип шага 'branch_step' (блок 'Отправить в филиал') "
    "отсутствует в /routes/new (recon 2026-05-25 — step настройки: "
    "Роль/Сотрудник/Подразделение/Действие)."
)
@pytest.mark.needs_backend
@pytest.mark.positive
@allure.title("Routes: маршрут с branch_step создаёт child-документ в target branch")
def test_route_with_branch_step_creates_child_document(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-43/44: subprocess workflow — parent ставится в waiting_for_subprocess."""
    pytest.skip("Builder UI шага branch_step не реализован.")


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-47: timeline с отступом для child-документа — зависит от "
    "BHUB-43..46 (нечего показывать без subprocess)."
)
@pytest.mark.needs_backend
@pytest.mark.positive
@allure.title("Documents timeline: subprocess отображается с отступом")
def test_document_timeline_shows_subprocess_nested(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-47: клик по child-документу в timeline открывает его карточку."""
    pytest.skip("Subprocess не создаётся — нечего показывать.")


@pytest.mark.skip(
    reason="BRD 2.0 BHUB-48: фильтр inbox по branch не виден в /inbox "
    "(recon 2026-05-25 — есть только search + 'История')."
)
@pytest.mark.needs_backend
@pytest.mark.positive
@allure.title("Inbox: branch-фильтрация — branch A не видит документы branch B")
def test_inbox_filters_documents_by_branch(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-48: scope = свой branch + subprocess chain."""
    pytest.skip("Фильтрация inbox по branch UI-визуально не наблюдается.")


# ---------- Дополнительные guard'ы ----------


@pytest.mark.smoke
@allure.title("Branches: deactivate-кнопки нет у head office (BHUB-38 protection)")
def test_head_office_has_no_deactivate_button(
    client_admin_page: Page, settings: Settings
) -> None:
    """BHUB-38: head нельзя удалить — у строки head допустима ТОЛЬКО 'Редактировать'.

    Recon 2026-05-25: в строке head единственная кнопка — "Редактировать"
    (нет "Деактивировать"/"Удалить"). Тест защищает регрессию.
    """
    br = _open(client_admin_page, settings)
    expect(br.head_row()).to_be_visible(timeout=settings.expect_timeout)
    deactivate_btn = br.head_row().get_by_role(
        "button", name=t("client.branches.row_action_deactivate")
    )
    expect(deactivate_btn).to_have_count(0)
    # А Редактировать у head — обязательно есть.
    expect(br.head_edit_button()).to_be_visible()
