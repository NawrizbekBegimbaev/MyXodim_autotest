"""Recon /routes/new — кликаем на шаг, ищем panel настроек."""

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
    (OUT / f"rte_{label}.yaml").write_text(page.locator("body").aria_snapshot())
    (OUT / f"rte_{label}_url.txt").write_text(page.url)


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

        # /routes/new
        page.goto(f"{CLIENT_URL}/routes/new", wait_until="networkidle")
        page.wait_for_timeout(2_500)
        snap(page, "01_initial")

        # Click на default Шаг 1 → ищем panel настроек
        try:
            page.get_by_text("Шаг 1", exact=True).click(timeout=3_000)
            page.wait_for_timeout(2_000)
            snap(page, "02_after_step_click")
        except Exception as e:
            (OUT / "rte_02_err.txt").write_text(str(e))

        # Ищем button "Add step" или подобное
        all_buttons_in_main = page.get_by_role("main").get_by_role("button").all()
        names = [
            (b.get_attribute("aria-label") or b.text_content() or "?")[:60]
            for b in all_buttons_in_main
        ]
        (OUT / "rte_03_main_buttons.txt").write_text("\n".join(f"- {n}" for n in names))

        page.close()
        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
