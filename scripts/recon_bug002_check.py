"""Проверка статуса BUG-002 — обязательность ПИНФЛ на /tenants/new."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import Page, sync_playwright

from pages.admin.create_company_page import CreateCompanyPage
from pages.admin.login_page import AdminLoginPage

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "https://dev-hub-admin.greatmall.uz")
SUPER_PHONE = os.environ["SUPER_ADMIN_PHONE"]
SUPER_PASS = os.environ["SUPER_ADMIN_PASSWORD"]

OUT = Path("recon")


def snap(page: Page, label: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / f"bug002_{label}.yaml").write_text(page.locator("body").aria_snapshot())


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        # Login as super admin via POM
        AdminLoginPage(page).goto(ADMIN_URL).login(SUPER_PHONE, SUPER_PASS)
        page.wait_for_url("**/dashboard", timeout=15_000)

        create = CreateCompanyPage(page).goto(ADMIN_URL)
        page.wait_for_timeout(2_000)
        snap(page, "01_form_initial")

        # Inspect ПИНФЛ field - look for asterisk in label
        # ARIA snapshot will show "ПИНФЛ *" if marked required
        body = page.locator("body").aria_snapshot()
        # Find lines mentioning ПИНФЛ
        pinfl_lines = [ln for ln in body.split("\n") if "ПИНФЛ" in ln or "пинфл" in ln.lower()]
        print("--- Lines mentioning ПИНФЛ ---")
        for ln in pinfl_lines[:10]:
            print(f"  {ln.strip()}")
        print()

        # Network listener for POST /tenants
        last_resp: dict[str, object] = {"status": None, "body": ""}

        def on_response(resp: object) -> None:
            url = resp.url  # type: ignore[attr-defined]
            if "/admin/tenants" in url and resp.request.method == "POST":  # type: ignore[attr-defined]
                last_resp["status"] = resp.status  # type: ignore[attr-defined]
                try:
                    last_resp["body"] = resp.text()  # type: ignore[attr-defined]
                except Exception:
                    pass

        page.on("response", on_response)

        # Fill all fields EXCEPT ПИНФЛ
        import secrets
        import uuid as _u

        suffix = _u.uuid4().hex[:6]
        create.fill_company(
            name=f"[E2E BUG002] {suffix}",
            slug=f"e2e-bug002-{suffix}",
            inn="".join(str(secrets.randbelow(10)) for _ in range(9)),
        )
        create.fill_admin(
            first_name="Тест",
            last_name="BUG002",
            phone_local=f"90{''.join(str(secrets.randbelow(10)) for _ in range(7))}",
            pinfl="",  # ПИНФЛ — НЕ заполняем
        )
        page.wait_for_timeout(500)
        snap(page, "02_filled_no_pinfl")

        create.submit()
        page.wait_for_timeout(3_000)
        snap(page, "03_after_submit")

        print(f"--- POST response status: {last_resp.get('status')} ---")
        body_str = str(last_resp.get("body", ""))[:500]
        print(f"--- POST response body (first 500 chars) ---")
        print(body_str)
        print()

        # URL after submit?
        print(f"URL after submit: {page.url}")

        # Visible toasts / error messages
        notif = page.get_by_role("region", name="Notifications").inner_text() if (
            page.get_by_role("region", name="Notifications").count() > 0
        ) else ""
        print(f"--- Notifications text ---\n{notif[:500]}")

        ctx.close()
        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
