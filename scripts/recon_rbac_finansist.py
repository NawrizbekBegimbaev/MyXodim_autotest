"""Recon: создаём сотрудника с ролью 'Finansist' + должностью, логинимся
им и проверяем что он видит."""

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
    (OUT / f"finrole_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

        emp_phone_full = f"+99890{_s.randbelow(10_000_000):07d}"
        emp_phone_local = emp_phone_full.removeprefix("+998")
        suffix = uuid.uuid4().hex[:6]

        page.goto(f"{CLIENT_URL}/members", wait_until="networkidle")
        page.wait_for_timeout(1_500)
        page.get_by_role("button", name="Добавить сотрудника", exact=True).click()
        page.wait_for_timeout(800)
        d = page.get_by_role("dialog", name="Добавить сотрудника")
        d.get_by_role("textbox", name="Имя").fill("Финансист")
        d.get_by_role("textbox", name="Фамилия").fill(f"[E2E] FinTest {suffix}")
        d.get_by_role("textbox", name="Телефон").fill(emp_phone_full)

        # Open Role combobox and snapshot all options
        d.get_by_role("combobox", name="Роль").click()
        page.wait_for_timeout(500)
        snap(page, "01_role_options")
        role_opts = page.get_by_role("listbox").get_by_role("option").all()
        print(f"Role options ({len(role_opts)}):")
        for i, o in enumerate(role_opts):
            print(f"  [{i}] {(o.text_content() or '').strip()!r}")

        # Try to pick "Finansist" (case-insensitive search in option text)
        target_role: str | None = None
        for o in role_opts:
            txt = (o.text_content() or "").strip()
            if "finan" in txt.lower() or "финан" in txt.lower():
                target_role = txt
                o.click()
                break
        if target_role is None:
            print("No 'Finansist' role found — picking first non-Administrator role")
            for o in role_opts:
                txt = (o.text_content() or "").strip()
                if "Администратор" not in txt and "Сотрудник" not in txt and txt:
                    target_role = txt
                    o.click()
                    break
        print(f"Picked role: {target_role!r}")
        page.wait_for_timeout(400)

        # Now Position combobox
        d.get_by_role("combobox", name="Должность").click()
        page.wait_for_timeout(500)
        snap(page, "02_position_options")
        pos_opts = page.get_by_role("listbox").get_by_role("option").all()
        print(f"Position options ({len(pos_opts)}):")
        for i, o in enumerate(pos_opts[:20]):
            print(f"  [{i}] {(o.text_content() or '').strip()!r}")

        # Pick first non-empty position
        target_pos: str | None = None
        for o in pos_opts:
            txt = (o.text_content() or "").strip()
            if txt and "не выбран" not in txt.lower() and "выберите" not in txt.lower():
                target_pos = txt
                o.click()
                break
        print(f"Picked position: {target_pos!r}")
        page.wait_for_timeout(400)

        d.get_by_role("button", name="Добавить").click()
        page.wait_for_timeout(2_500)
        snap(page, "03_after_submit")
        print(f"Created employee phone: {emp_phone_full}, role={target_role}, pos={target_pos}")

        admin_ctx.close()

        # ---- Login as the new employee ----
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
        try:
            ep.get_by_role("textbox", name="Код подтверждения").fill(TEST_OTP)
            ep.get_by_role("button", name="Войти").click()
            ep.wait_for_timeout(4_000)
            print(f"After OTP, URL: {ep.url}")
            if "tenant-select" in ep.url:
                ep.get_by_role("button").filter(
                    has=ep.get_by_role("heading", name=ORG, level=6, exact=True)
                ).click()
                ep.wait_for_timeout(3_000)
            print(f"After tenant select, URL: {ep.url}")
            snap(ep, "04_dashboard_as_finansist")

            # Header role
            header_html = ep.locator("banner, header").first.inner_text()
            print(f"--- Header text ---\n{header_html[:400]}\n---")

            # Visible nav links
            ep.wait_for_timeout(800)
            for group in ("Кабинет", "Управление", "Настройки"):
                try:
                    ep.get_by_role("button", name=group, exact=True).click(timeout=2_000)
                except Exception:
                    pass
            ep.wait_for_timeout(500)
            nav_links = ep.get_by_role("navigation").get_by_role("link").all()
            print(f"--- Nav links ({len(nav_links)}) ---")
            for nl in nav_links:
                txt = (nl.text_content() or "").strip()
                if txt:
                    print(f"  {txt!r}")

            # Try forbidden URLs
            for path in ["/members", "/roles", "/positions", "/templates",
                         "/branches", "/categories", "/routes", "/organization", "/integration"]:
                ep.goto(f"{CLIENT_URL}{path}", wait_until="networkidle")
                ep.wait_for_timeout(1_200)
                heading = ep.locator("h4").first
                title_text = heading.text_content() if heading.count() > 0 else ""
                # Check for "Доступ запрещён" / 403 indicators
                body_txt = ep.locator("body").inner_text()[:200]
                print(f"{path:14s} → URL={ep.url[-60:]:60s} h4={(title_text or '')[:40]!r:42s}")
        except Exception as e:
            print(f"Login as employee failed: {e}")
            snap(ep, "X_error")

        emp_ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
