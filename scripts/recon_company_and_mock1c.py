"""Длинная разведка: создаём компанию в Admin UI, копируем ключ, идём в Mock 1C,
снимаем экраны Должности и Сотрудники.

Создаёт ОДНУ тестовую компанию с префиксом [E2E recon]. Cleanup-тест её снесёт
позже по префиксу.
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
MOCK1C_URL = os.getenv("MOCK1C_URL", "https://dev-mock-1c.greatmall.uz")
ADMIN_PHONE = os.environ["SUPER_ADMIN_PHONE"]
ADMIN_PASS = os.environ["SUPER_ADMIN_PASSWORD"]

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"{label}_url.txt").write_text(page.url)
    (OUT / f"{label}_snapshot.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    suffix = uuid.uuid4().hex[:6]
    company_name = f"[E2E recon] {int(time.time())} {suffix}"
    inn = "".join(str((i * 7 + 3) % 10) for i in range(9))
    admin_phone = f"+99890{suffix}{int(time.time()) % 100:02d}"[:13]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )

        # === Admin UI: логин и создание компании ===
        page = ctx.new_page()
        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        page.get_by_role("button", name="Добавить компанию").click()
        page.wait_for_load_state("networkidle")
        snap(page, "company_modal_empty")

        # Снимем все textbox/комбо чтобы понять поля
        (OUT / "company_modal_textboxes.txt").write_text(
            "\n".join(
                tb.get_attribute("aria-label") or tb.get_attribute("placeholder") or "?"
                for tb in page.get_by_role("dialog").locator("input, textarea").all()
            )
        )

        # Заполнение — пробую известные поля
        dialog = page.get_by_role("dialog")
        # типичные имена — возьмём из snapshot после прогона
        try:
            dialog.get_by_label("Название").fill(company_name)
        except Exception:
            pass
        try:
            dialog.get_by_label("ИНН").fill(inn)
        except Exception:
            pass
        try:
            dialog.get_by_label("Телефон администратора").fill(admin_phone)
        except Exception:
            pass

        snap(page, "company_modal_filled")

        # Submit — кнопка может быть "Создать" / "Сохранить" / "Добавить"
        for btn_name in ("Создать", "Добавить", "Сохранить", "Создать компанию"):
            try:
                dialog.get_by_role("button", name=btn_name).first.click(timeout=2_000)
                break
            except Exception:
                continue

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2_000)
        snap(page, "company_after_submit")

        # Извлечь ключ интеграции (если он на экране)
        body_text = page.locator("body").inner_text()
        (OUT / "company_after_submit_text.txt").write_text(body_text)
        page.close()

        # === Mock 1C ===
        page = ctx.new_page()
        page.goto(MOCK1C_URL, wait_until="networkidle")
        snap(page, "mock1c_initial")
        page.close()

        ctx.close()
        browser.close()

    print(f"\nDone. Company: {company_name}")


if __name__ == "__main__":
    main()
