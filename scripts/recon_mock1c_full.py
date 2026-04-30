"""Полный recon Mock 1C интеграции:
1. Admin UI → создать компанию → извлечь integrationKey + tenantId
2. Mock 1C → ввести ключ → "Сохранить" → snapshot подключения
3. Mock 1C → Должности → создать → "Отправить"
4. Mock 1C → Сотрудники → создать → "Отправить"
5. Mock 1C → Шаблоны (просмотр)
6. Client UI (новый Administrator) → /positions, /members → проверить что данные появились
"""

from __future__ import annotations

import os
import re
import secrets
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
CLIENT_URL = os.getenv("CLIENT_URL", "https://dev-hub-client.greatmall.uz")
MOCK1C_URL = os.getenv("MOCK1C_URL", "https://dev-mock-1c.greatmall.uz")
ADMIN_PHONE = os.environ["SUPER_ADMIN_PHONE"]
ADMIN_PASS = os.environ["SUPER_ADMIN_PASSWORD"]
TEST_OTP = os.environ.get("TEST_OTP", "123456")

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"m1c_{label}_url.txt").write_text(page.url)
    (OUT / f"m1c_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def rd(n: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def valid_pinfl() -> str:
    return f"{secrets.randbelow(6) + 1}{rd(13)}"


def main() -> None:
    suffix = uuid.uuid4().hex[:6]
    company = {
        "name": f"[E2E mock1c] {suffix}",
        "slug": f"e2e-m1c-{suffix}",
        "inn": rd(9),
        "first_name": "Якорь",
        "last_name": "Mock1C",
        "phone_local": f"90{rd(7)}",  # 9 цифр (90 + 7 random)
        "pinfl": valid_pinfl(),
    }
    company["phone_full"] = f"+998{company['phone_local']}"

    api_log: list[str] = []

    def dump_api() -> None:
        OUT.mkdir(exist_ok=True)
        (OUT / "m1c_api.txt").write_text("\n".join(api_log))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ============================================================
        # ШАГ 1: Admin UI создаёт компанию
        # ============================================================
        admin_ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        admin_page = admin_ctx.new_page()
        def _admin_response(r):  # type: ignore[no-untyped-def]
            try:
                if "/api/" in r.url:
                    api_log.append(f"[{r.status} {r.request.method}] {r.url}\n  {r.text()[:300]}\n")
            except Exception:
                pass

        admin_page.on("response", _admin_response)

        admin_page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        admin_page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        admin_page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        admin_page.get_by_role("button", name="Войти").click()
        admin_page.wait_for_url("**/dashboard", timeout=15_000)
        # Дождаться полной инициализации SPA (как в conftest)
        from playwright.sync_api import expect as _expect

        _expect(admin_page.get_by_role("heading", name="Admin User")).to_be_visible(timeout=15_000)
        admin_page.wait_for_load_state("networkidle")
        admin_page.wait_for_timeout(1_000)

        # Используем POM (работает в pytest стабильно)
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from pages.admin.create_company_page import CreateCompanyPage  # noqa: E402

        create = CreateCompanyPage(admin_page).goto(ADMIN_URL)
        admin_page.wait_for_timeout(800)
        create.fill_company(
            name=company["name"], slug=company["slug"], inn=company["inn"]
        ).fill_admin(
            first_name=company["first_name"],
            last_name=company["last_name"],
            phone_local=company["phone_local"],
            pinfl=company["pinfl"],
        )
        # Submit с ожиданием POST-ответа
        with admin_page.expect_response(
            lambda r: "/api/v1/admin/tenants" in r.url and r.request.method == "POST",
            timeout=20_000,
        ):
            create._submit.click()  # noqa: SLF001
        admin_page.wait_for_timeout(2_500)
        snap(admin_page, "01_admin_success")

        # Извлекаем ключ из success-state
        body = admin_page.locator("body").inner_text()
        key_match = re.search(r"bh_live_[a-f0-9]{32}", body)
        tenant_id_match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", body)
        integration_key = key_match.group(0) if key_match else None
        tenant_id = tenant_id_match.group(0) if tenant_id_match else None
        print(f"\nCreated: {company['name']}")
        print(f"  integrationKey: {integration_key}")
        print(f"  tenantId:       {tenant_id}")
        print(f"  admin phone:    {company['phone_full']}")
        admin_ctx.close()

        if not integration_key:
            print("ERROR: integrationKey не найден на success-page")
            dump_api()
            browser.close()
            return

        # ============================================================
        # ШАГ 2: Mock 1C → ввести ключ → подключиться
        # ============================================================
        m1c_ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        m1c_page = m1c_ctx.new_page()
        m1c_page.on(
            "response",
            lambda r: api_log.append(f"[m1c {r.status} {r.request.method}] {r.url}\n  {r.text()[:300]}\n")
            if "/api/" in r.url
            else None,
        )

        m1c_page.goto(MOCK1C_URL, wait_until="networkidle")
        m1c_page.wait_for_timeout(1_500)
        snap(m1c_page, "02_initial")

        # Поле "Ключ интеграции" — было в первом recon
        m1c_page.get_by_role("textbox").first.fill(integration_key)
        m1c_page.get_by_role("button", name="Сохранить").click()
        m1c_page.wait_for_timeout(3_000)
        snap(m1c_page, "03_after_connect")

        # ============================================================
        # ШАГ 3: Mock 1C → Должности
        # ============================================================
        try:
            m1c_page.get_by_role("link", name="Должности").click(timeout=3_000)
            m1c_page.wait_for_timeout(1_500)
            snap(m1c_page, "04_positions_initial")
        except Exception as e:
            (OUT / "m1c_04_positions_err.txt").write_text(str(e))

        # ============================================================
        # ШАГ 4: Mock 1C → Сотрудники
        # ============================================================
        try:
            m1c_page.get_by_role("link", name="Сотрудники").click(timeout=3_000)
            m1c_page.wait_for_timeout(1_500)
            snap(m1c_page, "05_members_initial")
        except Exception as e:
            (OUT / "m1c_05_members_err.txt").write_text(str(e))

        # ============================================================
        # ШАГ 5: Mock 1C → Шаблоны
        # ============================================================
        try:
            m1c_page.get_by_role("link", name="Шаблоны").click(timeout=3_000)
            m1c_page.wait_for_timeout(1_500)
            snap(m1c_page, "06_templates_initial")
        except Exception as e:
            (OUT / "m1c_06_templates_err.txt").write_text(str(e))

        m1c_ctx.close()

        # ============================================================
        # ШАГ 6: Client UI — логин Администратора этой компании
        # ============================================================
        client_ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        client_page = client_ctx.new_page()
        client_page.goto(f"{CLIENT_URL}/login", wait_until="networkidle")
        client_page.get_by_role("textbox", name="Номер телефона").fill(company["phone_local"])
        client_page.get_by_role("button", name="Отправить код").click()
        client_page.wait_for_load_state("networkidle")
        client_page.wait_for_timeout(1_000)
        try:
            client_page.get_by_role("textbox", name="Код подтверждения").fill(TEST_OTP)
            client_page.get_by_role("button", name="Войти").click()
            client_page.wait_for_timeout(3_000)
            snap(client_page, "07_client_after_login")

            # Прямой переход на /integration чтобы взять ключ снова из Client UI
            client_page.goto(f"{CLIENT_URL}/integration", wait_until="networkidle")
            client_page.wait_for_timeout(1_500)
            snap(client_page, "08_client_integration")
        except Exception as e:
            (OUT / "m1c_07_client_err.txt").write_text(str(e))

        client_ctx.close()
        browser.close()

    dump_api()
    print("\nDone")


if __name__ == "__main__":
    main()
