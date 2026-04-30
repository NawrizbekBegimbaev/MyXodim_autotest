"""Полный тест: создаём, возвращаемся к списку, смотрим что там."""

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
    name = f"[E2E] full {suffix}"
    slug = f"e2e-full-{suffix}"
    pinfl = f"{secrets.randbelow(6) + 1}{rd(13)}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        # Create
        page.goto(f"{ADMIN_URL}/tenants/new", wait_until="networkidle")
        page.wait_for_timeout(1_000)
        page.get_by_role("textbox", name="Название компании").fill(name)
        page.get_by_role("textbox", name="Slug").fill(slug)
        page.get_by_role("textbox", name="ИНН").fill(rd(9))
        page.get_by_role("textbox", name="Имя").fill("Тест")
        page.get_by_role("textbox", name="Фамилия").fill("Админ")
        page.get_by_role("textbox", name="Телефон").fill(f"905{rd(7)}")
        page.get_by_role("textbox", name="ПИНФЛ").fill(pinfl)
        with page.expect_response(
            lambda r: "/api/v1/admin/tenants" in r.url and r.request.method == "POST",
            timeout=15_000,
        ):
            page.get_by_role("button", name="Создать").click()
        page.wait_for_timeout(2_000)
        print(f"After create URL: {page.url}")
        print(
            f"Success heading visible: "
            f"{page.get_by_role('heading', name='Компания создана').is_visible()}"
        )

        # Goto list
        page.goto(f"{ADMIN_URL}/tenants")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2_000)
        # Snapshot первых 15 строк
        rows = page.get_by_role("row").all()
        print(f"\nTotal rows: {len(rows)}")
        for i, row in enumerate(rows[:15]):
            text = row.text_content() or ""
            print(f"  {i}: {text[:100]}")

        print(f"\nIs my company in list?")
        my_row = page.get_by_role("row").filter(has_text=name)
        print(f"  count = {my_row.count()}")
        print(f"  visible = {my_row.first.is_visible() if my_row.count() else 'N/A'}")

        page.close()
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
