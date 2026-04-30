"""Расширенная разведка UC-3.6:
- негативные сценарии (дубль телефона, невалидное Имя, пустые поля)
- форма редактирования (клик "Редактировать" на строке)
- disable (клик "Отключить" — есть ли confirmation?)
"""

from __future__ import annotations

import os
import uuid
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
    (OUT / f"{label}_full.yaml").write_text(page.locator("body").aria_snapshot())


def login_and_open_members(page: Page) -> None:
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
    page.goto(f"{CLIENT_URL}/members", wait_until="networkidle")
    page.wait_for_timeout(1_500)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()
        login_and_open_members(page)

        # === Edit form (клик "Редактировать" на строке существующего юзера) ===
        page.get_by_role("row").filter(has_text="+998913030519").get_by_role(
            "button", name="Редактировать"
        ).click()
        page.wait_for_timeout(2_000)
        snap(page, "member_edit_form")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # === Disable (Отключить) — есть ли confirmation? ===
        # Чтобы не отключить реального юзера, попробуем на боте
        try:
            page.get_by_role("row").filter(has_text="Bot Workflow").get_by_role(
                "button", name="Отключить"
            ).click(timeout=3_000)
            page.wait_for_timeout(1_500)
            snap(page, "member_disable_confirm")
            # Если confirmation — закроем cancel
            for cancel_name in ("Отмена", "Cancel"):
                try:
                    page.get_by_role("button", name=cancel_name, exact=True).first.click(
                        timeout=1_500
                    )
                    break
                except Exception:
                    continue
        except Exception as e:
            (OUT / "member_disable_error.txt").write_text(str(e))

        # === Negative create: дубль телефона ===
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Добавить сотрудника").click()
        page.wait_for_timeout(1_500)
        page.get_by_role("textbox", name="Имя *").fill("Дубль")
        page.get_by_role("textbox", name="Фамилия *").fill(f"Тест{uuid.uuid4().hex[:4]}")
        page.get_by_role("textbox", name="Телефон *").fill("+998913030519")  # дубль
        page.get_by_role("combobox", name="Роль *").click()
        page.wait_for_timeout(500)
        page.get_by_role("listbox").get_by_role("option", name="Сотрудник").click()
        page.get_by_role("button", name="Добавить").click()
        page.wait_for_timeout(2_500)
        snap(page, "member_create_duplicate_phone")
        try:
            page.get_by_role("button", name="Отмена").first.click(timeout=1_500)
        except Exception:
            pass

        # === Negative create: цифры в Имя ===
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Добавить сотрудника").click()
        page.wait_for_timeout(1_500)
        page.get_by_role("textbox", name="Имя *").fill("Имя123")
        page.get_by_role("textbox", name="Фамилия *").fill("Фамилия")
        page.get_by_role("textbox", name="Телефон *").fill(
            f"+99890{uuid.uuid4().int % 10_000_000:07d}"
        )
        page.keyboard.press("Tab")
        page.wait_for_timeout(1_000)
        snap(page, "member_create_invalid_name")
        try:
            page.get_by_role("button", name="Отмена").first.click(timeout=1_500)
        except Exception:
            pass

        # === Negative create: пустые обязательные поля ===
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Добавить сотрудника").click()
        page.wait_for_timeout(1_500)
        page.get_by_role("button", name="Добавить").click()
        page.wait_for_timeout(1_500)
        snap(page, "member_create_empty")

        page.close()
        ctx.close()
        browser.close()

    print("Done")


if __name__ == "__main__":
    main()
