"""Debug: проверка что бэк делает с пустым ИНН."""

from __future__ import annotations

import os
import secrets
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
ADMIN_PHONE = os.environ["SUPER_ADMIN_PHONE"]
ADMIN_PASS = os.environ["SUPER_ADMIN_PASSWORD"]

OUT = Path("recon")


def rd(n: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def main() -> None:
    suffix = uuid.uuid4().hex[:6]
    api_log: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()
        page.on(
            "response",
            lambda r: api_log.append(f"{r.status} {r.request.method}\n  {r.text()[:400]}\n")
            if "/api/v1/admin/tenants" in r.url and r.request.method == "POST"
            else None,
        )

        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        page.goto(f"{ADMIN_URL}/tenants/new", wait_until="networkidle")
        page.wait_for_timeout(1_000)

        page.get_by_role("textbox", name="Название компании").fill(f"[E2E] noinn {suffix}")
        page.get_by_role("textbox", name="Slug").fill(f"e2e-noinn-{suffix}")
        # ИНН ОСТАВЛЯЕМ ПУСТЫМ
        page.get_by_role("textbox", name="Имя").fill("Тест")
        page.get_by_role("textbox", name="Фамилия").fill("Админ")
        page.get_by_role("textbox", name="Телефон").fill(f"905{rd(7)}")
        page.get_by_role("textbox", name="ПИНФЛ").fill(rd(14))
        page.get_by_role("button", name="Создать").click()
        page.wait_for_timeout(4_000)

        (OUT / "debug_noinn_after_url.txt").write_text(page.url)
        (OUT / "debug_noinn_after.yaml").write_text(page.locator("body").aria_snapshot())
        (OUT / "debug_noinn_api.txt").write_text("\n".join(api_log))

        page.close()
        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
