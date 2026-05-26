"""BRD 1.0 §6.4a — Import 1C→HUB тесты.

Все тесты skipped пока BUG-007 (Mock 1C UI gap) и BUG-008 (Client UI gap)
не починены. Структура подготовлена для активации после появления UI.
"""

from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.skip(
        reason="BUG-007 + BUG-008: Import UI not implemented on 2026-05-26"
    ),
    pytest.mark.needs_import_ui,
]


def test_mock1c_import_page_opens() -> None:
    """Mock 1C: таб 'Документы' / 'Импорт' открывается."""


def test_mock1c_import_form_has_required_fields() -> None:
    """Mock 1C: форма содержит file + externalId + submit."""


def test_import_with_template_and_route_succeeds() -> None:
    """BRD §6.4a: templateId+routeId → документ 'На рассмотрении'."""


def test_import_without_route_creates_draft() -> None:
    """BRD §6.4a: import без route → статус 'Черновик (импорт)'."""


def test_import_idempotency_same_external_id() -> None:
    """BRD §6.4a: тот же externalId не создаёт дубликат документа."""


def test_user_picks_route_for_imported_draft() -> None:
    """BRD §6.4a: imported draft can be routed and submitted from Client UI."""


def test_import_with_invalid_file_format_rejected() -> None:
    """Не PDF/DOCX/JPG → UI показывает ошибку импорта."""


def test_import_without_required_external_id_rejected() -> None:
    """Empty externalId → validation error."""


def test_import_with_non_existent_template_id_rejected() -> None:
    """templateId которого нет → UI показывает backend validation error."""

