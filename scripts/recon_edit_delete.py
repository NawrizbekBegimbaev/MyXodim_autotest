"""Recon: edit/delete dialogs для категорий, филиалов, ролей."""

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
    (OUT / f"ed_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    suffix = secrets.token_hex(3)
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

        # ===== Категории edit/delete =====
        page.goto(f"{CLIENT_URL}/categories", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        # Создаём категорию
        page.get_by_role("button", name="Добавить категорию").click()
        page.wait_for_timeout(1_000)
        cat_name = f"[E2E] Cat-edit {suffix}"
        page.get_by_role("dialog").get_by_role("textbox", name="Название").fill(cat_name)
        page.get_by_role("dialog").get_by_role("button", name="Создать", exact=True).click()
        page.wait_for_timeout(2_000)

        # Click "Редактировать" — ищем рядом с названием
        try:
            cat_node = page.get_by_text(cat_name, exact=True).first
            # Edit button рядом
            edit_btn = page.get_by_role("button", name="Редактировать").first
            edit_btn.click(timeout=3_000)
            page.wait_for_timeout(1_500)
            snap(page, "01_cat_edit_dialog")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception as e:
            (OUT / "ed_01_cat_edit_err.txt").write_text(str(e))

        # ===== Филиалы edit =====
        page.goto(f"{CLIENT_URL}/branches", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        page.get_by_role("button", name="Добавить филиал").first.click()
        page.wait_for_timeout(1_000)
        br_name = f"[E2E] Br-edit {suffix}"
        page.get_by_role("dialog").get_by_role("textbox", name="Название").fill(br_name)
        page.get_by_role("dialog").get_by_role("button", name="Создать", exact=True).click()
        page.wait_for_timeout(2_500)

        try:
            page.get_by_role("listitem").filter(
                has=page.get_by_role("heading", name=br_name, level=6, exact=True)
            ).get_by_role("button", name="Редактировать").click(timeout=3_000)
            page.wait_for_timeout(1_500)
            snap(page, "02_br_edit_dialog")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception as e:
            (OUT / "ed_02_br_edit_err.txt").write_text(str(e))

        # ===== Роли edit + delete =====
        page.goto(f"{CLIENT_URL}/roles", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        # Берём существующую роль (любую) — первая data-row
        first_data_row = page.get_by_role("row").nth(1)
        try:
            first_data_row.get_by_role("button", name="Редактировать").click(timeout=3_000)
            page.wait_for_timeout(1_500)
            snap(page, "03_role_edit_dialog")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception as e:
            (OUT / "ed_03_role_edit_err.txt").write_text(str(e))

        # Click Удалить — посмотреть confirmation
        try:
            page.get_by_role("row").nth(1).get_by_role(
                "button", name="Удалить"
            ).click(timeout=3_000)
            page.wait_for_timeout(1_500)
            snap(page, "04_role_delete_confirm")
            page.keyboard.press("Escape")
        except Exception as e:
            (OUT / "ed_04_role_delete_err.txt").write_text(str(e))

        page.close()
        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
