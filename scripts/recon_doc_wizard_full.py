"""Recon полного wizard'а с правильным заполнением полей."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

CLIENT_URL = os.getenv("CLIENT_URL", "https://dev-hub-client.greatmall.uz")
PHONE = os.environ["CLIENT_SMOKE_PHONE"].removeprefix("+998")
TEST_OTP = os.environ.get("TEST_OTP", "123456")
ORG = os.environ.get("CLIENT_SMOKE_ORG", "QaTeam")

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"docwf_{label}.yaml").write_text(page.locator("body").aria_snapshot())


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
        page.wait_for_load_state("networkidle")
        page.get_by_role("textbox", name="Код подтверждения").fill(TEST_OTP)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/tenant-select", timeout=15_000)
        page.get_by_role("button").filter(
            has=page.get_by_role("heading", name=ORG, level=6, exact=True)
        ).click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        page.goto(f"{CLIENT_URL}/documents/create", wait_until="networkidle")
        page.wait_for_timeout(2_000)

        # Step 1: select first template that contains [E2E]
        first = page.get_by_role("button").filter(
            has=page.get_by_role("heading", level=6)
        ).filter(has_text="INTERNAL").first
        first.click()
        page.wait_for_timeout(800)

        title = f"[E2E] Recon Doc {secrets.token_hex(3)}"
        page.get_by_role("textbox", name="Заголовок").fill(title)
        page.get_by_role("textbox", name="Содержание").fill("recon e2e content blob")
        page.wait_for_timeout(500)

        snap(page, "01_step1_filled")

        page.get_by_role("button", name="Далее", exact=True).click()
        page.wait_for_timeout(2_500)
        snap(page, "02_step2_route")

        # Try to select a route — list buttons with INTERNAL or Active
        # From step 2 — the page should show route templates
        # Click first available route option
        try:
            # Routes likely shown as cards. Let's try clicking by heading
            options = page.get_by_role("main").get_by_role("button").all()
            print(f"Step 2 buttons count: {len(options)}")
            for i, b in enumerate(options[:30]):
                txt = (b.text_content() or "")[:80]
                print(f"  [{i}] {txt!r}")
        except Exception as e:
            print(f"Step 2 listing error: {e}")

        page.close()
        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
