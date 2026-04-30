"""UC-3.6 positive: создание сотрудника локально через Client UI.

BRD §3.6: управление сотрудниками (добавить).
В UI раздел называется "Пользователи" (/members), кнопка "Добавить сотрудника".

Тесты работают в существующей орг (settings.client_smoke_org) — пока BUG-001
блокирует создание новых компаний. Каждый создаваемый сотрудник имеет
[E2E] префикс в фамилии → maintenance-тест чистит еженедельно.
"""

from __future__ import annotations

import uuid

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from data.constants import E2E_PREFIX
from pages.client.member_create_dialog import MemberCreateDialog
from pages.client.members_page import MembersPage


@pytest.mark.positive
@allure.title("UC-3.6: создание сотрудника с валидными данными → появляется в списке")
def test_member_create_with_valid_data_appears_in_list(
    client_admin_page: Page, settings: Settings, random_test_phone: str
) -> None:
    suffix = uuid.uuid4().hex[:6]
    first_name = "Тестовый"
    last_name = f"{E2E_PREFIX} Сотрудник {suffix}"
    phone = random_test_phone

    members = MembersPage(client_admin_page).goto(settings.client_url)

    with allure.step("Открываем модалку создания сотрудника"):
        members.click_add()
        dialog = MemberCreateDialog(client_admin_page)
        expect(dialog.dialog).to_be_visible(timeout=settings.expect_timeout)

    with allure.step(f"Заполняем форму (телефон={phone})"):
        dialog.fill_required(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role="Сотрудник",
        )

    with allure.step("Submit"):
        dialog.submit()
        expect(dialog.dialog).to_be_hidden(timeout=settings.expect_timeout)

    with allure.step("Сотрудник виден в списке (поиск по телефону)"):
        members.search(phone)
        expect(members.row_by_phone(phone)).to_be_visible(timeout=settings.expect_timeout)
