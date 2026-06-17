"""Sanity case 29 — launch a document (create from a template → draft).

Self-contained: pushes templates via Mock 1C (idempotent), then as the company
admin creates a document from an imported template and saves it as a draft. The
document is created with its template/route and is ready for circulation.

Scope note: the in-form route-builder (adding an approval step, then «Отправить
на согласование» → «Согласовать») is currently NOT automated here. On the
document-create page the route-step row re-renders continuously while the
template workflow resolves, so interacting with it is not stable enough for a
daily gate. That instability is itself a product UX issue worth reporting; the
submit→approve leg is deferred until the create-page route panel is stabilised.
Signing stays out of scope (agreed). Runs last so it doesn't disturb the
clean-directories case.
"""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.admin.create_company_page import CreatedTenant
from pages.client.create_document_page import CreateDocumentPage
from pages.client.documents_page import DocumentsPage
from pages.mock1c.mock1c_page import Mock1cPage

pytestmark = [pytest.mark.sanity, pytest.mark.client]

TEMPLATE = "Заявка на отпуск"


@allure.title("29. Запуск документа в оборот — создание из шаблона")
@allure.description(
    "**Цель:** документ запускается из импортированного шаблона (создаётся черновик).\n\n"
    "**Окружение:** stage, Mock 1C + Client UI.\n"
    "**Предусловие:** создана [SANITY]-компания (есть ключ интеграции).\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Через Mock 1C импортировать шаблоны («Отправить все» на странице Шаблоны).\n"
    "2. В Client UI открыть `/documents/create`.\n"
    "3. Выбрать «Вид документа» = «Заявка на отпуск».\n"
    "4. Нажать «Сохранить как черновик».\n"
    "5. Открыть `/documents` и найти документ.\n\n"
    "**Ожидаемый результат:** документ создан и виден в списке.\n\n"
    "_Граница:_ submit→«Согласовать» не автоматизирован — на странице создания строка "
    "шага маршрута нестабильна (непрерывный ре-рендер); подпись вне scope."
)
def test_document_circulation(
    page: Page, admin_client_page: Page, cfg, sanity_tenant: CreatedTenant
) -> None:
    with allure.step("Mock 1C: импорт шаблонов в компанию"):
        mock = Mock1cPage(page, cfg.mock1c_url).connect(sanity_tenant.integration_key)
        mock.push_all("/templates")
        expect(page.get_by_text("Отправлено").first).to_be_visible(timeout=20_000)

    create = CreateDocumentPage(admin_client_page, cfg.client_url).open()
    expect(create.heading).to_be_visible()

    with allure.step(f"Создать документ из шаблона «{TEMPLATE}» и сохранить черновик"):
        create.select_template(TEMPLATE)
        expect(create.save_draft_button).to_be_enabled()
        create.save_as_draft()
        expect(admin_client_page).not_to_have_url(re.compile(r"/documents/create$"), timeout=20_000)

    with allure.step("Документ виден в списке (запущен)"):
        docs = DocumentsPage(admin_client_page, cfg.client_url).open()
        expect(docs.heading).to_be_visible()
        expect(admin_client_page.get_by_text(TEMPLATE).first).to_be_visible(timeout=20_000)
