"""BRD 1.0 §6.4 — Event Queue Pull Model тесты.

Все тесты skipped пока BUG-011/012/013 не починены.
"""

import pytest

pytestmark = [
    pytest.mark.skip(reason="BUG-011/012/013: Event Queue not ready (recon 2026-05-26)"),
    pytest.mark.needs_events_ui,
]


def test_mock1c_events_page_opens() -> None:
    """Mock 1C: таб 'События' открывается, виден heading + table."""


def test_mock1c_events_table_has_all_columns() -> None:
    """Mock 1C: таблица содержит sequenceNumber/timestamp/type/payload/status."""


def test_mock1c_events_poll_button_present() -> None:
    """Mock 1C: кнопка 'Опросить HUB' видна или есть auto-loop indicator."""


def test_event_appears_after_document_completion() -> None:
    """BRD §6.4: после document.completed event появляется в Mock 1C."""


def test_event_delete_removes_from_queue() -> None:
    """BRD §6.4 retention: delete row removes event from queue."""


def test_event_sequence_number_strictly_monotonic() -> None:
    """BRD §6.4: sequenceNumber всегда возрастает."""


def test_event_idempotency_after_param() -> None:
    """BRD §6.4: after cursor controls repeated delivery."""


def test_event_tenant_rls_isolation() -> None:
    """BRD §6.4 RLS: tenant A не видит события tenant B."""


def test_event_invalid_after_seq_rejected_or_handled() -> None:
    """after=-1/string/999999 обрабатываются graceful."""


def test_event_auth_required() -> None:
    """Event Queue UI/API path requires integration auth."""


def test_long_poll_returns_within_wait_seconds() -> None:
    """Empty queue + waitSeconds=2 returns within the requested wait window."""


def test_long_poll_returns_immediately_when_event_arrives() -> None:
    """waitSeconds=30 returns early when a matching event arrives."""

