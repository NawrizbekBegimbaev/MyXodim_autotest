"""UC-3.1 Документы /documents — минимальное покрытие визарда (step 1).

Полный flow создания документа покрывается главным E2E.
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.documents_page import DocumentCreateWizardPage, DocumentsPage


def _open_documents(page: Page, settings: Settings) -> DocumentsPage:
    docs = DocumentsPage(page).goto(settings.client_url)
    expect(docs.heading).to_be_visible(timeout=settings.nav_timeout)
    return docs


@pytest.mark.positive
@allure.title("Documents: главный список открывается + есть кнопка 'Создать документ'")
def test_documents_list_has_create_button(
    client_admin_page: Page, settings: Settings
) -> None:
    docs = _open_documents(client_admin_page, settings)
    expect(docs.create_button).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Documents: 'Создать документ' открывает /documents/create wizard")
def test_documents_create_button_opens_wizard(
    client_admin_page: Page, settings: Settings
) -> None:
    docs = _open_documents(client_admin_page, settings)
    docs.click_create()
    expect(client_admin_page).to_have_url(
        re.compile(r"/documents/create"), timeout=settings.nav_timeout
    )
    wizard = DocumentCreateWizardPage(client_admin_page)
    expect(wizard.heading).to_be_visible(timeout=settings.expect_timeout)


@pytest.mark.positive
@allure.title("Documents wizard: переключатель 'По шаблону' / 'Свободный' кликабелен")
def test_documents_wizard_template_freeform_toggle(
    client_admin_page: Page, settings: Settings
) -> None:
    docs = _open_documents(client_admin_page, settings)
    docs.click_create()
    wizard = DocumentCreateWizardPage(client_admin_page)
    expect(wizard.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(wizard.tab_template).to_be_visible()
    expect(wizard.tab_freeform).to_be_visible()
    wizard.tab_freeform.click()
    wizard.tab_template.click()
    # Не упало → ОК (expect ретраится пока вкладки переключаются)
    expect(wizard.heading).to_be_visible()


@pytest.mark.positive
@allure.title("Documents wizard: 'Назад' возвращает на /documents")
def test_documents_wizard_back_returns_to_list(
    client_admin_page: Page, settings: Settings
) -> None:
    docs = _open_documents(client_admin_page, settings)
    docs.click_create()
    wizard = DocumentCreateWizardPage(client_admin_page)
    expect(wizard.back_button).to_be_visible(timeout=settings.expect_timeout)
    wizard.back_button.click()
    expect(client_admin_page).to_have_url(
        re.compile(r"/documents(\?|$)"), timeout=settings.nav_timeout
    )
