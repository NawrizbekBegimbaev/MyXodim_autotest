"""Разведка экранов после логина: Admin (после ввода пары) и Client OTP-page."""

import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
CLIENT_URL = os.getenv("CLIENT_URL", "https://dev-hub-client.greatmall.uz")
ADMIN_PHONE = os.environ["SUPER_ADMIN_PHONE"]
ADMIN_PASS = os.environ["SUPER_ADMIN_PASSWORD"]
CLIENT_PHONE = os.environ["CLIENT_SMOKE_PHONE"].removeprefix("+998")

OUT = Path("recon")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )

        # --- Admin: логин и снимок главной ---
        page = ctx.new_page()
        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        (OUT / "admin_after_login_url.txt").write_text(page.url)
        (OUT / "admin_after_login_snapshot.yaml").write_text(
            page.locator("body").aria_snapshot()
        )
        page.close()

        # --- Client: телефон → "Отправить код" → снимок OTP ---
        page = ctx.new_page()
        page.goto(f"{CLIENT_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Номер телефона").fill(CLIENT_PHONE)
        page.get_by_role("button", name="Отправить код").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        (OUT / "client_otp_url.txt").write_text(page.url)
        (OUT / "client_otp_snapshot.yaml").write_text(page.locator("body").aria_snapshot())
        page.close()

        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
