"""Полный прогон создания компании с заполнением реальных полей.
Цель: поймать момент появления ключа интеграции (toast/page/dialog)."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
ADMIN_PHONE = os.environ["SUPER_ADMIN_PHONE"]
ADMIN_PASS = os.environ["SUPER_ADMIN_PASSWORD"]

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"{label}_url.txt").write_text(page.url)
    (OUT / f"{label}_snapshot.yaml").write_text(page.locator("body").aria_snapshot())
    (OUT / f"{label}_text.txt").write_text(page.locator("body").inner_text())


def main() -> None:
    suffix = uuid.uuid4().hex[:6]
    company_name = f"[E2E recon] {suffix}"
    slug = f"e2e-recon-{suffix}"
    # Уникальный ИНН на основе timestamp
    inn = str(int(time.time()))[-9:]
    admin_phone_local = f"905{int(time.time()) % 1_000_000:06d}"
    pinfl = "".join(str((i * 3 + 1) % 10) for i in range(14))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        # Перехват API
        api_responses: list[str] = []

        def log_response(r: object) -> None:
            try:
                url = r.url  # type: ignore[attr-defined]
                if "/api/" in url:
                    body = ""
                    try:
                        body = r.text()[:500]  # type: ignore[attr-defined]
                    except Exception:
                        body = "<unreadable>"
                    api_responses.append(
                        f"{r.status} {r.request.method} {url}\n  body: {body}\n"  # type: ignore[attr-defined]
                    )
            except Exception:
                pass

        page.on("response", log_response)

        # Логин
        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        # На страницу новой компании
        page.get_by_role("button", name="Добавить компанию").click()
        page.wait_for_url("**/tenants/new", timeout=10_000)

        # Заполнение
        page.get_by_role("textbox", name="Название компании *").fill(company_name)
        page.get_by_role("textbox", name="Slug *").fill(slug)
        page.get_by_role("textbox", name="ИНН").fill(inn)
        page.get_by_role("textbox", name="Имя *").fill("Тест")
        page.get_by_role("textbox", name="Фамилия *").fill("Реконов")
        page.get_by_role("textbox", name="Телефон *").fill(admin_phone_local)
        page.get_by_role("textbox", name="ПИНФЛ").fill(pinfl)
        snap(page, "company_form_filled")

        page.get_by_role("button", name="Создать").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3_000)
        snap(page, "company_after_create")
        (OUT / "create_api_log.txt").write_text("\n".join(api_responses))

        # Прямой URL /tenants/{slug}
        page.goto(f"{ADMIN_URL}/tenants/{slug}", wait_until="networkidle")
        page.wait_for_timeout(2_000)
        snap(page, "company_by_slug")

        # Список компаний с network-логом
        page.goto(f"{ADMIN_URL}/tenants", wait_until="networkidle")
        page.wait_for_timeout(2_000)
        snap(page, "tenants_list")
        (OUT / "tenants_list_network.txt").write_text("\n".join(api_responses))

        page.close()
        ctx.close()
        browser.close()

    print(f"\nDone. Company: {company_name}, slug={slug}, admin=+998{admin_phone_local}")


if __name__ == "__main__":
    main()
