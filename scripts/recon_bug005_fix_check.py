"""Проверка фикса BUG-005: создание сотрудника с дубль-телефоном.

Шаги:
1. Создаём жертву (роль: Сотрудник) с уникальным телефоном
2. Пытаемся создать ВТОРОГО с тем же телефоном но другим именем и ролью
3. Анализируем:
   - Что вернул бэк (200/4xx)?
   - Закрылся ли диалог?
   - Изменилась ли роль существующего юзера?
"""

from __future__ import annotations

import os
import secrets
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

CLIENT_URL = os.getenv("CLIENT_URL", "https://dev-hub-client.greatmall.uz")
PHONE = os.environ["CLIENT_SMOKE_PHONE"].removeprefix("+998")
TEST_OTP = os.environ.get("TEST_OTP", "123456")
ORG = "QaTeam"

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"bug005_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def rd(n: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def create_member(
    page: Page, first_name: str, last_name: str, phone: str, role: str
) -> None:
    page.get_by_role("button", name="Добавить сотрудника").click()
    page.wait_for_timeout(1_000)
    page.get_by_role("textbox", name="Имя *").fill(first_name)
    page.get_by_role("textbox", name="Фамилия *").fill(last_name)
    page.get_by_role("textbox", name="Телефон *").fill(phone)
    page.get_by_role("combobox", name="Роль *").click()
    page.wait_for_timeout(500)
    page.get_by_role("listbox").get_by_role("option", name=role, exact=True).click()
    page.get_by_role("button", name="Добавить").click()


def main() -> None:
    suffix = uuid.uuid4().hex[:6]
    victim_phone = f"+99890{rd(7)}"
    victim_first_name = f"Жертва{suffix}"
    victim_last_name = "[E2E] Виктимова"

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
            lambda r: api_log.append(
                f"[{r.status} {r.request.method}] {r.url}\n  {r.text()[:400]}\n"
            )
            if "/members" in r.url and r.request.method == "POST"
            else None,
        )

        # Login
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
        page.goto(f"{CLIENT_URL}/members", wait_until="networkidle")
        page.wait_for_timeout(1_500)

        # === Шаг 1: Создаём жертву (Сотрудник) ===
        api_log.append("--- CREATE VICTIM ---")
        create_member(
            page, victim_first_name, victim_last_name, victim_phone, "Сотрудник"
        )
        page.wait_for_timeout(3_000)
        snap(page, "01_after_victim_create")

        # === Шаг 2: Пытаемся создать ВТОРОГО с тем же телефоном но как Администратор ===
        # (worst case — попытка повысить или переписать)
        api_log.append("--- CREATE WITH DUPLICATE PHONE ---")
        create_member(
            page,
            "Атакующий",
            f"[E2E] Дубль{suffix}",
            victim_phone,  # тот же телефон!
            "Администратор",  # пытаемся повысить
        )
        page.wait_for_timeout(3_500)
        snap(page, "02_after_duplicate_attempt")

        # === Шаг 3: Закрываем dialog если открыт, ищем жертву в списке ===
        try:
            page.get_by_role("button", name="Отмена").first.click(timeout=2_000)
        except Exception:
            pass
        page.wait_for_timeout(1_000)

        # Поиск жертвы по телефону
        page.get_by_role("textbox", name="Поиск по имени или телефону...").fill(victim_phone)
        page.wait_for_timeout(2_000)
        snap(page, "03_after_search")

        (OUT / "bug005_api.txt").write_text("\n".join(api_log))
        page.close()
        ctx.close()
        browser.close()
    print(f"Done. Victim phone: {victim_phone}")


if __name__ == "__main__":
    main()
