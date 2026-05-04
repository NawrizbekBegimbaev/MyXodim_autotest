"""Переключатели локали Admin/Client UI.

Admin UI: button с aria-label "Сменить язык" (или "Tilni o'zgartirish" на UZ),
          текст "ru"/"uz".
Client UI: button с aria-label "Switch language to O'zbekcha" / "...to Русский",
            текст "RU"/"UZ".

Mock 1C: отдельный тумблер UZ-only кнопки в шапке (не покрываем).
"""

from __future__ import annotations

import re
from typing import Self

from playwright.sync_api import Locator, Page


class AdminLocaleSwitcher:
    """Toggle между ru/uz в Admin UI.

    aria-label кнопки переведён на RU после i18n-batch (был "change language",
    стал "Сменить язык"). Локаторим по обоим.
    """

    _ARIA_RE = re.compile(r"^(Сменить язык|Tilni o'zgartirish|change language)$")

    def __init__(self, page: Page) -> None:
        self.page = page
        self._button: Locator = page.get_by_role("button", name=self._ARIA_RE)

    @property
    def button(self) -> Locator:
        return self._button

    def current(self) -> str:
        """Возвращает текущую локаль ('ru' или 'uz') по тексту кнопки."""
        return (self._button.text_content() or "").strip().lower()

    def switch_to(self, locale: str) -> Self:
        """Кликает кнопку пока текущая локаль не сравняется с целевой."""
        target = locale.lower()
        if target not in ("ru", "uz"):
            raise ValueError(f"Unknown locale: {locale}. Expected 'ru' or 'uz'.")
        # 2 клика максимум — toggle между двумя состояниями.
        for _ in range(2):
            if self.current() == target:
                return self
            self._button.click()
        if self.current() != target:
            raise RuntimeError(
                f"Не удалось переключить локаль на {target}. Текущая: {self.current()!r}"
            )
        return self


class ClientLocaleSwitcher:
    """Toggle между RU/UZ в Client UI.

    Кнопка имеет динамический aria-label: "Switch language to O'zbekcha"
    когда сейчас RU, и "Switch language to Русский" когда сейчас UZ.
    """

    _ARIA_PATTERN = "Switch language to"

    def __init__(self, page: Page) -> None:
        self.page = page
        # Локатор по фрагменту aria-label (общий для обоих состояний).
        self._button: Locator = page.locator(f"button[aria-label*=\"{self._ARIA_PATTERN}\"]")

    @property
    def button(self) -> Locator:
        return self._button

    def current(self) -> str:
        """RU или UZ — определяем по тексту кнопки."""
        return (self._button.text_content() or "").strip().upper()

    def switch_to(self, locale: str) -> Self:
        target = locale.upper()
        if target not in ("RU", "UZ"):
            raise ValueError(f"Unknown locale: {locale}. Expected 'RU' or 'UZ'.")
        for _ in range(2):
            if self.current() == target:
                return self
            self._button.click()
        if self.current() != target:
            raise RuntimeError(
                f"Не удалось переключить локаль на {target}. Текущая: {self.current()!r}"
            )
        return self
