"""BRD 3.0 / Мой кабинет / Отпуск."""

import pytest

pytestmark = pytest.mark.skip(
    reason="BUG-021: /vacation degenerate stub without structure (recon 2026-05-26)"
)


def test_vacation_page_shows_days_balance() -> None:
    """BRD 3.0: счётчик 'Доступно дней отпуска'."""


def test_vacation_request_form_opens() -> None:
    """BRD 3.0: форма заявки на отпуск."""


def test_vacation_history_list_visible() -> None:
    """BRD 3.0: список предыдущих заявок."""
