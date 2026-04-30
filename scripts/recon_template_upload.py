"""Recon шаблоны step 2: загрузка PDF после step 1."""

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
    (OUT / f"tu_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    title = f"[E2E] Tmpl-up {secrets.token_hex(3)}"
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

        page.goto(f"{CLIENT_URL}/templates", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        page.get_by_role("button", name="Добавить шаблон").click()
        page.wait_for_timeout(1_000)
        page.get_by_role("dialog").get_by_role("textbox", name="Название").fill(title)
        page.get_by_role("dialog").get_by_role("button", name="Создать", exact=True).click()
        page.wait_for_timeout(3_000)
        snap(page, "step2_after_step1")
        # URL?
        (OUT / "tu_step2_url.txt").write_text(page.url)

        page.close()
        ctx.close()
        browser.close()
    print(f"Done: {title}")


if __name__ == "__main__":
    main()
