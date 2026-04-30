"""Шаблоны /templates — Step 1 (имя). Загрузка PDF в отдельном dialog'е не тестируется."""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.templates_page import TemplateCreateDialog, TemplatesPage


def _open(page: Page, settings: Settings) -> TemplatesPage:
    tp = TemplatesPage(page).goto(settings.client_url)
    expect(tp.heading).to_be_visible(timeout=settings.nav_timeout)
    return tp


def _fresh_title() -> str:
    return f"{E2E_PREFIX} Tmpl {secrets.token_hex(3)}"


@pytest.mark.positive
@allure.title("Templates: первый этап (имя) → открывается следующий dialog (PDF upload)")
def test_template_create_name_opens_next_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    """После submit имени dialog "Добавить шаблон" должен закрыться,
    и (в идеале) откроется PDF upload — но мы не идём дальше step 1.
    """
    title = _fresh_title()
    tp = _open(client_admin_page, settings)
    tp.click_add()
    dialog = TemplateCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.fill_title(title).submit()
    # Шаг 1 dialog закрылся (либо переход в step 2)
    expect(dialog.dialog).to_be_hidden(timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("Templates: Cancel закрывает диалог без создания")
def test_template_create_cancel_closes_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title()
    tp = _open(client_admin_page, settings)
    tp.click_add()
    dialog = TemplateCreateDialog(client_admin_page)
    dialog.fill_title(title).cancel()
    expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)


@pytest.mark.negative
@allure.title("Templates neg: пустое название → диалог остаётся")
def test_template_create_empty_title_stays_on_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    tp = _open(client_admin_page, settings)
    tp.click_add()
    dialog = TemplateCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    dialog.submit()
    client_admin_page.wait_for_timeout(2_000)
    expect(dialog.dialog).to_be_visible()
