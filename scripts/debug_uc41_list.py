"""Debug: создание + проверка в списке."""

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
    name = f"[E2E] {suffix}"
    slug = f"e2e-{suffix}"

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

        page.goto(f"{ADMIN_URL}/tenants/new", wait_until="networkidle")
        page.wait_for_timeout(1_000)
        page.get_by_role("textbox", name="Название компании").fill(name)
        page.get_by_role("textbox", name="Slug").fill(slug)
        page.get_by_role("textbox", name="ИНН").fill(rd(9))
        page.get_by_role("textbox", name="Имя").fill("Тест")
        page.get_by_role("textbox", name="Фамилия").fill("Админ")
        page.get_by_role("textbox", name="Телефон").fill(f"905{rd(7)}")
        page.get_by_role("textbox", name="ПИНФЛ").fill(rd(14))
        page.get_by_role("button", name="Создать").click()
        page.wait_for_timeout(3_000)
        # success state expected
        print("After submit URL:", page.url)
        print("Has success heading:", page.get_by_role(
            "heading", name="Компания создана", level=5
        ).is_visible())

        # goto /tenants
        page.goto(f"{ADMIN_URL}/tenants")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3_000)
        print("/tenants URL:", page.url)
        (OUT / "debug_list_no_search.yaml").write_text(page.locator("body").aria_snapshot())

        # search by slug
        page.get_by_role("textbox", name="Поиск...").fill(slug)
        page.wait_for_timeout(2_500)
        (OUT / "debug_list_with_search.yaml").write_text(page.locator("body").aria_snapshot())

        page.close()
        ctx.close()
        browser.close()
    print(f"Created name={name}, slug={slug}")


if __name__ == "__main__":
    main()
