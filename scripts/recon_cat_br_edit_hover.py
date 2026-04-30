"""Edit для категорий/филиалов через hover."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

CLIENT_URL = os.getenv("CLIENT_URL", "https://dev-hub-client.greatmall.uz")
PHONE = os.environ["CLIENT_SMOKE_PHONE"].removeprefix("+998")
TEST_OTP = os.environ.get("TEST_OTP", "123456")
ORG = os.environ.get("CLIENT_SMOKE_ORG", "QaTeam")

OUT = Path("recon")


def main() -> None:
    suffix = secrets.token_hex(3)
    cat_name = f"[E2E] CatHover {suffix}"
    br_name = f"[E2E] BrHover {suffix}"

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

        # Категории — создаём + hover на узле + click edit
        page.goto(f"{CLIENT_URL}/categories", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        page.get_by_role("button", name="Добавить категорию").click()
        page.wait_for_timeout(1_000)
        page.get_by_role("dialog").get_by_role("textbox", name="Название").fill(cat_name)
        page.get_by_role("dialog").get_by_role("button", name="Создать", exact=True).click()
        page.wait_for_timeout(2_000)

        # Hover на узле категории в дереве
        cat_node = page.get_by_text(cat_name, exact=True).first
        cat_node.hover()
        page.wait_for_timeout(800)
        # Снимок hover-state
        OUT.mkdir(exist_ok=True)
        (OUT / "ed2_cat_hover.yaml").write_text(page.locator("body").aria_snapshot())

        # Click parent listitem-кнопки edit (рядом с paragraph узла)
        try:
            page.get_by_role("listitem").filter(
                has=page.get_by_text(cat_name, exact=True)
            ).get_by_role("button", name="Редактировать").click(timeout=3_000)
            page.wait_for_timeout(1_500)
            (OUT / "ed2_cat_edit_dialog.yaml").write_text(
                page.locator("body").aria_snapshot()
            )
        except Exception as e:
            (OUT / "ed2_cat_err.txt").write_text(str(e))

        page.close()
        ctx.close()
        browser.close()
    print(f"Done: cat={cat_name}, br={br_name}")


if __name__ == "__main__":
    main()
