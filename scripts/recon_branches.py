"""Recon /branches — форма создания филиала."""

from __future__ import annotations

import os
import secrets
import uuid
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
    (OUT / f"br_{label}_url.txt").write_text(page.url)
    (OUT / f"br_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    title = f"[E2E] Филиал {uuid.uuid4().hex[:6]}"

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

        page.goto(f"{CLIENT_URL}/branches", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        snap(page, "01_list")

        page.get_by_role("button", name="Добавить филиал").first.click()
        page.wait_for_timeout(1_500)
        snap(page, "02_dialog")

        dialog = page.get_by_role("dialog")
        try:
            dialog.get_by_role("textbox").first.fill(title)
            snap(page, "03_filled")
            for btn in ("Создать", "Добавить", "Сохранить"):
                try:
                    dialog.get_by_role("button", name=btn, exact=True).click(timeout=2_000)
                    break
                except Exception:
                    continue
            page.wait_for_timeout(2_500)
            snap(page, "04_after_create")
        except Exception as e:
            (OUT / "br_err.txt").write_text(str(e))

        page.close()
        ctx.close()
        browser.close()
    print(f"Done: {title}")


if __name__ == "__main__":
    main()
