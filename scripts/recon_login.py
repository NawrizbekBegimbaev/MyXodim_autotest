"""Одноразовая разведка форм логина — снимаем aria-snapshot для починки локаторов.

Не часть тест-сьюта. Запуск: .venv/bin/python scripts/recon_login.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

TARGETS = [
    ("admin", "https://dev-hub-admin.greatmall.uz"),
    ("client", "https://dev-hub-client.greatmall.uz"),
    ("mock1c", "https://dev-mock-1c.greatmall.uz"),
]

OUT = Path("recon")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
            ignore_https_errors=True,
        )
        for label, url in TARGETS:
            page = ctx.new_page()
            page.goto(url, wait_until="networkidle")
            (OUT / f"{label}_url.txt").write_text(page.url)
            (OUT / f"{label}_title.txt").write_text(page.title())
            (OUT / f"{label}_snapshot.yaml").write_text(page.locator("body").aria_snapshot())
            (OUT / f"{label}_html.html").write_text(page.content())
            page.close()
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
