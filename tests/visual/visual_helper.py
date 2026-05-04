"""Свой visual-regression helper (pytest-playwright не имеет встроенного).

Хранит baseline PNG'ы в `tests/visual/baselines/`. Первый прогон:
- если baseline нет → создаём + skip с сообщением "baseline created"
- если есть → сравниваем

Сравнение: pixel-diff через PIL.ImageChops.difference + считаем долю
не-нулевых пикселей. Если > threshold (по умолчанию 1%) — fail с
сохранением actual + diff PNG.

UPDATE_BASELINES=1 переопределяет любые baseline свежим снимком.
"""

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from playwright.sync_api import Page

BASELINE_DIR: Path = Path(__file__).parent / "baselines"
ARTIFACTS_DIR: Path = Path(__file__).parent / "artifacts"


def _diff_ratio(actual: Image.Image, baseline: Image.Image) -> float:
    """Доля пикселей которые отличаются от baseline (после difference())."""
    diff = ImageChops.difference(actual, baseline)
    bbox = diff.getbbox()
    if bbox is None:
        return 0.0
    # Считаем не-нулевые пиксели (сумма каналов > 0).
    pixels = list(diff.getdata())
    if not pixels:
        return 0.0
    differing = sum(
        1 for px in pixels if (sum(px) if isinstance(px, tuple) else px) > 0
    )
    return differing / len(pixels)


def assert_screenshot_matches(
    page: Page,
    name: str,
    threshold: float = 0.01,
    full_page: bool = True,
) -> None:
    """Проверяет что текущий скриншот совпадает с baseline.

    Args:
        name: имя файла без расширения (e.g. "admin-login")
        threshold: максимально допустимая доля изменённых пикселей (0.01 = 1%)
        full_page: full-page скриншот или только viewport
    """
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = BASELINE_DIR / f"{name}.png"

    actual_bytes = page.screenshot(full_page=full_page, animations="disabled")

    update_mode = os.environ.get("UPDATE_BASELINES", "0") == "1"

    if not baseline_path.exists() or update_mode:
        baseline_path.write_bytes(actual_bytes)
        action = "updated" if update_mode else "created"
        pytest.skip(f"Visual baseline {action}: {baseline_path.name}")

    actual_img = Image.open(BytesIO(actual_bytes))
    baseline_img = Image.open(baseline_path)

    if actual_img.size != baseline_img.size:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        actual_out = ARTIFACTS_DIR / f"{name}-actual.png"
        actual_out.write_bytes(actual_bytes)
        raise AssertionError(
            f"Visual size mismatch: actual={actual_img.size}, "
            f"baseline={baseline_img.size}. Actual saved to {actual_out}."
        )

    # Приводим к одному mode (RGB) для сравнения
    if actual_img.mode != baseline_img.mode:
        target_mode = "RGB"
        actual_img = actual_img.convert(target_mode)  # type: ignore[assignment]
        baseline_img = baseline_img.convert(target_mode)  # type: ignore[assignment]

    ratio = _diff_ratio(actual_img, baseline_img)
    if ratio > threshold:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        actual_out = ARTIFACTS_DIR / f"{name}-actual.png"
        diff_out = ARTIFACTS_DIR / f"{name}-diff.png"
        actual_out.write_bytes(actual_bytes)
        diff = ImageChops.difference(actual_img, baseline_img)
        diff.save(diff_out)
        raise AssertionError(
            f"Visual diff {ratio * 100:.2f}% > порог {threshold * 100:.2f}%. "
            f"Actual: {actual_out}. Diff: {diff_out}."
        )
