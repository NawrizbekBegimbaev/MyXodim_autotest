"""Recon реакций Admin UI на negative login + security + session."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
ADMIN_PHONE = os.environ["SUPER_ADMIN_PHONE"]
ADMIN_PASS = os.environ["SUPER_ADMIN_PASSWORD"]

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"login_{label}_url.txt").write_text(page.url)
    (OUT / f"login_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def login_form(page: Page) -> None:
    page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
    page.wait_for_timeout(500)


def main() -> None:
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
            lambda r: api_log.append(f"[{r.status} {r.request.method}] {r.url}\n  {r.text()[:300]}\n")
            if "/api/v1/admin/auth" in r.url
            else None,
        )

        # 1. Initial form
        login_form(page)
        snap(page, "00_initial")

        # 2. Empty submit
        page.get_by_role("button", name="Войти").click()
        page.wait_for_timeout(1_000)
        snap(page, "01_empty_submit")

        # 3. Invalid phone format (letters)
        login_form(page)
        page.get_by_role("textbox", name="Телефон").fill("abcdefghi")
        page.get_by_role("textbox", name="Пароль").fill("anything")
        page.get_by_role("button", name="Войти").click()
        page.wait_for_timeout(1_500)
        snap(page, "02_letters_in_phone")

        # 4. Невалидная длина телефона
        login_form(page)
        page.get_by_role("textbox", name="Телефон").fill("123")
        page.get_by_role("textbox", name="Пароль").fill("anything")
        page.get_by_role("button", name="Войти").click()
        page.wait_for_timeout(1_500)
        snap(page, "03_short_phone")

        # 5. Несуществующий телефон
        login_form(page)
        page.get_by_role("textbox", name="Телефон").fill("+998900000099")
        page.get_by_role("textbox", name="Пароль").fill("any-password-123")
        api_log.append("--- WRONG PHONE ---")
        page.get_by_role("button", name="Войти").click()
        page.wait_for_timeout(2_500)
        snap(page, "04_wrong_phone")

        # 6. Неверный пароль (правильный телефон)
        login_form(page)
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill("wrong-password")
        api_log.append("--- WRONG PASSWORD ---")
        page.get_by_role("button", name="Войти").click()
        page.wait_for_timeout(2_500)
        snap(page, "05_wrong_password")

        # 7. XSS в телефоне
        login_form(page)
        page.get_by_role("textbox", name="Телефон").fill("<script>alert(1)</script>")
        page.get_by_role("textbox", name="Пароль").fill("any")
        api_log.append("--- XSS PHONE ---")
        page.get_by_role("button", name="Войти").click()
        page.wait_for_timeout(1_500)
        snap(page, "06_xss_phone")

        # 8. SQLi в пароль
        login_form(page)
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill("' OR 1=1 --")
        api_log.append("--- SQLi ---")
        page.get_by_role("button", name="Войти").click()
        page.wait_for_timeout(2_500)
        snap(page, "07_sqli_password")

        # 9. Direct URL /dashboard БЕЗ логина
        ctx2 = browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
        p2 = ctx2.new_page()
        p2.goto(f"{ADMIN_URL}/dashboard", wait_until="networkidle")
        p2.wait_for_timeout(1_500)
        snap(p2, "08_direct_dashboard_no_auth")
        ctx2.close()

        # 10. Direct URL /tenants/new без логина
        ctx3 = browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
        p3 = ctx3.new_page()
        p3.goto(f"{ADMIN_URL}/tenants/new", wait_until="networkidle")
        p3.wait_for_timeout(1_500)
        snap(p3, "09_direct_tenants_new_no_auth")
        ctx3.close()

        # 11. Logout flow: успешный логин → клик "Выйти" → ?
        login_form(page)
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)
        page.wait_for_timeout(1_500)
        snap(page, "10_after_login")
        page.get_by_role("button", name="Выйти").click()
        page.wait_for_timeout(2_500)
        snap(page, "11_after_logout")

        # 12. Refresh после logout — попытка зайти на /dashboard
        page.goto(f"{ADMIN_URL}/dashboard", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        snap(page, "12_after_logout_dashboard")

        (OUT / "login_api.txt").write_text("\n".join(api_log))
        page.close()
        ctx.close()
        browser.close()

    print("Done")


if __name__ == "__main__":
    main()
