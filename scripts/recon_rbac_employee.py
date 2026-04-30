"""Recon: проверить может ли свежесозданный Сотрудник залогиниться по OTP
и какие пункты меню он видит.
"""

from __future__ import annotations

import os
import secrets as _s
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

CLIENT_URL = os.getenv("CLIENT_URL", "https://dev-hub-client.greatmall.uz")
ADMIN_PHONE = os.environ["CLIENT_SMOKE_PHONE"].removeprefix("+998")
TEST_OTP = os.environ.get("TEST_OTP", "123456")
ORG = os.environ.get("CLIENT_SMOKE_ORG", "QaTeam")

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"rbac_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # ---- 1. Login as admin and create new employee ----
        admin_ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = admin_ctx.new_page()
        page.goto(f"{CLIENT_URL}/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Номер телефона").fill(ADMIN_PHONE)
        page.get_by_role("button", name="Отправить код").click()
        page.wait_for_load_state("networkidle")
        page.get_by_role("textbox", name="Код подтверждения").fill(TEST_OTP)
        page.get_by_role("button", name="Войти").click()
        page.wait_for_url("**/tenant-select", timeout=15_000)
        page.get_by_role("button").filter(
            has=page.get_by_role("heading", name=ORG, level=6, exact=True)
        ).click()
        page.wait_for_url("**/dashboard", timeout=15_000)

        # Generate unique phone for new employee — full +998 format
        emp_phone_full = f"+99890{_s.randbelow(10_000_000):07d}"
        emp_phone_local = emp_phone_full.removeprefix("+998")
        suffix = uuid.uuid4().hex[:6]

        page.goto(f"{CLIENT_URL}/members", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        page.get_by_role("button", name="Добавить сотрудника", exact=True).click()
        page.wait_for_timeout(800)
        # Fill dialog (no exact=True, role-based name match)
        d = page.get_by_role("dialog", name="Добавить сотрудника")
        d.get_by_role("textbox", name="Имя").fill("RBAC")
        d.get_by_role("textbox", name="Фамилия").fill(f"[E2E] EmpRbac {suffix}")
        d.get_by_role("textbox", name="Телефон").fill(emp_phone_full)
        d.get_by_role("combobox", name="Роль").click()
        page.wait_for_timeout(400)
        page.get_by_role("listbox").get_by_role(
            "option", name="Сотрудник", exact=True
        ).click()
        page.wait_for_timeout(300)
        d.get_by_role("button", name="Добавить").click()
        page.wait_for_timeout(2_000)
        print(f"Created employee phone: +998{emp_phone_local}")

        admin_ctx.close()

        # ---- 2. Login as employee in fresh context ----
        emp_ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        ep = emp_ctx.new_page()
        ep.goto(f"{CLIENT_URL}/login", wait_until="networkidle")
        ep.get_by_role("textbox", name="Номер телефона").fill(emp_phone_local)
        ep.get_by_role("button", name="Отправить код").click()
        ep.wait_for_load_state("networkidle")
        ep.wait_for_timeout(2_000)
        snap(ep, "01_after_send_otp")
        try:
            ep.get_by_role("textbox", name="Код подтверждения").fill(TEST_OTP)
            ep.get_by_role("button", name="Войти").click()
            ep.wait_for_timeout(5_000)
            print(f"After OTP, URL: {ep.url}")
            snap(ep, "02_after_otp_submit")
            # If we reached tenant-select
            if "tenant-select" in ep.url:
                ep.get_by_role("button").filter(
                    has=ep.get_by_role("heading", name=ORG, level=6, exact=True)
                ).click()
                ep.wait_for_timeout(3_000)
                print(f"After tenant select, URL: {ep.url}")
                snap(ep, "03_after_tenant_select")
            # Try navigating to admin sections
            for path in ["/members", "/roles", "/positions", "/templates", "/dashboard"]:
                ep.goto(f"{CLIENT_URL}{path}", wait_until="networkidle")
                ep.wait_for_timeout(1_500)
                heading = ep.locator("h4").first
                title_text = heading.text_content() if heading.count() > 0 else ""
                print(f"{path} → URL={ep.url} heading='{title_text}'")
                snap(ep, f"04_path_{path.strip('/')}")
        except Exception as e:
            print(f"Login as employee failed: {e}")
            snap(ep, "X_error")

        emp_ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
