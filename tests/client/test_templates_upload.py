"""Templates step 2: загрузка PDF / Пропустить."""

from __future__ import annotations

import secrets
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.templates_page import (
    TemplateCreateDialog,
    TemplatesPage,
    TemplateUploadDialog,
)


def _open_create(page: Page, settings: Settings) -> TemplateCreateDialog:
    tp = TemplatesPage(page).goto(settings.client_url)
    expect(tp.heading).to_be_visible(timeout=settings.nav_timeout)
    tp.click_add()
    dialog = TemplateCreateDialog(page)
    expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)
    return dialog


def _fresh_title() -> str:
    return f"{E2E_PREFIX} Tmpl {secrets.token_hex(3)}"


@pytest.mark.positive
@allure.title("Templates step 2: 'Пропустить' закрывает upload-диалог")
def test_template_upload_skip_closes_dialog(
    client_admin_page: Page, settings: Settings
) -> None:
    title = _fresh_title()
    create = _open_create(client_admin_page, settings)
    create.fill_title(title).submit()
    upload = TemplateUploadDialog(client_admin_page)
    expect(upload.dialog).to_be_visible(timeout=settings.nav_timeout)
    expect(upload.skip_button).to_be_visible()
    upload.click_skip()
    expect(upload.dialog).to_be_hidden(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Templates step 2: загрузка PDF активирует кнопку 'Завершить'")
def test_template_upload_pdf_enables_finish(
    client_admin_page: Page, settings: Settings
) -> None:
    pdf_path = Path(__file__).parent.parent.parent / "data" / "test_files" / "sample.pdf"
    assert pdf_path.exists(), f"Test PDF не найден: {pdf_path}"

    title = _fresh_title()
    create = _open_create(client_admin_page, settings)
    create.fill_title(title).submit()
    upload = TemplateUploadDialog(client_admin_page)
    expect(upload.dialog).to_be_visible(timeout=settings.nav_timeout)
    expect(upload.finish_button).to_be_disabled()
    upload.upload_file(str(pdf_path))
    client_admin_page.wait_for_timeout(2_000)
    # После загрузки кнопка должна стать enabled
    expect(upload.finish_button).to_be_enabled(timeout=settings.expect_timeout)
    # Не идём в submit — оставляем шаблон без обязательного завершения
    upload.click_skip()
    expect(upload.dialog).to_be_hidden(timeout=settings.expect_timeout)
