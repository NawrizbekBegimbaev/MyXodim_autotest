"""Проверка: телефон +998945535395 был создан минуту назад через UI.
Сейчас попробуем залогиниться им — если получится, значит BUG-010
был race condition (eventual consistency), а не реальный bug."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

CLIENT_URL = os.getenv("CLIENT_URL", "https://dev-hub-client.greatmall.uz")
TEST_OTP = os.environ.get("TEST_OTP", "123456")

PHONE = sys.argv[1] if len(sys.argv) > 1 else "945535395"
OUT = Path("recon")


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()
        page.goto(f"{CLIENT_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Номер телефона").fill(PHONE)
        page.get_by_role("button", name="Отправить код").click()
        page.wait_for_timeout(3_000)
        OUT.mkdir(exist_ok=True)
        (OUT / "otp_existing_check.yaml").write_text(page.locator("body").aria_snapshot())
        body = page.locator("body").inner_text()
        if "Ошибка отправки кода" in body:
            print(f"FAIL: phone {PHONE} → 'Ошибка отправки кода'")
        elif page.get_by_role("textbox", name="Код подтверждения").count() > 0:
            print(f"OK: phone {PHONE} → OTP input appeared")
        else:
            print(f"UNKNOWN: phone {PHONE} — see recon/otp_existing_check.yaml")
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
