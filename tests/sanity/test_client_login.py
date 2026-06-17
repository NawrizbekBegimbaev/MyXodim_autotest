"""Sanity case 5 — Client UI login by phone + OTP."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.sanity, pytest.mark.client]


@allure.title("5. Логин — вход по телефону + OTP")
@allure.description(
    "**Цель:** сотрудник входит в Client UI по телефону и одноразовому коду (OTP).\n\n"
    "**Окружение:** stage, Client UI. На stage принимается любой 6-значный OTP "
    "(`123456`) для зарегистрированного номера.\n"
    "**Предусловие:** существует пользователь (админ созданной [SANITY]-компании).\n\n"
    "**Шаги воспроизведения:**\n"
    "1. Открыть Client UI `/login`.\n"
    "2. Ввести номер телефона, нажать «Отправить код».\n"
    "3. Ввести OTP `123456`, нажать «Войти».\n"
    "4. Дождаться рабочего стола.\n\n"
    "**Ожидаемый результат:** редирект на `/home`, виден заголовок «Добро пожаловать», "
    "роль «Администратор»."
)
def test_client_login_by_otp(admin_client_page: Page, cfg) -> None:
    with allure.step("Открыть /home под залогиненным пользователем"):
        admin_client_page.goto(f"{cfg.client_url}/home", wait_until="domcontentloaded")
    with allure.step("Проверить /home, приветствие и роль"):
        expect(admin_client_page).to_have_url(re.compile(r"/home"))
        expect(admin_client_page.get_by_role("heading", name="Добро пожаловать")).to_be_visible()
        expect(admin_client_page.get_by_text("Администратор").first).to_be_visible()
