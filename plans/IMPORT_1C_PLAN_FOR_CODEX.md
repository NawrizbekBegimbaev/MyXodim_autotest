# Plan for Codex: Import 1C→HUB block (BRD 1.0 §6.4a)

> **Дата:** 2026-05-26
> **Recon-источник:** `recon/IMPORT_1C_RECON_2026-05-26.md`
> **Bug-кандидаты:** BUG-007..010 в `Bugs.txt`
> **Статус блока:** **BLOCKED** — UI отсутствует в Mock 1C и Client UI
> **Что делает Codex:** только placeholder-тесты (skip-only) + минимальный POM
>                       чтобы snapshot текущего состояния и подготовить
>                       structure для будущей имплементации.

## Контекст

BRD 1.0 §6.4a определяет endpoint `POST /api/v1/integration/documents`:
- multipart upload (file + JSON metadata)
- `externalId` — uniqueness key для idempotency
- `templateId` — опциональный
- `route` (routeId) — опциональный
- Без route → документ в статусе **"Черновик (импорт)"**
- С route → сразу "На рассмотрении" → стандартный workflow

**Текущее состояние UI (recon 2026-05-26):**
- Mock 1C UI **не имеет** таба "Документы" или "Импорт"
- Client UI **не имеет** колонки "Черновик (импорт)" в /documents
- JS-бандлы обоих UI не знают slot для импорта

См. `Bugs.txt` BUG-007..010 для детального описания gap'ов.

## Файлы для создания

### 1. `pages/mock1c/import_documents_page.py` (NEW — placeholder)

POM-заглушка с явным docstring "BRD §6.4a — UI ожидается, на 2026-05-26
ещё не имплементирован". Класс ImportDocumentsPage с минимальными
локаторами:

```python
"""BRD 1.0 §6.4a — Mock 1C: Импорт документов в HUB.

ВНИМАНИЕ: на 2026-05-26 этот раздел UI ещё не имплементирован в Mock 1C.
См. BUG-007 в Bugs.txt. Этот POM-класс — placeholder для будущей
имплементации; все локаторы могут быть None или менять структуру.

Когда фронт прилетит — обновить локаторы после повторного recon.
"""

from __future__ import annotations
from typing import Self
from playwright.sync_api import Locator, Page
from pages.base_page import BasePage


class ImportDocumentsPage(BasePage):
    """Раздел Mock 1C для импорта документов в HUB через /api/v1/integration/documents."""

    URL_PATH = "/documents"  # ожидается, recon 2026-05-26: redirects на /

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Placeholder локаторы — обновить после recon когда UI появится
        self._heading: Locator = page.get_by_role("heading", name="Импорт документов")
        self._upload_button: Locator = page.get_by_role("button", name="Импортировать в HUB")
        self._file_input: Locator = page.locator('input[type="file"]')
        self._external_id_input: Locator = page.get_by_label("externalId")
        self._template_select: Locator = page.get_by_label("Шаблон")
        self._route_select: Locator = page.get_by_label("Маршрут")
        self._submit_button: Locator = page.get_by_role("button", name="Импортировать")

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def upload_button(self) -> Locator:
        return self._upload_button
```

### 2. `tests/mock1c/test_import_documents.py` (NEW — skip-only placeholder)

Все тесты помечены `@pytest.mark.skip(reason="BUG-007: Mock 1C UI for document import not implemented yet (recon 2026-05-26)")`.

Покрытие (по плану — все skipped пока):

```python
"""BRD 1.0 §6.4a — Import 1C→HUB тесты.

Все тесты в этом файле helly skipped пока BUG-007 (Mock 1C UI gap) и
BUG-008 (Client UI gap) не починены. Структура подготовлена для быстрой
активации когда UI прилетит.

Когда снимать skip:
- BUG-007 fixed → активировать смок-тесты (страница открывается, форма видна)
- BUG-008 fixed → активировать positive (импортированный документ виден в Client UI)
- BUG-009 fixed → активировать API-probe sentinel (auth работает)
"""

import pytest


pytestmark = pytest.mark.skip(
    reason="BUG-007 + BUG-008: Import UI не имплементирован на 2026-05-26"
)


# === SMOKE ===

def test_mock1c_import_page_opens():
    """Mock 1C: таб 'Документы' / 'Импорт' открывается"""

def test_mock1c_import_form_has_required_fields():
    """Mock 1C: форма содержит file + externalId + submit"""


# === POSITIVE ===

def test_import_with_template_and_route_succeeds():
    """BRD §6.4a happy path: Mock 1C push с templateId+routeId →
    в Client UI /documents появляется документ "На рассмотрении" с
    меткой 'Источник: 1С'."""

def test_import_without_route_creates_draft():
    """BRD §6.4a: import без route → статус 'Черновик (импорт)' в Client UI."""

def test_import_idempotency_same_external_id():
    """BRD §6.4a: двойной POST с тем же externalId → один и тот же
    documentId в response, в Client UI один документ (не дубликат)."""

def test_user_picks_route_for_imported_draft():
    """BRD §6.4a: открыть 'Черновик (импорт)' в Client UI → wizard
    выбора маршрута → submit → статус 'На рассмотрении' → standard
    approve/sign chain работает."""


# === NEGATIVE ===

def test_import_with_invalid_file_format_rejected():
    """Не PDF/DOCX/JPG → 400 + UI error."""

def test_import_without_required_external_id_rejected():
    """Empty externalId → backend validation error."""

def test_import_with_non_existent_template_id_rejected():
    """templateId которого нет → 400/404."""
```

### 3. `data/i18n.py` UPDATE

Добавить ключи (используя паттерн `mock1c.import_documents.*` и
`client.documents.status.draft_import`):

```python
# Mock 1C — Импорт документов (BRD §6.4a, ожидается UI)
"mock1c.import_documents.title": "Импорт документов",
"mock1c.import_documents.tab_label": "Документы",
"mock1c.import_documents.upload_button": "Импортировать в HUB",
"mock1c.import_documents.file_label": "Файл документа",
"mock1c.import_documents.external_id_label": "externalId",
"mock1c.import_documents.template_label": "Шаблон (опционально)",
"mock1c.import_documents.route_label": "Маршрут (опционально)",
"mock1c.import_documents.submit": "Импортировать",
"mock1c.import_documents.success_toast": "Документ импортирован",

# Client UI — статус импортированного черновика
"client.documents.status.draft_import": "Черновик (импорт)",
"client.documents.source_1c_label": "Источник: 1С",
"client.documents.kanban_column.draft_import": "Черновик (импорт)",
```

### 4. `pytest.ini` UPDATE (если нужно)

Добавить marker если не существует:

```ini
markers =
    ...
    needs_import_ui: blocked by BUG-007/008 — Import 1C UI not implemented
```

Использовать в test_import_documents.py:
```python
pytestmark = [
    pytest.mark.skip(reason="..."),
    pytest.mark.needs_import_ui,
]
```

## Проверки

После создания файлов:
```bash
.venv/bin/ruff check pages/mock1c/import_documents_page.py tests/mock1c/test_import_documents.py
.venv/bin/python -m mypy --strict pages/mock1c/import_documents_page.py tests/mock1c/test_import_documents.py
.venv/bin/python -m pytest tests/mock1c/test_import_documents.py --collect-only
.venv/bin/python -m pytest tests/mock1c/test_import_documents.py --co -m "needs_import_ui"
```

Ожидаемо: 9 tests collected, все skipped (no fails).

## Что НЕ делать

- НЕ писать API-level тесты (нарушение UI-only правила CLAUDE.md §13)
- НЕ закрывать BUG-007..010 в Bugs.txt (это ответственность QA/PM)
- НЕ создавать integration_documents fixture (нет UI для setup)
- НЕ удалять существующие тесты Mock 1C

## После имплементации

Когда фронт-команда добавит UI:
1. Обнови `ImportDocumentsPage` локаторы по новой структуре (re-recon через MCP)
2. Сними `pytest.mark.skip` с smoke-тестов первым шагом
3. Активируй positive когда BUG-008 (Client UI статус) fixed
4. API-probe sentinel (negative) — когда BUG-009 (auth) задокументирован
