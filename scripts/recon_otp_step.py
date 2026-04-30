"""Разведка: что показывается в Client UI после "Отправить код"."""

from pathlib import Path

from playwright.sync_api import sync_playwright

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
        page = ctx.new_page()
        page.goto("https://dev-hub-client.greatmall.uz/login", wait_until="networkidle")
        page.get_by_role("textbox", name="Номер телефона").fill("900000000")
        page.get_by_role("button", name="Отправить код").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)  # одноразово в recon, не в тестах
        (OUT / "client_after_submit_url.txt").write_text(page.url)
        (OUT / "client_after_submit_snapshot.yaml").write_text(
            page.locator("body").aria_snapshot()
        )
        page.close()
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
