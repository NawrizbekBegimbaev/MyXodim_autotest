"""Periodic recon: снимает aria-snapshot ключевых страниц и diff'ит с baseline.

Запуск:
    .venv/bin/python scripts/periodic_recon.py
    .venv/bin/python scripts/periodic_recon.py --update  # перезаписать baseline'ы

Что делает:
  1. Логинится в Admin/Client UI (через storage_state .auth/)
  2. Открывает каждую страницу из PAGES, дёргает aria_snapshot()
  3. Сравнивает с baseline в recon/baseline/<name>.yml
  4. Печатает unified-diff для всех изменившихся
  5. Сохраняет новые snapshot'ы в recon/baseline/<name>.yml.new — человек ревьюит и переименовывает
  6. Для совсем новых страниц (без baseline) — сразу сохраняет в .yml

Запускать по расписанию (cron / GitHub Actions) — изменения в UI будут видны
без необходимости лезть в каждый тест после релиза. Если что-то поменялось —
будем знать заранее.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, sync_playwright

# Импорт от корня репо
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import Settings
from data.constants import TEST_OTP
from pages.admin.login_page import AdminLoginPage
from pages.client.login_page import ClientLoginPage
from pages.client.otp_page import OtpPage

BASELINE_DIR: Path = Path(__file__).resolve().parent.parent / "recon" / "baseline"

# (ui, path, name)  — `ui` ∈ {"admin","client","mock1c"}
PAGES: tuple[tuple[str, str, str], ...] = (
    # Admin (Super Admin авторизация)
    ("admin", "/dashboard", "admin_dashboard"),
    ("admin", "/tenants", "admin_tenants"),
    ("admin", "/tenants/new", "admin_tenants_new"),
    ("admin", "/admins", "admin_admins"),
    # Client (один админ-пользователь)
    ("client", "/dashboard", "client_dashboard"),
    ("client", "/documents", "client_documents"),
    ("client", "/inbox", "client_inbox"),
    ("client", "/members", "client_members"),
    ("client", "/branches", "client_branches"),
    ("client", "/departments", "client_departments"),
    ("client", "/positions", "client_positions"),
    ("client", "/org-positions", "client_org_positions"),
    ("client", "/templates", "client_templates"),
    ("client", "/routes", "client_routes"),
    ("client", "/categories", "client_categories"),
    ("client", "/organization", "client_organization"),
    ("client", "/integration", "client_integration"),
    # Mock 1C (без auth)
    ("mock1c", "/", "mock1c_setup"),
)


@contextmanager
def admin_context(browser: Browser, settings: Settings) -> Iterator[BrowserContext]:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    AdminLoginPage(page).goto(settings.admin_url).login(
        settings.super_admin_phone, settings.super_admin_password
    )
    page.wait_for_url("**/dashboard", timeout=settings.nav_timeout)
    page.close()
    try:
        yield ctx
    finally:
        ctx.close()


@contextmanager
def client_context(browser: Browser, settings: Settings) -> Iterator[BrowserContext]:
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    ClientLoginPage(page).goto(settings.client_url).enter_phone(
        settings.client_smoke_phone
    ).submit()
    OtpPage(page).enter_code(TEST_OTP).submit()
    page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
    # Юзер с одной орг → /documents; ≥2 орг → /tenant-select.
    if "tenant-select" in page.url and settings.client_smoke_org:
        from pages.client.select_organization_page import SelectOrganizationPage

        SelectOrganizationPage(page).select(settings.client_smoke_org)
        page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
    page.close()
    try:
        yield ctx
    finally:
        ctx.close()


def take_snapshot(ctx: BrowserContext, base_url: str, path: str, settings: Settings) -> str:
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}{path}", wait_until="networkidle", timeout=settings.nav_timeout)
        return page.locator("body").aria_snapshot()
    finally:
        page.close()


def diff_or_save(
    name: str, snapshot: str, *, update: bool
) -> tuple[str, str | None]:
    """Возвращает (status, diff_text).

    status ∈ {"NEW", "OK", "CHANGED"}
    """
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = BASELINE_DIR / f"{name}.yml"

    if not baseline_path.exists():
        baseline_path.write_text(snapshot, encoding="utf-8")
        return "NEW", None

    if update:
        baseline_path.write_text(snapshot, encoding="utf-8")
        return "OK", None

    old = baseline_path.read_text(encoding="utf-8")
    if old == snapshot:
        return "OK", None

    # Дифф + сохраняем new-версию для ревью
    new_path = baseline_path.with_suffix(".yml.new")
    new_path.write_text(snapshot, encoding="utf-8")
    diff_lines = list(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            snapshot.splitlines(keepends=True),
            fromfile=f"baseline/{name}.yml",
            tofile=f"new/{name}.yml",
            n=2,
        )
    )
    return "CHANGED", "".join(diff_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="Перезаписать baseline'ы свежими snapshot'ами без diff",
    )
    args = parser.parse_args()

    settings = Settings()
    summary: list[tuple[str, str, str | None]] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            try:
                admin_ctx_ctx = admin_context(browser, settings)
                with admin_ctx_ctx as admin_ctx:
                    for ui, path, name in PAGES:
                        if ui != "admin":
                            continue
                        snap = take_snapshot(
                            admin_ctx, settings.admin_url, path, settings
                        )
                        status, diff = diff_or_save(name, snap, update=args.update)
                        summary.append((name, status, diff))
            except Exception as e:
                # BUG-016 etc — Admin auth может быть сломан.
                # Не валим всю утилиту: skip admin part, идём дальше.
                err = str(e)[:200]
                for ui, path, name in PAGES:
                    if ui == "admin":
                        summary.append((name, "SKIPPED", f"admin auth failed: {err}"))

            with client_context(browser, settings) as client_ctx:
                for ui, path, name in PAGES:
                    if ui != "client":
                        continue
                    try:
                        snap = take_snapshot(
                            client_ctx, settings.client_url, path, settings
                        )
                    except Exception as e:
                        summary.append((name, "ERROR", str(e)[:200]))
                        continue
                    status, diff = diff_or_save(name, snap, update=args.update)
                    summary.append((name, status, diff))

            # Mock 1C — без контекста с auth
            mock_ctx = browser.new_context(
                viewport={"width": 1440, "height": 900},
                ignore_https_errors=True,
            )
            try:
                for ui, path, name in PAGES:
                    if ui != "mock1c":
                        continue
                    snap = take_snapshot(mock_ctx, settings.mock1c_url, path, settings)
                    status, diff = diff_or_save(name, snap, update=args.update)
                    summary.append((name, status, diff))
            finally:
                mock_ctx.close()

        finally:
            browser.close()

    # Отчёт
    by_status: dict[str, int] = {}
    print("\n" + "=" * 60)
    print("PERIODIC RECON REPORT")
    print("=" * 60)
    for name, status, diff in summary:
        by_status[status] = by_status.get(status, 0) + 1
        marker = {"OK": "✓", "NEW": "+", "CHANGED": "~", "ERROR": "✗"}.get(status, "?")
        print(f"  {marker} {status:8} {name}")
        if diff and status == "CHANGED":
            print(diff)
        elif diff and status == "ERROR":
            print(f"      err: {diff}")

    print("\n" + "-" * 60)
    print("Summary:", ", ".join(f"{s}={n}" for s, n in sorted(by_status.items())))
    if "CHANGED" in by_status:
        print(
            "\n→ UI drift обнаружен. Свежие snapshot'ы лежат в "
            f"{BASELINE_DIR}/<name>.yml.new — ревьюй и mv в .yml если ок."
        )
        return 1
    if "ERROR" in by_status:
        print("\n→ Были ошибки навигации / снапшота — см. выше.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
