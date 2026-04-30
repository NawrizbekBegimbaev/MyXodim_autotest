"""Recon: полный submit документа через wizard (3 шага)."""

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
    (OUT / f"docs_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    title = f"[E2E] Doc submit {secrets.token_hex(3)}"
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

        # Wizard
        page.goto(f"{CLIENT_URL}/documents/create", wait_until="networkidle")
        page.wait_for_timeout(2_000)

        # Step 1: select template + fill
        first_template = (
            page.get_by_role("button")
            .filter(has=page.get_by_role("heading", level=6))
            .filter(has_text="INTERNAL")
            .first
        )
        first_template.click()
        page.wait_for_timeout(500)
        page.get_by_role("textbox", name="Заголовок").fill(title)
        page.get_by_role("textbox", name="Содержание").fill("E2E содержание для submit")
        page.get_by_role("button", name="Далее", exact=True).click()
        page.wait_for_timeout(2_500)
        snap(page, "step2_route")

        # Step 2: выбрать первый маршрут
        try:
            route_btn = (
                page.get_by_role("main")
                .get_by_role("button")
                .filter(has=page.get_by_role("heading", level=6))
                .first
            )
            route_btn.click(timeout=3_000)
            page.wait_for_timeout(800)
        except Exception as e:
            (OUT / "docs_step2_err.txt").write_text(str(e))

        page.get_by_role("button", name="Далее", exact=True).click()
        page.wait_for_timeout(2_500)
        snap(page, "step3_review")

        # Step 3: submit
        for btn in ("Отправить", "Создать", "Submit"):
            try:
                page.get_by_role("button", name=btn, exact=True).click(timeout=2_000)
                break
            except Exception:
                continue
        page.wait_for_timeout(3_000)
        snap(page, "after_submit")
        print(f"After submit URL: {page.url}")
        print(f"Title: {title}")
        page.close()
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
