"""Real-document flow: создаём документ через wizard → отправляем на маршрут →
проверяем что он появился в /documents в статусе 'В работе' с pipeline approvers.

Approve/Reject как непосредственное действие требует чтобы текущий юзер был
первым в маршруте. В существующих маршрутах ('Повышение (v2)' и др.) admin —
только creator, не approver, поэтому /inbox для него пуст. Тест на сам клик
'Согласовать'/'Отклонить' помечен xfail (ожидает либо custom-route с self-approve
либо multi-user setup). См. main E2E flow для полной цепочки.
"""

from __future__ import annotations

import re
import secrets

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.documents_page import DocumentCreateWizardPage, DocumentsPage
from pages.client.inbox_page import InboxPage


def _create_doc_with_route(
    page: Page, settings: Settings, title: str
) -> str:
    """Создаёт документ через wizard и отправляет на маршрут.
    Возвращает URL detail-страницы (/documents/{uuid}).
    """
    docs = DocumentsPage(page).goto(settings.client_url)
    expect(docs.heading).to_be_visible(timeout=settings.nav_timeout)
    docs.click_create()
    wizard = DocumentCreateWizardPage(page)
    expect(wizard.heading).to_be_visible(timeout=settings.nav_timeout)

    wizard.select_first_template()
    page.wait_for_timeout(800)
    wizard.fill_title(title).fill_content("E2E real-doc content").click_next()
    page.wait_for_timeout(2_500)

    wizard.select_route()
    wizard.select_target_branch_first()
    wizard.click_next()
    page.wait_for_timeout(2_500)

    expect(wizard.review_heading).to_be_visible(timeout=settings.nav_timeout)
    wizard.click_submit_route()
    # После submit редирект на /documents/{uuid}
    page.wait_for_url(
        re.compile(r"/documents/[0-9a-f-]{36}"), timeout=settings.nav_timeout
    )
    page.wait_for_timeout(2_000)
    return page.url


# Все тесты в файле мутируют состояние через UI (CRUD-формы).
pytestmark = [
    pytest.mark.creates_data,
    pytest.mark.needs_backend,
    pytest.mark.skip(reason="Real document flow blocked until document wizard fixtures are available"),
]


@pytest.mark.positive
@allure.title(
    "Real doc: создание + отправка на маршрут → редирект на detail с DOC-N в работе"
)
def test_real_doc_submit_lands_on_detail_in_progress(
    client_admin_page: Page, settings: Settings
) -> None:
    title = f"{E2E_PREFIX} Real {secrets.token_hex(3)}"
    detail_url = _create_doc_with_route(client_admin_page, settings, title)
    assert "/documents/" in detail_url

    page = client_admin_page
    # Заголовок документа в detail
    expect(
        page.get_by_role("heading", name=title, level=6)
    ).to_be_visible(timeout=settings.nav_timeout)
    # Статус "В работе"
    expect(page.get_by_text("В работе").first).to_be_visible(
        timeout=settings.nav_timeout
    )
    # DOC-N номер видим (формат "DOC-<digits>")
    expect(page.get_by_text(re.compile(r"DOC-\d+")).first).to_be_visible()


@pytest.mark.positive
@allure.title(
    "Real doc: detail-страница показывает pipeline approvers (Активность tab)"
)
def test_real_doc_detail_shows_route_pipeline(
    client_admin_page: Page, settings: Settings
) -> None:
    title = f"{E2E_PREFIX} Pipe {secrets.token_hex(3)}"
    _create_doc_with_route(client_admin_page, settings, title)
    page = client_admin_page

    # Tabs: Активность / Маршрут / Поля
    expect(page.get_by_role("tab", name="Активность")).to_be_visible(
        timeout=settings.expect_timeout
    )
    expect(page.get_by_role("tab", name="Маршрут")).to_be_visible()
    expect(page.get_by_role("tab", name="Поля")).to_be_visible()
    # Хотя бы один "Ожидает действия" должен быть в pipeline
    expect(page.get_by_text("Ожидает действия").first).to_be_visible(
        timeout=settings.expect_timeout
    )


@pytest.mark.positive
@allure.title("Real doc: после submit виден в /documents (Мои документы)")
def test_real_doc_appears_in_documents_list(
    client_admin_page: Page, settings: Settings
) -> None:
    title = f"{E2E_PREFIX} ListReal {secrets.token_hex(3)}"
    _create_doc_with_route(client_admin_page, settings, title)
    page = client_admin_page

    page.goto(f"{settings.client_url}/documents", wait_until="networkidle")
    page.wait_for_timeout(2_000)
    # Документ виден где-то на странице (поиском по заголовку/ссылке)
    short_title = title.split("] ")[1]
    expect(page.get_by_text(short_title).first).to_be_visible(
        timeout=settings.nav_timeout
    )


@pytest.mark.positive
@allure.title(
    "Real doc: /inbox для admin'а не содержит свежесозданный док "
    "(admin = creator, не approver)"
)
def test_real_doc_not_in_admin_inbox(
    client_admin_page: Page, settings: Settings
) -> None:
    """Админ создаёт док → ожидаем что в /inbox его НЕТ, т.к. он только
    creator. Это негативный sanity-чек который объясняет почему full
    approve flow требует multi-user setup."""
    title = f"{E2E_PREFIX} NotMine {secrets.token_hex(3)}"
    _create_doc_with_route(client_admin_page, settings, title)
    page = client_admin_page

    inbox = InboxPage(page).goto(settings.client_url)
    expect(inbox.heading).to_be_visible(timeout=settings.nav_timeout)
    # Поиск по короткому заголовку — ничего не должно найтись
    short_title = title.split("] ")[1]
    inbox.search_input.fill(short_title)
    page.wait_for_timeout(1_500)
    # row с этим названием отсутствует
    expect(
        page.get_by_role("row").filter(has_text=short_title)
    ).to_have_count(0)


@pytest.mark.positive
@pytest.mark.xfail(
    reason="Approve как клик доступен только для approver-юзера, "
    "admin = creator. Требует multi-user setup или custom-route с self-approve.",
    strict=False,
)
@allure.title("Real doc: admin может нажать 'Согласовать' на свежесозданном доке")
def test_real_doc_creator_can_approve(
    client_admin_page: Page, settings: Settings
) -> None:
    title = f"{E2E_PREFIX} Apprv {secrets.token_hex(3)}"
    _create_doc_with_route(client_admin_page, settings, title)
    page = client_admin_page

    approve_btn = page.get_by_role("button", name="Согласовать", exact=True)
    expect(approve_btn).to_be_enabled(timeout=settings.expect_timeout)
    approve_btn.click()
