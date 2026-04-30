"""Recon: клик "Отключить" в /tenants — есть ли confirmation? Как меняется статус?"""

from __future__ import annotations

import os
import secrets
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
ADMIN_PHONE = os.environ["SUPER_ADMIN_PHONE"]
ADMIN_PASS = os.environ["SUPER_ADMIN_PASSWORD"]

OUT = Path("recon")


def rd(n: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"disable_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    api_log: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()
        page.on(
            "response",
            lambda r: api_log.append(f"[{r.status} {r.request.method}] {r.url}\n  {r.text()[:300]}\n")
            if "/api/v1/admin/tenants" in r.url
            else None,
        )

        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        # Идём на /tenants — берём первую попавшуюся [E2E] компанию из списка
        page.goto(f"{ADMIN_URL}/tenants", wait_until="networkidle")
        page.wait_for_timeout(3_000)
        snap(page, "01_list_before")

        # Дождаться видимости первой data row
        from playwright.sync_api import expect

        first_data = page.get_by_role("row").nth(1)
        expect(first_data).to_be_visible(timeout=15_000)

        rows = page.get_by_role("row").all()
        import sys

        print(f"Total rows: {len(rows)}", flush=True)
        sys.stdout.flush()
        for i, r in enumerate(rows[:5]):
            txt = (r.text_content() or "")[:80]
            print(f"  [{i}] {txt}", flush=True)
            for b in r.get_by_role("button").all():
                print(f"      button: '{b.text_content()}'", flush=True)

        # "Отключить" — это switch (toggle), не button. По одному на каждую data row.
        target_text = page.get_by_role("row").nth(1).text_content() or ""
        page.get_by_role("switch").nth(0).click(timeout=10_000)
        page.wait_for_timeout(3_000)
        snap(page, "03_after_disable")

        # Текст target_row должен начинаться с slug — извлечём его
        # Структура: name slug inn users status date action
        # Например: [E2E] 0f1939 e2e-0f1939 107909734 2 Активна 28.04.2026 Отключить
        # Имя начинается с "[E2E] "
        import re

        m = re.match(r"(\[E2E\] [a-f0-9]{6})", target_text)
        if m:
            company_name = m.group(1)
            print(f"Disabled: {company_name}")

            # Ищем эту же компанию в списке после disable
            page.goto(f"{ADMIN_URL}/tenants", wait_until="networkidle")
            page.wait_for_timeout(2_000)
            snap(page, "04_list_after_disable")

            # Если есть кнопка "Включить" — кликаем
            try:
                page.get_by_role("row").filter(has_text=company_name).first.get_by_role(
                    "button", name="Включить"
                ).click(timeout=3_000)
                page.wait_for_timeout(2_500)
                snap(page, "05_after_reenable")
            except Exception:
                pass

        (OUT / "disable_api.txt").write_text("\n".join(api_log))
        page.close()
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
