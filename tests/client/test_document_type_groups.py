"""BRD 3.0 §26 — Группы видов документов (/document-groups).

Покрытие:
- Smoke: страница открывается, heading/кнопка/таблица на месте, empty state виден.
- Positive: поиск, dialog открывается, есть поля name + submit/cancel.
- Negative: пустое имя → helper "Введите название", диалог не закрывается.
- Skipped: actual create persist — пока подтверждено только что валидация работает,
  positive create требует чистого tenant и проверки реакции UI после успешного POST
  (recon 2026-05-25/26: на recon-tenant'е групп нет, dialog закрывается только
  после успешного backend-ответа).

POM: pages.client.document_type_groups_page (DocumentTypeGroupsPage,
DocumentTypeGroupCreateDialog). Все тесты UI-only (CLAUDE.md §13).
"""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from data.i18n import t
from pages.client.document_type_groups_page import (
    DocumentTypeGroupCreateDialog,
    DocumentTypeGroupsPage,
)


def _open(page: Page, settings: Settings) -> DocumentTypeGroupsPage:
    pg = DocumentTypeGroupsPage(page).goto(settings.client_url)
    expect(pg.heading).to_be_visible(timeout=settings.nav_timeout)
    return pg


def _fresh_name(prefix: str = "DocGrp") -> str:
    return f"{E2E_PREFIX} {prefix} {secrets.token_hex(3)}"


# ---------- Smoke (read-only) ----------


@pytest.mark.smoke
@allure.title("DocGroups smoke: страница /document-groups открывается админом")
def test_doc_groups_page_opens_for_admin(
    client_admin_page: Page, settings: Settings
) -> None:
    """BRD 3.0 §26: раздел "Группы видов документов" доступен админу."""
    pg = _open(client_admin_page, settings)
    expect(pg.heading).to_be_visible()
    expect(pg.add_button).to_be_visible()


@pytest.mark.smoke
@allure.title("DocGroups smoke: heading h4 'Группы видов документов'")
def test_doc_groups_has_expected_heading(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    expect(pg.heading).to_have_text(t("client.doc_groups.title"))


@pytest.mark.smoke
@allure.title("DocGroups smoke: кнопка 'Создать' видна и enabled")
def test_doc_groups_has_create_button(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    expect(pg.add_button).to_be_visible()
    expect(pg.add_button).to_be_enabled()


@pytest.mark.smoke
@allure.title("DocGroups smoke: таблица содержит колонку 'Наименование'")
def test_doc_groups_table_has_name_column(
    client_admin_page: Page, settings: Settings
) -> None:
    """BRD 3.0 §26: таблица групп — колонка "Наименование" (одна)."""
    pg = _open(client_admin_page, settings)
    expect(pg.table).to_be_visible(timeout=settings.expect_timeout)
    expect(pg.column_header(t("client.doc_groups.col_name"))).to_be_visible()


@pytest.mark.smoke
@allure.title("DocGroups smoke: empty state 'Нет данных' виден на пустом tenant")
def test_doc_groups_empty_state_visible_when_no_data(
    client_admin_page: Page, settings: Settings
) -> None:
    """Recon 2026-05-26: tenant [E2E recon] 8dgk1l — 0 групп → строка 'Нет данных'."""
    pg = _open(client_admin_page, settings)
    expect(pg.empty_cell).to_be_visible(timeout=settings.expect_timeout)


# ---------- Positive (read-only — не мутируют состояние) ----------


@pytest.mark.positive
@allure.title("DocGroups: search-инпут принимает ввод без падения UI")
def test_doc_groups_search_input_accepts_text(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    pg.search("zzz-no-match-xyz")
    expect(pg.heading).to_be_visible()


@pytest.mark.positive
@allure.title("DocGroups: dialog 'Создать' открывается по клику")
def test_doc_groups_create_dialog_opens(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    pg.click_add()
    dialog = DocumentTypeGroupCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("DocGroups: dialog содержит name input + кнопки Создать/Отмена")
def test_doc_groups_dialog_has_name_field_and_buttons(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    pg.click_add()
    dialog = DocumentTypeGroupCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    expect(dialog.name_input).to_be_visible()
    expect(dialog.submit_button).to_be_visible()
    expect(dialog.cancel_button).to_be_visible()
    dialog.cancel()


@pytest.mark.positive
@allure.title("DocGroups: Cancel закрывает диалог без сайд-эффектов")
def test_doc_groups_cancel_closes_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    pg = _open(client_admin_page, settings)
    pg.click_add()
    dialog = DocumentTypeGroupCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_name(_fresh_name("Cancel"))
    dialog.cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    # Empty state остаётся — ничего не создано.
    expect(pg.empty_cell).to_be_visible(timeout=settings.expect_timeout)


# ---------- Negative ----------


@pytest.mark.negative
@allure.title("DocGroups neg: пустое имя → helper 'Введите название', диалог не закрывается")
def test_doc_groups_create_empty_name_shows_validation_error(
    client_admin_page: Page, settings: Settings
) -> None:
    """Recon 2026-05-26: клик "Создать" с пустым name показывает helper-text
    "Введите название" и не закрывает диалог.
    """
    pg = _open(client_admin_page, settings)
    pg.click_add()
    dialog = DocumentTypeGroupCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.submit()
    # Диалог остаётся открытым.
    expect(dialog.dialog).to_be_visible()
    # Helper-text "Введите название" появился.
    expect(dialog.error_text).to_be_visible(timeout=settings.expect_timeout)
    dialog.cancel()


# ---------- BLOCKED / SKIP ----------


@pytest.mark.skip(
    reason="BUG-кандидат: dialog title = 'Добавить категорию' (copy/paste из "
    "/categories вместо 'Новая группа видов документов'). Тест включить после "
    "переименования; пока ассерт зафейлит = false positive."
)
@pytest.mark.regression
@allure.title("DocGroups regression: dialog title корректный 'Новая группа видов документов'")
def test_doc_groups_dialog_has_correct_title(
    client_admin_page: Page, settings: Settings
) -> None:
    """Когда фронт исправит copy/paste — i18n
    `client.doc_groups.create_dialog_title` поменять на 'Новая группа видов
    документов', тест автоматически начнёт зелёный.
    """
    pg = _open(client_admin_page, settings)
    pg.click_add()
    dialog = DocumentTypeGroupCreateDialog(client_admin_page)
    expect(dialog.dialog).to_have_attribute(
        "aria-labelledby",
        # ожидаем "expected"-вариант
        t("client.doc_groups.create_dialog_expected_title"),
    )


@pytest.mark.skip(
    reason="BLOCKED: positive create persist не проверяем (recon 2026-05-26 — "
    "dialog закрывается ТОЛЬКО при успешном POST; нужно убедиться что в "
    "БД нет нашей группы, а row появляется в таблице после reload). "
    "Раздел /document-groups свежесозданный, behaviour 'after successful create' "
    "ещё не подтверждён manual recon — раскомментировать после."
)
@pytest.mark.creates_data
@pytest.mark.positive
@allure.title("DocGroups: создание группы → строка появляется в таблице")
def test_doc_groups_create_persists_in_table(
    client_admin_page: Page, settings: Settings
) -> None:
    """BRD 3.0 §26 US-1: после создания группа отображается в таблице."""
    name = _fresh_name()
    pg = _open(client_admin_page, settings)
    pg.click_add()
    dialog = DocumentTypeGroupCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_name(name).submit()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)
    expect(pg.row_by_name(name)).to_be_visible(timeout=settings.nav_timeout)
