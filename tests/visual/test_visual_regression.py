"""Visual regression — pixel-сравнение скриншотов с baseline.

Ловит классы багов которые не видит DOM-проверка:
- Кнопка ушла за viewport / скрыта overflow'ом
- Z-index сломан, модалка под заголовком
- Стиль color/font/padding регресснул
- Лейаут схлопнулся

Baseline хранится в tests/visual/baselines/, коммитится в git.

Первый прогон создаёт baseline и SKIP'ит. Дальнейшие — сравнивают.
Чтобы перегенерировать baseline'ы (после намеренной смены UI):
    UPDATE_BASELINES=1 pytest tests/visual

При fail'е actual.png + diff.png идут в tests/visual/artifacts/.

3 страницы покрыты: Admin /login, Client /login, Mock 1C / —
все без auth и стабильны.
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from tests.visual.visual_helper import assert_screenshot_matches


@pytest.mark.visual
@allure.title("Visual: Admin /login — pixel-baseline")
def test_visual_admin_login_page(page: Page, settings: Settings) -> None:
    page.goto(f"{settings.admin_url}/login", wait_until="networkidle")
    expect(
        page.get_by_role("heading", name="BusinessHub Admin", level=6)
    ).to_be_visible(timeout=settings.expect_timeout)
    assert_screenshot_matches(page, "admin-login", threshold=0.01)


@pytest.mark.visual
@allure.title("Visual: Client /login — pixel-baseline")
def test_visual_client_login_page(page: Page, settings: Settings) -> None:
    page.goto(f"{settings.client_url}/login", wait_until="networkidle")
    expect(
        page.get_by_role("heading", name="Добро пожаловать в BusinessHub", level=5)
    ).to_be_visible(timeout=settings.expect_timeout)
    assert_screenshot_matches(page, "client-login", threshold=0.01)


@pytest.mark.visual
@allure.title("Visual: Mock 1C / — pixel-baseline")
def test_visual_mock1c_setup_page(page: Page, settings: Settings) -> None:
    page.goto(settings.mock1c_url, wait_until="networkidle")
    expect(
        page.get_by_role("heading", name="Mock 1C", level=1)
    ).to_be_visible(timeout=settings.expect_timeout)
    assert_screenshot_matches(page, "mock1c-setup", threshold=0.01)
