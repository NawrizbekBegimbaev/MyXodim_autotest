"""Раскрываем collapsible-группы в sidebar Client UI и снимаем подпункты."""

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
GROUPS = ["Кабинет", "Управление", "Настройки"]
EXTRA_PATHS = ["/inbox", "/documents", "/templates", "/branches", "/categories", "/roles", "/positions", "/organization", "/integration"]

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

        page.goto(f"{CLIENT_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Номер телефона").fill(PHONE)
        page.get_by_role("button", name="Отправить код").click()
        page.wait_for_load_state("networkidle")
        page.get_by_role("textbox", name="Код подтверждения").fill(TEST_OTP)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/tenant-select", timeout=15_000)
        page.get_by_role("button").filter(
            has=page.get_by_role("heading", name=ORG, level=6)
        ).click()
        page.wait_for_url("**/dashboard", timeout=15_000)
        page.wait_for_load_state("networkidle")

        # Раскрываем все группы
        for group_name in GROUPS:
            try:
                page.get_by_role("button", name=group_name, exact=True).click()
            except Exception as e:
                (OUT / f"sidebar_{group_name}_error.txt").write_text(str(e))

        page.wait_for_timeout(1_000)
        snap(page, "client_sidebar_expanded")

        # Все ссылки sidebar после раскрытия
        nav_links = page.get_by_role("navigation").get_by_role("link").all()
        link_data: list[tuple[str, str]] = []
        for link in nav_links:
            text = (link.text_content() or "?").strip()
            href = link.get_attribute("href") or "?"
            link_data.append((text, href))
        (OUT / "client_sidebar_all_links.txt").write_text(
            "\n".join(f"{t} -> {h}" for t, h in link_data)
        )

        # По каждому пути снимаем snapshot главного контейнера main
        for href in EXTRA_PATHS:
            slug = href.strip("/").replace("/", "_") or "root"
            label = f"client_{slug}"
            try:
                page.goto(f"{CLIENT_URL}{href}", wait_until="networkidle")
                page.wait_for_timeout(2_000)
                # снимаем только main (без sidebar) для компактности
                main = page.get_by_role("main")
                (OUT / f"{label}_url.txt").write_text(page.url)
                (OUT / f"{label}_main.yaml").write_text(main.aria_snapshot())
            except Exception as e:
                (OUT / f"{label}_error.txt").write_text(str(e))

        page.close()
        ctx.close()
        browser.close()

    print("Done")


if __name__ == "__main__":
    main()
