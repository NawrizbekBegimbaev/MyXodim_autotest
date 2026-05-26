"""BRD 3.0 / Мой кабинет / График работы."""

import pytest

pytestmark = pytest.mark.skip(
    reason="BUG-021: /work-schedule degenerate stub without structure (recon 2026-05-26)"
)


def test_work_schedule_has_calendar_or_pdf() -> None:
    """BRD 3.0: страница должна иметь календарь или PDF просмотр графика."""


def test_work_schedule_displays_current_period() -> None:
    """BRD 3.0: текущий период (месяц/неделя) должен быть выделен."""
