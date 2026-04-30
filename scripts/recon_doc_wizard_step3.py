"""Recon: пройти до step 3 (Проверка) и снять снимок."""

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
    (OUT / f"docw3_{label}.yaml").write_text(page.locator("body").aria_snapshot())


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

        # Step 1
        first = page.get_by_role("button").filter(
            has=page.get_by_role("heading", level=6)
        ).filter(has_text="INTERNAL").first
        first.click()
        page.wait_for_timeout(800)

        title = f"[E2E] Recon3 {secrets.token_hex(3)}"
        page.get_by_role("textbox", name="Заголовок").fill(title)
        page.get_by_role("textbox", name="Содержание").fill("recon3 e2e content")
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Далее", exact=True).click()
        page.wait_for_timeout(2_500)

        # Step 2: select route via combobox
        # Маршрут *
        route_cb = page.get_by_role("combobox", name="Маршрут")
        route_cb.click()
        page.wait_for_timeout(800)
        snap(page, "01_step2_route_open")
        # Click first option
        opts = page.get_by_role("option").all()
        print(f"route options: {len(opts)}")
        for i, o in enumerate(opts[:10]):
            print(f"  [{i}] {(o.text_content() or '')[:80]!r}")
        if len(opts) > 1:
            opts[1].click()  # skip placeholder
            page.wait_for_timeout(500)

        # Целевой филиал *
        # second combobox
        branch_cbs = page.get_by_role("combobox").all()
        print(f"comboboxes after route: {len(branch_cbs)}")
        if len(branch_cbs) >= 2:
            branch_cbs[-1].click()
            page.wait_for_timeout(800)
            bopts = page.get_by_role("option").all()
            print(f"branch options: {len(bopts)}")
            for i, o in enumerate(bopts[:10]):
                print(f"  [{i}] {(o.text_content() or '')[:80]!r}")
            if len(bopts) > 1:
                bopts[1].click()
                page.wait_for_timeout(500)

        snap(page, "02_step2_filled")
        page.get_by_role("button", name="Далее", exact=True).click()
        page.wait_for_timeout(2_500)
        snap(page, "03_step3_review")

        page.close()
        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
