"""BRD 3.0 §25 — Виды документов для согласования (/document-types).

Покрытие:
- Smoke: страница открывается, heading/кнопка/таблица/фильтры на месте.
- Positive: search принимает ввод, клик "Создать" → /document-types/create
  с полями (name, group, prefix, флаги), форма имеет Save/Cancel.
- Negative: empty submit → "Наименование обязательно", страница не уходит.
- Связь с Routes (BRD §27): см. tests/client/test_routes.py — поле
  "Группы видов документов *" есть в Route Builder.
- Skipped: actual persist create — recon-tenant имеет уже 1 вид
  (ReconTemplate 0519), создание нового мутирует tenant и без maintenance-чистки
  не желательно в CI; раскомментировать когда появится cleanup endpoint.

POM: pages.client.document_types_page (DocumentTypesPage, DocumentTypeCreatePage).
"""

from __future__ import annotations

import re
import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from data.i18n import t
from pages.client.document_types_page import (
    DocumentTypeCreatePage,
    DocumentTypesPage,
)


def _open(page: Page, settings: Settings) -> DocumentTypesPage:
    pg = DocumentTypesPage(page).goto(settings.client_url)
    expect(pg.heading).to_be_visible(timeout=settings.nav_timeout)
    return pg


def _open_create(page: Page, settings: Settings) -> DocumentTypeCreatePage:
    pg = _open(page, settings)
    pg.click_add()
    create = DocumentTypeCreatePage(page)
    expect(create.heading).to_be_visible(timeout=settings.nav_timeout)
    return create


def _fresh_name(prefix: str = "DocType") -> str:
    return f"{E2E_PREFIX} {prefix} {secrets.token_hex(3)}"


# ---------- Smoke (read-only) ----------


@pytest.mark.smoke
@allure.title("DocTypes smoke: страница /document-types открывается админом")
def test_doc_types_page_opens_for_admin(
    client_admin_page: Page, settings: Settings
) -> None:
    """BRD 3.0 §25: раздел "Виды документов для согласования" доступен админу."""
    pg = _open(client_admin_page, settings)
    expect(pg.heading).to_be_visible()
    expect(pg.add_button).to_be_visible()


@pytest.mark.smoke
@allure.title("DocTypes smoke: heading h4 'Виды документов для согласования'")
def test_doc_types_has_expected_heading(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    expect(pg.heading).to_have_text(t("client.doc_types.title"))


@pytest.mark.smoke
@allure.title("DocTypes smoke: таблица содержит все 5 колонок BRD 3.0")
def test_doc_types_table_has_all_columns(
    client_admin_page: Page, settings: Settings
) -> None:
    """Recon 2026-05-26: колонки Файл/Наименование/Префикс/QR код/Загрузка файлов."""
    pg = _open(client_admin_page, settings)
    expect(pg.table).to_be_visible(timeout=settings.expect_timeout)
    for col in DocumentTypesPage.COLUMNS:
        expect(pg.column_header(col)).to_be_visible()


@pytest.mark.smoke
@allure.title("DocTypes smoke: 3 фильтра (QR/Файлы/Шаблон) видны с дефолтом 'Все'")
def test_doc_types_filters_visible(
    client_admin_page: Page, settings: Settings
) -> None:
    """Recon 2026-05-26: дефолтные значения комбобоксов = "Все"."""
    pg = _open(client_admin_page, settings)
    expect(pg.filter_combobox(t("client.doc_types.filter_qr"))).to_be_visible()
    expect(pg.filter_combobox(t("client.doc_types.filter_files"))).to_be_visible()
    expect(pg.filter_combobox(t("client.doc_types.filter_template"))).to_be_visible()


@pytest.mark.smoke
@allure.title("DocTypes smoke: кнопка 'Сбросить' фильтры присутствует (disabled на дефолте)")
def test_doc_types_reset_button_present(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    expect(pg.reset_filters_button).to_be_visible()
    # На дефолте disabled — фильтры не изменены, нечего сбрасывать.
    expect(pg.reset_filters_button).to_be_disabled()


# ---------- Positive (read-only) ----------


@pytest.mark.positive
@allure.title("DocTypes: search-инпут принимает ввод без падения UI")
def test_doc_types_search_input_accepts_text(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    pg.search("zzz-no-match-xyz")
    expect(pg.heading).to_be_visible()


@pytest.mark.positive
@allure.title("DocTypes: клик 'Создать' → переход на /document-types/create")
def test_doc_types_create_navigates_to_create_page(
    client_admin_page: Page, settings: Settings
) -> None:
    """BRD 3.0 §25: создание Вида — отдельная страница, не диалог."""
    create = _open_create(client_admin_page, settings)
    expect(create.heading).to_be_visible()
    expect(client_admin_page).to_have_url(re.compile(r"/document-types/create"))


@pytest.mark.positive
@allure.title("DocTypes create page: все поля и кнопки видны")
def test_doc_types_create_page_has_all_fields(
    client_admin_page: Page, settings: Settings
) -> None:
    """Recon 2026-05-26: name, group, prefix (+ helper-text), 2 чекбокса, Save/Cancel."""
    create = _open_create(client_admin_page, settings)
    expect(create.name_input).to_be_visible()
    expect(create.group_combobox).to_be_visible()
    expect(create.prefix_input).to_be_visible()
    expect(create.prefix_helper).to_be_visible()
    expect(create.qr_checkbox).to_be_visible()
    expect(create.files_checkbox).to_be_visible()
    expect(create.submit_button).to_be_visible()
    expect(create.cancel_button).to_be_visible()


@pytest.mark.positive
@allure.title("DocTypes create: чекбоксы QR/Файлы по умолчанию unchecked")
def test_doc_types_checkboxes_default_unchecked(
    client_admin_page: Page, settings: Settings
) -> None:
    create = _open_create(client_admin_page, settings)
    expect(create.qr_checkbox).not_to_be_checked()
    expect(create.files_checkbox).not_to_be_checked()


@pytest.mark.positive
@allure.title("DocTypes create: Cancel → возврат на /document-types")
def test_doc_types_create_cancel_returns_to_list(
    client_admin_page: Page, settings: Settings
) -> None:
    create = _open_create(client_admin_page, settings)
    create.cancel()
    pg = DocumentTypesPage(client_admin_page)
    expect(pg.heading).to_be_visible(timeout=settings.expect_timeout)


# ---------- Negative ----------


@pytest.mark.negative
@allure.title("DocTypes neg: empty name submit → 'Наименование обязательно'")
def test_doc_types_create_empty_name_shows_validation_error(
    client_admin_page: Page, settings: Settings
) -> None:
    """Recon 2026-05-26: helper-text "Наименование обязательно" (НЕ "Введите
    название" как в groups — два разных сообщения для одного по сути типа
    валидации; BUG-кандидат на consistency).
    """
    create = _open_create(client_admin_page, settings)
    create.submit()
    # Страница не ушла на список.
    expect(create.heading).to_be_visible()
    # Helper "Наименование обязательно".
    expect(create.error_name_required).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.negative
@allure.title("DocTypes neg: group combobox пуст ('No options') на чистом tenant")
def test_doc_types_group_combobox_no_options_when_no_groups(
    client_admin_page: Page, settings: Settings
) -> None:
    """Recon 2026-05-26: tenant без групп → MUI Autocomplete показывает "No options".

    Это не баг, а ожидаемый empty state. Тест защищает что combobox реагирует
    на клик (open) и popup рендерится.
    """
    create = _open_create(client_admin_page, settings)
    create.open_group_combobox()
    expect(create.group_combobox_no_options).to_be_visible(
        timeout=settings.expect_timeout
    )


# ---------- BLOCKED / SKIP ----------


@pytest.mark.skip(
    reason="BLOCKED: actual create persist изменяет tenant state (1 → 2 видов). "
    "На recon-tenant'е накопление E2E-данных нежелательно без maintenance-чистки. "
    "Раскомментировать когда появится cleanup-задача или dedicated provisioning."
)
@pytest.mark.creates_data
@pytest.mark.positive
@allure.title("DocTypes: создание Вида → строка появляется в таблице")
def test_doc_types_create_persists_in_table(
    client_admin_page: Page, settings: Settings
) -> None:
    """BRD 3.0 §25 US-1: после Save Вид виден в таблице /document-types."""
    name = _fresh_name()
    create = _open_create(client_admin_page, settings)
    create.fill_name(name).submit()
    pg = DocumentTypesPage(client_admin_page)
    expect(pg.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(pg.row_by_name(name)).to_be_visible(timeout=settings.nav_timeout)


@pytest.mark.skip(
    reason="BLOCKED: positive create-with-group тест требует существующей группы "
    "в tenant; recon-tenant 0 групп ('No options'). Включить когда появится "
    "session-фикстура `recon_group` (сидится через Mock 1C или admin UI)."
)
@pytest.mark.creates_data
@pytest.mark.positive
@allure.title("DocTypes: создание Вида с привязкой к Группе")
def test_doc_types_create_with_group_binding(
    client_admin_page: Page, settings: Settings
) -> None:
    """BRD 3.0 §25/§26: Вид может принадлежать Группе (FK на documentGroup)."""
    pytest.skip("Требует существующей Группы в tenant.")


@pytest.mark.skip(
    reason="BUG-кандидат на consistency: /document-groups показывает 'Введите "
    "название', /document-types — 'Наименование обязательно' (одинаковый по "
    "смыслу validation, разные тексты). Включить regression-тест когда фронт "
    "унифицирует сообщение."
)
@pytest.mark.regression
@allure.title("DocTypes regression: validation message consistency с DocGroups")
def test_doc_types_validation_message_matches_doc_groups(
    client_admin_page: Page, settings: Settings
) -> None:
    """Когда фронт унифицирует тексты — этот тест задокументирует ожидаемое
    единое сообщение и предохранит от дрейфа.
    """
    pytest.skip("UI ещё не унифицирован.")


@pytest.mark.skip(
    reason="BLOCKED: уникальность префикса (BRD §25) — нечего тестировать без "
    "существующего префикса и POST для создания дубликата. См. test "
    "test_doc_types_create_persists_in_table выше."
)
@pytest.mark.negative
@allure.title("DocTypes neg: дубликат префикса → ошибка валидации")
def test_doc_types_duplicate_prefix_rejected(
    client_admin_page: Page, settings: Settings
) -> None:
    """BRD 3.0 §25: префикс должен быть уникальным внутри tenant."""
    pytest.skip("Требует working create-flow.")
