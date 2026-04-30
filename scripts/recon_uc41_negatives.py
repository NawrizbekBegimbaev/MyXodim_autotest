"""Полный recon негативных сценариев UC-4.1.

Создаём anchor-компанию, потом по каждому кейсу: заполняем форму,
жмём Создать, снимаем snapshot + перехватываем API-ответ.
"""

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
api_log: list[str] = []


def rd(n: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def valid_pinfl() -> str:
    return f"{secrets.randbelow(6) + 1}{rd(13)}"


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"neg_{label}_url.txt").write_text(page.url)
    (OUT / f"neg_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def fill_form(
    page: Page,
    name: str,
    slug: str,
    inn: str,
    first: str,
    last: str,
    phone: str,
    pinfl: str,
) -> None:
    page.goto(f"{ADMIN_URL}/tenants/new", wait_until="networkidle")
    page.wait_for_timeout(1_000)
    page.get_by_role("textbox", name="Название компании").fill(name)
    page.get_by_role("textbox", name="Slug").fill(slug)
    page.get_by_role("textbox", name="ИНН").fill(inn)
    page.get_by_role("textbox", name="Имя").fill(first)
    page.get_by_role("textbox", name="Фамилия").fill(last)
    page.get_by_role("textbox", name="Телефон").fill(phone)
    page.get_by_role("textbox", name="ПИНФЛ").fill(pinfl)


def submit_and_snap(page: Page, label: str) -> None:
    page.get_by_role("button", name="Создать").click()
    page.wait_for_timeout(3_500)
    snap(page, label)


def main() -> None:
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
            lambda r: api_log.append(
                f"[{r.status} {r.request.method}] {r.url}\n  {r.text()[:300]}\n"
            )
            if "/api/v1/admin/tenants" in r.url
            else None,
        )

        # Login
        page.goto(f"{ADMIN_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Телефон").fill(ADMIN_PHONE)
        page.get_by_role("textbox", name="Пароль").fill(ADMIN_PASS)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        # Anchor: создаём 1 валидную компанию A
        anchor = {
            "name": f"[E2E anchor] {uuid.uuid4().hex[:6]}",
            "slug": f"e2e-anchor-{uuid.uuid4().hex[:6]}",
            "inn": rd(9),
            "first": "Тест",
            "last": "Якорь",
            "phone": f"905{rd(7)}",
            "pinfl": valid_pinfl(),
        }
        api_log.append("--- ANCHOR ---")
        fill_form(page, **anchor)
        submit_and_snap(page, "00_anchor_create")

        # 1. Дубль ИНН
        api_log.append("--- DUP INN ---")
        fill_form(
            page,
            name=f"[E2E] dup_inn {uuid.uuid4().hex[:6]}",
            slug=f"e2e-dup-inn-{uuid.uuid4().hex[:6]}",
            inn=anchor["inn"],
            first="Дубль",
            last="ИНН",
            phone=f"905{rd(7)}",
            pinfl=valid_pinfl(),
        )
        submit_and_snap(page, "01_dup_inn")

        # 2. Дубль slug
        api_log.append("--- DUP SLUG ---")
        fill_form(
            page,
            name=f"[E2E] dup_slug {uuid.uuid4().hex[:6]}",
            slug=anchor["slug"],
            inn=rd(9),
            first="Дубль",
            last="Слаг",
            phone=f"905{rd(7)}",
            pinfl=valid_pinfl(),
        )
        submit_and_snap(page, "02_dup_slug")

        # 3. Дубль телефона
        api_log.append("--- DUP PHONE ---")
        fill_form(
            page,
            name=f"[E2E] dup_phone {uuid.uuid4().hex[:6]}",
            slug=f"e2e-dup-phone-{uuid.uuid4().hex[:6]}",
            inn=rd(9),
            first="Дубль",
            last="Телефон",
            phone=anchor["phone"],
            pinfl=valid_pinfl(),
        )
        submit_and_snap(page, "03_dup_phone")

        # 4. Цифры в Имя
        api_log.append("--- DIGITS IN FIRST NAME ---")
        fill_form(
            page,
            name=f"[E2E] digits {uuid.uuid4().hex[:6]}",
            slug=f"e2e-digits-{uuid.uuid4().hex[:6]}",
            inn=rd(9),
            first="Имя123",
            last="Тест",
            phone=f"905{rd(7)}",
            pinfl=valid_pinfl(),
        )
        # Tab + click
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
        submit_and_snap(page, "04_digits_in_name")

        # 5. Невалидный ИНН (буквы)
        api_log.append("--- INVALID INN LETTERS ---")
        fill_form(
            page,
            name=f"[E2E] inv_inn {uuid.uuid4().hex[:6]}",
            slug=f"e2e-inv-inn-{uuid.uuid4().hex[:6]}",
            inn="abcdefghi",
            first="Тест",
            last="Тест",
            phone=f"905{rd(7)}",
            pinfl=valid_pinfl(),
        )
        submit_and_snap(page, "05_inn_letters")

        # 6. Невалидный ИНН (5 цифр)
        api_log.append("--- INN 5 DIGITS ---")
        fill_form(
            page,
            name=f"[E2E] short_inn {uuid.uuid4().hex[:6]}",
            slug=f"e2e-short-inn-{uuid.uuid4().hex[:6]}",
            inn="12345",
            first="Тест",
            last="Тест",
            phone=f"905{rd(7)}",
            pinfl=valid_pinfl(),
        )
        submit_and_snap(page, "06_inn_short")

        # 7. ПИНФЛ начинается с 7 (NOT 1-6)
        api_log.append("--- PINFL FIRST != 1-6 ---")
        fill_form(
            page,
            name=f"[E2E] bad_pinfl {uuid.uuid4().hex[:6]}",
            slug=f"e2e-bad-pinfl-{uuid.uuid4().hex[:6]}",
            inn=rd(9),
            first="Тест",
            last="Тест",
            phone=f"905{rd(7)}",
            pinfl=f"7{rd(13)}",
        )
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
        submit_and_snap(page, "07_bad_pinfl_start")

        # 8. Пустые обязательные поля — открыть форму, ничего не вводить, нажать Создать
        api_log.append("--- ALL EMPTY ---")
        page.goto(f"{ADMIN_URL}/tenants/new", wait_until="networkidle")
        page.wait_for_timeout(1_000)
        snap(page, "08a_empty_initial")
        page.get_by_role("button", name="Создать").click()
        page.wait_for_timeout(2_000)
        snap(page, "08b_empty_after_submit")

        (OUT / "neg_api.txt").write_text("\n".join(api_log))
        page.close()
        ctx.close()
        browser.close()

    print("Done")


if __name__ == "__main__":
    main()
