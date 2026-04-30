"""Recon: создаём документ через wizard, отправляем на маршрут и смотрим
видим ли мы его в Inbox для approve/reject."""

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
    (OUT / f"inbx_{label}.yaml").write_text(page.locator("body").aria_snapshot())


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

        # Create document via wizard
        title = f"[E2E] InboxDoc {secrets.token_hex(3)}"
        page.goto(f"{CLIENT_URL}/documents/create", wait_until="networkidle")
        page.wait_for_timeout(2_000)

        # Step 1
        first = page.get_by_role("button").filter(
            has=page.get_by_role("heading", level=6)
        ).filter(has_text="INTERNAL").first
        first.click()
        page.wait_for_timeout(800)
        page.get_by_role("textbox", name="Заголовок").fill(title)
        page.get_by_role("textbox", name="Содержание").fill("inbox e2e content")
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Далее", exact=True).click()
        page.wait_for_timeout(2_500)

        # Step 2
        page.get_by_role("combobox", name="Маршрут").click()
        page.wait_for_timeout(400)
        opts = page.get_by_role("option").all()
        for o in opts:
            txt = (o.text_content() or "")
            if "Выберите" not in txt:
                o.click()
                break
        page.wait_for_timeout(400)
        cbs = page.get_by_role("combobox").all()
        cbs[-1].click()
        page.wait_for_timeout(400)
        bopts = page.get_by_role("option").all()
        for o in bopts:
            txt = (o.text_content() or "")
            if "Выберите" not in txt:
                o.click()
                break
        page.wait_for_timeout(400)
        page.get_by_role("button", name="Далее", exact=True).click()
        page.wait_for_timeout(2_500)

        # Step 3 — Отправить на маршрут
        page.get_by_role("button", name="Отправить на маршрут", exact=True).click()
        page.wait_for_timeout(4_000)
        snap(page, "01_after_submit")
        print(f"After submit URL: {page.url}")
        print(f"Document title: {title}")

        # Open inbox
        page.goto(f"{CLIENT_URL}/inbox", wait_until="networkidle")
        page.wait_for_timeout(3_000)
        snap(page, "02_inbox_list")

        # Try search
        search = page.get_by_role("textbox", name="Поиск по заголовку")
        search.fill(title.split("] ")[1])
        page.wait_for_timeout(1_500)
        snap(page, "03_inbox_searched")

        # Look for the document row and what action buttons are there
        rows = page.get_by_role("row").all()
        print(f"Inbox rows: {len(rows)}")
        for i, r in enumerate(rows[:6]):
            print(f"  [{i}] {(r.text_content() or '')[:120]!r}")

        # Click row to open doc detail or actions
        try:
            doc_link = page.get_by_role("link").filter(has_text=title.split("] ")[1]).first
            doc_link.click()
            page.wait_for_timeout(2_500)
            snap(page, "04_doc_detail")
            print(f"Doc detail URL: {page.url}")
            # List all buttons on doc detail
            btns = page.get_by_role("button").all()
            print(f"Doc detail buttons: {len(btns)}")
            for i, b in enumerate(btns[:30]):
                txt = (b.text_content() or "")[:80]
                if txt.strip():
                    print(f"  [{i}] {txt!r}")
        except Exception as e:
            print(f"Open detail err: {e}")

        page.close()
        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
