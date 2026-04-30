from typing import Self

from playwright.sync_api import Page


class BasePage:
    URL_PATH: str = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self, base_url: str) -> Self:
        self.page.goto(base_url.rstrip("/") + self.URL_PATH)
        self.wait_loaded()
        return self

    def wait_loaded(self) -> Self:
        self.page.wait_for_load_state("domcontentloaded")
        return self
