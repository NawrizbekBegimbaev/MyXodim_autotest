"""Recon: detail page компании, User menu, кнопка Назад/Отмена, Records per page,
pagination на /tenants, кнопка 'Все' на дашборде."""

from __future__ import annotations

import os
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
    (OUT / f"extras_{label}_url.txt").write_text(page.url)
    (OUT / f"extras_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)
        page.wait_for_timeout(1_500)

        # 1. Открыть форму /tenants/new и посмотреть кнопку Назад
        page.goto(f"{ADMIN_URL}/tenants/new", wait_until="networkidle")
        page.wait_for_timeout(1_000)
        snap(page, "01_form_buttons")

        # Click "Назад" → должен быть редирект
        page.get_by_role("button", name="Назад").click()
        page.wait_for_timeout(1_500)
        snap(page, "02_after_back")

        # 2. Открыть /tenants и проверить click по строке
        page.goto(f"{ADMIN_URL}/tenants", wait_until="networkidle")
        page.wait_for_timeout(2_500)
        snap(page, "03_list")

        # Берём первую data row
        rows = page.get_by_role("row").all()
        if len(rows) > 1:
            target = rows[1]
            txt = (target.text_content() or "")[:100]
            print(f"Will click row: {txt}", flush=True)
            target.click()
            page.wait_for_timeout(2_000)
            snap(page, "04_row_click")

        # 3. На detail page (если редирект случился)
        snap(page, "05_detail")

        # 4. User menu — кнопка "User menu"
        page.goto(f"{ADMIN_URL}/dashboard", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        try:
            page.get_by_role("button", name="User menu").click(timeout=3_000, force=True)
            page.wait_for_timeout(1_500)
            snap(page, "06_user_menu_after_click")
            # hover, ждать
            page.get_by_role("button", name="User menu").hover()
            page.wait_for_timeout(1_500)
            snap(page, "06b_user_menu_after_hover")
        except Exception as e:
            (OUT / "extras_06_user_menu_err.txt").write_text(str(e))

        # 5. Кнопка "Все" в "Недавние компании"
        page.goto(f"{ADMIN_URL}/dashboard", wait_until="networkidle")
        page.wait_for_timeout(1_000)
        try:
            page.get_by_role("button", name="Все").click(timeout=3_000)
            page.wait_for_timeout(1_500)
            snap(page, "07_all_recent")
        except Exception as e:
            (OUT / "extras_07_all_err.txt").write_text(str(e))

        # 6. Records per page combobox в /tenants
        page.goto(f"{ADMIN_URL}/tenants", wait_until="networkidle")
        page.wait_for_timeout(2_500)
        try:
            # accessible-name combobox: "Записей на странице: 25" (включает текущее)
            combo = page.get_by_role("combobox").last
            combo.click(timeout=3_000)
            page.wait_for_timeout(1_200)
            snap(page, "08_records_combo")
            # снимем listbox
            (OUT / "extras_08_listbox.yaml").write_text(
                page.get_by_role("listbox").aria_snapshot()
            )
        except Exception as e:
            (OUT / "extras_08_records_err.txt").write_text(str(e))

        page.close()
        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
