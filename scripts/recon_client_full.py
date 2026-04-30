"""Полная разведка Client UI после выбора организации.

Логинимся +998913030519 → выбираем SecondQaTeam → снимаем главную + все
разделы из sidebar. Цель: понять структуру меню, URL, локаторы кнопок.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

CLIENT_URL = os.getenv("CLIENT_URL", "https://dev-hub-client.greatmall.uz")
PHONE = os.environ["CLIENT_SMOKE_PHONE"].removeprefix("+998")
TEST_OTP = os.environ.get("TEST_OTP", "123456")
ORG = "SecondQaTeam"

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"{label}_url.txt").write_text(page.url)
    (OUT / f"{label}_snapshot.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        # Логин и выбор орг
        page.goto(f"{CLIENT_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Номер телефона").fill(PHONE)
        page.get_by_role("button", name="Отправить код").click()
        page.wait_for_load_state("networkidle")
        page.get_by_role("textbox", name="Код подтверждения").fill(TEST_OTP)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/tenant-select", timeout=15_000)

        # Выбор SecondQaTeam
        page.get_by_role("button").filter(
            has=page.get_by_role("heading", name=ORG, level=6)
        ).click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2_000)
        snap(page, "client_home")

        # Извлекаем все ссылки sidebar и пробегаемся по ним
        nav_links = page.get_by_role("navigation").get_by_role("link").all()
        link_data = [
            (link.text_content() or "?", link.get_attribute("href") or "?")
            for link in nav_links
        ]
        (OUT / "client_sidebar_links.txt").write_text(
            "\n".join(f"{text.strip()} -> {href}" for text, href in link_data)
        )

        # По каждой ссылке снимем snapshot
        for text, href in link_data:
            if not href or href.startswith("#"):
                continue
            label = "client_section_" + (text.strip() or href.lstrip("/")).replace(
                " ", "_"
            ).replace("/", "")[:40]
            try:
                page.goto(f"{CLIENT_URL}{href}", wait_until="networkidle")
                page.wait_for_timeout(1_500)
                snap(page, label)
            except Exception as e:
                (OUT / f"{label}_error.txt").write_text(str(e))

        page.close()
        ctx.close()
        browser.close()

    print("Done")


if __name__ == "__main__":
    main()
