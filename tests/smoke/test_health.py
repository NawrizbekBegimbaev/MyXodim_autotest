"""Health smoke: все три UI открываются и страница логина доступна.

BRD: общая работоспособность dev-окружения.
"""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings


@pytest.mark.smoke
@allure.title("Admin UI: страница логина открывается")
def test_admin_ui_login_page_opens(page: Page, settings: Settings) -> None:
    page.goto(settings.admin_url)
    expect(page).to_have_url(re.compile(re.escape(settings.admin_url)), timeout=settings.nav_timeout)


@pytest.mark.smoke
@allure.title("Client UI: страница логина открывается")
def test_client_ui_login_page_opens(page: Page, settings: Settings) -> None:
    page.goto(settings.client_url)
    expect(page).to_have_url(re.compile(re.escape(settings.client_url)), timeout=settings.nav_timeout)


@pytest.mark.smoke
@allure.title("Mock 1C: главная страница (настройки подключения) открывается")
def test_mock1c_ui_main_page_opens(page: Page, settings: Settings) -> None:
    """Mock 1C не имеет логина по логину/паролю — авторизация через ключ интеграции
    из админ-панели BusinessHub. Проверяем что главная отдаётся.
    """
    page.goto(settings.mock1c_url)
    expect(page).to_have_url(re.compile(re.escape(settings.mock1c_url)), timeout=settings.nav_timeout)
    expect(page.get_by_role("heading", name="Настройки подключения")).to_be_visible(
        timeout=settings.expect_timeout
    )
