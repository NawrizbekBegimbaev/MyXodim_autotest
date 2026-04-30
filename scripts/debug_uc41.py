"""Debug UC-4.1: повторяем логику теста и смотрим что не так."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
ADMIN_PHONE = os.environ["SUPER_ADMIN_PHONE"]
ADMIN_PASS = os.environ["SUPER_ADMIN_PASSWORD"]

OUT = Path("recon")


def main() -> None:
    suffix = uuid.uuid4().hex[:6]
    ts = int(time.time())
    name = f"[E2E] {suffix}"
    slug = f"e2e-{suffix}"
    inn = str(ts)[-9:]
    phone_local = f"905{ts % 1_000_000:06d}"
    import secrets
    pinfl = "".join(str(secrets.randbelow(10)) for _ in range(14))

    print(f"name={name}, slug={slug}, inn={inn}, phone=+998{phone_local}, pinfl={pinfl}")

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
            lambda r: api_log.append(f"{r.status} {r.request.method} {r.url}\n  {r.text()[:400]}\n")
            if "/api/v1/admin/tenants" in r.url
            else None,
        )

        # Login
        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        # /tenants/new (как в тесте — через goto)
        page.goto(f"{ADMIN_URL}/tenants/new", wait_until="networkidle")
        page.wait_for_timeout(1_000)

        # Fill — точно как в POM
        page.get_by_role("textbox", name="Название компании").fill(name)
        page.get_by_role("textbox", name="Slug").fill(slug)
        page.get_by_role("textbox", name="ИНН").fill(inn)
        page.get_by_role("textbox", name="Имя").fill("Тест")
        page.get_by_role("textbox", name="Фамилия").fill("Администратор")
        page.get_by_role("textbox", name="Телефон").fill(phone_local)
        page.get_by_role("textbox", name="ПИНФЛ").fill(pinfl)

        (OUT / "debug_filled_url.txt").write_text(page.url)
        (OUT / "debug_filled.yaml").write_text(page.locator("body").aria_snapshot())

        page.get_by_role("button", name="Создать").click()
        page.wait_for_timeout(4_000)
        (OUT / "debug_after_url.txt").write_text(page.url)
        (OUT / "debug_after.yaml").write_text(page.locator("body").aria_snapshot())
        (OUT / "debug_after_text.txt").write_text(page.locator("body").inner_text())

        (OUT / "debug_api.txt").write_text("\n".join(api_log))

        page.close()
        ctx.close()
        browser.close()

    print("Done")


if __name__ == "__main__":
    main()
