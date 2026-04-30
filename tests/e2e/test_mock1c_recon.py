"""Recon Mock 1C: подключение по ключу, обзор страниц.

Это recon-тест — снимает snapshot Mock 1C страниц для построения POM.
После того как POM-ы готовы, можно превратить в обычные положительные тесты.
"""

from __future__ import annotations

from pathlib import Path

import allure
import pytest
from playwright.sync_api import Browser, Page, expect

from config.settings import Settings

OUT = Path("recon")


def _snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"m1c_pt_{label}_url.txt").write_text(page.url)
    (OUT / f"m1c_pt_{label}.yaml").write_text(page.locator("body").aria_snapshot())


@pytest.mark.e2e
@allure.title("Mock1C recon: подключение по ключу + обзор разделов")
def test_mock1c_recon_connect_and_browse(
    browser: Browser,
    super_admin_context: object,
    settings: Settings,
) -> None:
    """Создаёт компанию + получает ключ ВНУТРИ теста, потом recon Mock 1C."""
    import re as _re
    import secrets as _s
    import uuid as _u

    from pages.admin.create_company_page import CompanyCreatedView, CreateCompanyPage

    suffix = _u.uuid4().hex[:6]
    cdata = {
        "name": f"[E2E mock1c] {suffix}",
        "slug": f"e2e-m1c-{suffix}",
        "inn": "".join(str(_s.randbelow(10)) for _ in range(9)),
        "first_name": "Якорь",
        "last_name": "Моков",
        "phone_local": f"905{''.join(str(_s.randbelow(10)) for _ in range(7))}",
        "pinfl": f"{_s.randbelow(6) + 1}{''.join(str(_s.randbelow(10)) for _ in range(13))}",
    }
    admin_page = super_admin_context.new_page()  # type: ignore[attr-defined]
    create = CreateCompanyPage(admin_page).goto(settings.admin_url)
    create.fill_company(name=cdata["name"], slug=cdata["slug"], inn=cdata["inn"]).fill_admin(
        first_name=cdata["first_name"],
        last_name=cdata["last_name"],
        phone_local=cdata["phone_local"],
        pinfl=cdata["pinfl"],
    ).submit()
    success = CompanyCreatedView(admin_page)
    expect(success.heading).to_be_visible(timeout=settings.nav_timeout)
    body = admin_page.locator("body").inner_text()
    integration_key = _re.search(r"bh_live_[a-f0-9]{32}", body).group(0)  # type: ignore[union-attr]
    print(f"\nGot key: {integration_key}", flush=True)
    mock1c_company = {
        **cdata,
        "integration_key": integration_key,
        "phone_full": f"+998{cdata['phone_local']}",
    }
    """Создаёт fresh-context, открывает Mock 1C, вводит ключ, снимает snapshot
    каждого раздела (Подключение / Должности / Сотрудники / Шаблоны).
    """
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()

    with allure.step("Открываем Mock 1C"):
        page.goto(settings.mock1c_url, wait_until="networkidle")
        page.wait_for_timeout(1_500)
        _snap(page, "01_initial")

    with allure.step("Вводим ключ интеграции и сохраняем"):
        page.get_by_role("textbox").first.fill(mock1c_company["integration_key"])
        page.wait_for_timeout(500)
        _snap(page, "02_key_filled")
        page.get_by_role("button", name="Сохранить").click()
        page.wait_for_timeout(3_000)
        _snap(page, "03_after_save")

    for label, link_name in [
        ("04_positions", "Должности"),
        ("05_members", "Сотрудники"),
        ("06_templates", "Шаблоны"),
        ("07_connection_back", "Подключение"),
    ]:
        with allure.step(f"Раздел: {link_name}"):
            try:
                page.get_by_role("link", name=link_name).first.click(timeout=5_000)
                page.wait_for_timeout(1_500)
                _snap(page, label)
            except Exception as e:
                (OUT / f"m1c_pt_{label}_err.txt").write_text(str(e))

    # Прямые URL fallback (если link'ов в навигации не было)
    for path, label in [
        ("/positions", "08_direct_positions"),
        ("/employees", "09_direct_employees"),
        ("/templates", "10_direct_templates"),
    ]:
        try:
            page.goto(f"{settings.mock1c_url}{path}", wait_until="networkidle")
            page.wait_for_timeout(1_500)
            _snap(page, label)
        except Exception as e:
            (OUT / f"m1c_pt_{label}_err.txt").write_text(str(e))

    ctx.close()

    # Базовая проверка: ключ принят (после Сохранить страница не показала ошибку)
    # Снапшот 03_after_save должен показать "Подключено" или иной success-state
    snap_text = (OUT / "m1c_pt_03_after_save.yaml").read_text()
    assert "Не подключено" not in snap_text, (
        "Mock 1C показывает 'Не подключено' после ввода валидного ключа — "
        "проверь содержимое recon/m1c_pt_03_after_save.yaml"
    )


@pytest.mark.e2e
@pytest.mark.skip(reason="Активируется после успешного recon — нужен mock1c_company fixture")
@allure.title("Mock1C: ключ интеграции виден на /integration в Client UI")
def test_client_ui_integration_page_shows_key(
    browser: Browser, settings: Settings, mock1c_company: dict[str, str]
) -> None:
    """Проверяем что ключ из success-page Admin UI совпадает с ключом
    в /integration Client UI (для того же tenant).
    """
    from data.constants import TEST_OTP
    from pages.client.login_page import ClientLoginPage
    from pages.client.otp_page import OtpPage

    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()

    # Логин Администратора этой компании (только что созданной — он один в орг)
    ClientLoginPage(page).goto(settings.client_url).enter_phone(
        mock1c_company["phone_full"]
    ).submit()
    OtpPage(page).enter_code(TEST_OTP).submit()
    # Один в орг → сразу на /dashboard или /tenant-select c одной кнопкой
    page.wait_for_timeout(3_000)

    page.goto(f"{settings.client_url}/integration", wait_until="networkidle")
    page.wait_for_timeout(2_000)
    expect(page.get_by_text(mock1c_company["integration_key"])).to_be_visible(
        timeout=settings.expect_timeout
    )
    ctx.close()
