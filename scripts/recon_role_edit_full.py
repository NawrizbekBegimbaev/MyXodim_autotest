"""Подробный recon edit-диалога роли + delete confirmation."""

from __future__ import annotations

import os
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
    (OUT / f"role_full_{label}.yaml").write_text(page.locator("body").aria_snapshot())


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

        page.goto(f"{CLIENT_URL}/roles", wait_until="networkidle")
        page.wait_for_timeout(2_000)

        # Click Edit на первой data-row
        first_data_row = page.get_by_role("row").nth(1)
        first_data_row.get_by_role("button", name="Редактировать").click()
        page.wait_for_timeout(1_500)
        snap(page, "edit_full")
        # Извлекаем диалог и его структуру
        dialogs = page.get_by_role("dialog").all()
        for i, d in enumerate(dialogs):
            (OUT / f"role_full_dialog_{i}.yaml").write_text(d.aria_snapshot())

        page.close()
        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
