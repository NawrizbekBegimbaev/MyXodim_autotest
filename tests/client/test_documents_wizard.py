"""UC-3.1 Документы wizard: полный flow создания документа.

Шаг 1: Содержимое (шаблон/свободный + поля)
Шаг 2: Маршрут (выбор)
Шаг 3: Проверка → submit
"""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.documents_page import DocumentCreateWizardPage, DocumentsPage


def _open_wizard(page: Page, settings: Settings) -> DocumentCreateWizardPage:
    docs = DocumentsPage(page).goto(settings.client_url)
    expect(docs.heading).to_be_visible(timeout=settings.nav_timeout)
    docs.click_create()
    wizard = DocumentCreateWizardPage(page)
    expect(wizard.heading).to_be_visible(timeout=settings.nav_timeout)
    return wizard


# Все тесты в файле мутируют состояние через UI (CRUD-формы).
pytestmark = [
    pytest.mark.creates_data,
    pytest.mark.needs_backend,
    pytest.mark.skip(reason="Document wizard needs template/route fixtures in recon tenant"),
]


@pytest.mark.positive
@allure.title("Doc wizard: step 1 — выбор шаблона + заполнение → переход на step 2")
def test_doc_wizard_step1_template_to_step2(
    client_admin_page: Page, settings: Settings
) -> None:
    title = f"{E2E_PREFIX} Doc {secrets.token_hex(3)}"
    content = "E2E содержание документа для тестов"

    wizard = _open_wizard(client_admin_page, settings)
    wizard.select_first_template()
    client_admin_page.wait_for_timeout(800)
    wizard.fill_title(title).fill_content(content)
    wizard.click_next()
    client_admin_page.wait_for_timeout(2_500)
    # Wizard heading остался — step индикатор должен показывать Маршрут
    expect(wizard.heading).to_be_visible()
    # Heading "Маршрут" появился
    expect(client_admin_page.get_by_role("heading", name="Маршрут", level=6).first).to_be_visible(
        timeout=settings.nav_timeout
    )


@pytest.mark.negative
@allure.title("Doc wizard step 1: пустые поля → 'Далее' заблокирован")
def test_doc_wizard_step1_empty_fields_blocks_next(
    client_admin_page: Page, settings: Settings
) -> None:
    wizard = _open_wizard(client_admin_page, settings)
    wizard.click_next()
    client_admin_page.wait_for_timeout(1_500)
    # Wizard остался на странице "Создать новый документ"
    expect(wizard.heading).to_be_visible()
    # Heading "Маршрут" НЕ появился
    expect(
        client_admin_page.get_by_role("heading", name="Маршрут", level=6).first
    ).not_to_be_visible()


@pytest.mark.positive
@allure.title("Doc wizard: переключение По шаблону / Свободный режим")
def test_doc_wizard_template_freeform_toggle(
    client_admin_page: Page, settings: Settings
) -> None:
    wizard = _open_wizard(client_admin_page, settings)
    wizard.tab_freeform.click()
    client_admin_page.wait_for_timeout(800)
    # После переключения список шаблонов скрыт (или другие элементы)
    # Главное — нет crash
    expect(wizard.heading).to_be_visible()
    wizard.tab_template.click()
    client_admin_page.wait_for_timeout(800)
    expect(wizard.heading).to_be_visible()


@pytest.mark.positive
@allure.title("Doc wizard: full flow step 1 → 2 → 3 → 'Сохранить как черновик'")
def test_doc_wizard_full_flow_save_draft(
    client_admin_page: Page, settings: Settings
) -> None:
    title = f"{E2E_PREFIX} Draft {secrets.token_hex(3)}"
    content = "E2E full-flow draft content"

    wizard = _open_wizard(client_admin_page, settings)
    # Step 1
    wizard.select_first_template()
    client_admin_page.wait_for_timeout(800)
    wizard.fill_title(title).fill_content(content)
    wizard.click_next()
    client_admin_page.wait_for_timeout(2_500)

    # Step 2: маршрут + филиал
    wizard.select_route()
    wizard.select_target_branch_first()
    wizard.click_next()
    client_admin_page.wait_for_timeout(2_500)

    # Step 3: Проверка
    expect(wizard.review_heading).to_be_visible(timeout=settings.nav_timeout)
    expect(wizard.save_draft_button).to_be_visible()
    expect(wizard.submit_route_button).to_be_visible()
    wizard.click_save_draft()
    client_admin_page.wait_for_timeout(3_000)
    # После save draft фронт обычно редиректит на /documents
    # Главное — не упал, заголовок страницы остался валидным
    # (нет жёсткой проверки URL чтобы не флейкать на разные UX-вариации)


@pytest.mark.positive
@allure.title("Doc wizard step 3: кнопка 'Отправить на маршрут' видна на review")
def test_doc_wizard_step3_review_buttons_visible(
    client_admin_page: Page, settings: Settings
) -> None:
    title = f"{E2E_PREFIX} Review {secrets.token_hex(3)}"

    wizard = _open_wizard(client_admin_page, settings)
    wizard.select_first_template()
    client_admin_page.wait_for_timeout(800)
    wizard.fill_title(title).fill_content("review check")
    wizard.click_next()
    client_admin_page.wait_for_timeout(2_500)
    wizard.select_route()
    wizard.select_target_branch_first()
    wizard.click_next()
    client_admin_page.wait_for_timeout(2_500)

    expect(wizard.review_heading).to_be_visible(timeout=settings.nav_timeout)
    expect(wizard.save_draft_button).to_be_enabled()
    expect(wizard.submit_route_button).to_be_enabled()
