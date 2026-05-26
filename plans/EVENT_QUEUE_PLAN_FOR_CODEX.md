# Plan for Codex: Event Queue Pull Model block (BRD 1.0 §6.4)

> **Дата:** 2026-05-26
> **Recon-источник:** `recon/EVENT_QUEUE_RECON_2026-05-26.md`
> **Bug-кандидаты:** BUG-011..013 в `Bugs.txt`
> **Статус блока:** **BLOCKED** — backend 500 на всех endpoints +
>                  Mock 1C UI gap (нет таба "События")
> **Что делает Codex:** только placeholder POM + skip-only тесты.
>                       Структура чтобы быстро активировать когда
>                       фронт+бэк прилетят.

## Контекст

BRD 1.0 §6.4 определяет асимметричную интеграцию: HUB публикует события
в tenant-scoped очередь, 1С long-poll'ит их.

Endpoints:
- `GET /api/v1/integration/events?after={seq}&limit=100&waitSeconds=30`
- `DELETE /api/v1/integration/events/{id}`
- `POST /api/v1/integration/events:bulkDelete`
- `POST /api/v1/integration/events/{id}/ack`

Event types:
- `document.completed` (документ завершён в HUB → 1С обновляет реестр)
- `document.rejected`
- `document.cancelled`
- `document.exported`

Idempotency: 1С хранит у себя последний обработанный `sequenceNumber`,
передаёт в `after=` query-param при следующем poll. Retention 30 дней
by default, 1С сама удаляет события через DELETE.

**Текущее состояние UI (recon 2026-05-26):**
- Mock 1C UI: **нет** таба "События", JS-бандл не содержит long-poll loop
- Client UI: только косвенные статусы документа `Отправлен в 1С` /
  `Ошибка экспорта в 1С` (i18n strings present, но фильтр в /documents нет)
- Backend: все Event Queue endpoints возвращают 500 (см. BUG-011)

См. `Bugs.txt` BUG-011..013.

## Файлы для создания

### 1. `pages/mock1c/events_page.py` (NEW — placeholder)

POM-заглушка таба "События" Mock 1C UI:

```python
"""BRD 1.0 §6.4 — Mock 1C: Event Queue Consumer (long-polling).

ВНИМАНИЕ: на 2026-05-26 раздел UI не имплементирован. См. BUG-012.
Этот POM — placeholder. Локаторы могут поменяться когда фронт прилетит.

Ожидаемая структура UI:
    - Таб "События" в навигации
    - Кнопка "Опросить HUB" / auto-loop indicator
    - Таблица: sequenceNumber, timestamp, type, payload preview, status
    - Per-row "Обработать" / "Удалить" (DELETE event)
    - Bulk action "Удалить все обработанные"
"""

from __future__ import annotations
from typing import Self
from playwright.sync_api import Locator, Page
from pages.base_page import BasePage


class EventsPage(BasePage):
    """Mock 1C → раздел Event Queue (BRD §6.4)."""

    URL_PATH = "/events"  # ожидается, recon 2026-05-26 → redirects /

    COLUMNS: tuple[str, ...] = (
        "sequenceNumber",
        "timestamp",
        "type",
        "payload",
        "status",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role("heading", name="События")
        self._poll_button: Locator = page.get_by_role("button", name="Опросить HUB")
        self._table: Locator = page.get_by_role("main").get_by_role("table")
        self._bulk_delete: Locator = page.get_by_role("button", name="Удалить обработанные")

    @property
    def heading(self) -> Locator:
        return self._heading

    @property
    def poll_button(self) -> Locator:
        return self._poll_button

    @property
    def table(self) -> Locator:
        return self._table

    def row_by_sequence(self, seq: int) -> Locator:
        return self._table.locator("tbody tr").filter(has_text=str(seq))

    def process_row(self, seq: int) -> Self:
        row = self.row_by_sequence(seq)
        row.get_by_role("button", name="Обработать").click()
        return self

    def delete_row(self, seq: int) -> Self:
        row = self.row_by_sequence(seq)
        row.get_by_role("button", name="Удалить").click()
        return self
```

### 2. `tests/mock1c/test_events.py` (NEW — skip-only)

Все тесты `pytest.mark.skip` пока BUG-011/012 не починены:

```python
"""BRD 1.0 §6.4 — Event Queue Pull Model тесты.

ВСЕ тесты в этом файле helly skipped пока:
- BUG-011 (backend 500 на event endpoints)
- BUG-012 (Mock 1C UI gap — нет таба События)
- BUG-013 (auth scheme conflict)

Когда снимать skip:
- BUG-011 fixed → активировать API-probe sentinel
- BUG-012 fixed → активировать smoke (страница открывается, таблица видна)
- BUG-013 определён → активировать integration auth test
"""

import pytest


pytestmark = pytest.mark.skip(
    reason="BUG-011/012/013: Event Queue not ready (recon 2026-05-26)"
)


# === SMOKE ===

def test_mock1c_events_page_opens():
    """Mock 1C: таб 'События' открывается, виден heading + table"""

def test_mock1c_events_table_has_all_columns():
    """Mock 1C: таблица содержит sequenceNumber/timestamp/type/payload/status"""

def test_mock1c_events_poll_button_present():
    """Mock 1C: кнопка 'Опросить HUB' видна (или auto-loop indicator)"""


# === POSITIVE ===

def test_event_appears_after_document_completion():
    """BRD §6.4 happy path:
    1. В Client UI: создать документ → пройти весь workflow → завершить
    2. В Mock 1C: открыть таб 'События' → нажать 'Опросить HUB'
    3. В таблице появляется row с type='document.completed' +
       sequenceNumber + payload содержащий document_id
    """

def test_event_delete_removes_from_queue():
    """BRD §6.4 retention:
    1. Получить event
    2. Click 'Удалить' на row
    3. Re-poll → event не возвращается
    """

def test_event_sequence_number_strictly_monotonic():
    """BRD §6.4 sequenceNumber всегда возрастает: создать 3 документа
    последовательно, опросить → 3 события с seq N, N+1, N+2"""

def test_event_idempotency_after_param():
    """BRD §6.4 курсор:
    1. Получить событие seq=5
    2. Re-poll с after=5 → событий нет
    3. Re-poll с after=4 → возвращается seq=5 ещё раз
    """


# === NEGATIVE / SECURITY ===

def test_event_tenant_rls_isolation():
    """BRD §6.4 RLS: tenant A не видит события tenant B"""

def test_event_invalid_after_seq_rejected_or_handled():
    """after=-1, after=string, after=999999 — graceful behavior"""

def test_event_auth_required():
    """GET /events без auth → 401"""


# === LONG-POLL ===

def test_long_poll_returns_within_wait_seconds():
    """BRD §6.4: empty queue + waitSeconds=2 → response через ~2 сек,
    не моментально, не вечно"""

def test_long_poll_returns_immediately_when_event_arrives():
    """waitSeconds=30, но во время ожидания происходит document.completed
    → response возвращается сразу (< 5 сек), не ждёт 30"""
```

### 3. `data/i18n.py` UPDATE

```python
# Mock 1C — Event Queue (BRD §6.4)
"mock1c.events.title": "События",
"mock1c.events.tab_label": "События",
"mock1c.events.poll_button": "Опросить HUB",
"mock1c.events.bulk_delete_button": "Удалить обработанные",
"mock1c.events.col_seq": "sequenceNumber",
"mock1c.events.col_timestamp": "Дата/время",
"mock1c.events.col_type": "Тип",
"mock1c.events.col_payload": "Содержимое",
"mock1c.events.col_status": "Статус",
"mock1c.events.row_action_process": "Обработать",
"mock1c.events.row_action_delete": "Удалить",
"mock1c.events.status_new": "Новое",
"mock1c.events.status_processed": "Обработано",
"mock1c.events.empty_state": "Нет новых событий",

# Client UI — связанные статусы документа
# (уже есть в i18n: SENT_TO_1C, EXPORT_ERROR — не дублировать)
```

### 4. `pytest.ini` UPDATE (markers)

```ini
markers =
    ...
    needs_events_ui: blocked by BUG-011/012/013 — Event Queue not ready
```

## Проверки

```bash
.venv/bin/ruff check pages/mock1c/events_page.py tests/mock1c/test_events.py
.venv/bin/python -m mypy --strict pages/mock1c/events_page.py tests/mock1c/test_events.py
.venv/bin/python -m pytest tests/mock1c/test_events.py --collect-only
```

Ожидаемо: 12 tests collected, все skipped (no fails).

## Что НЕ делать

- НЕ писать API-level integration tests (UI-only)
- НЕ закрывать BUG-011..013
- НЕ создавать event-fixture (нет UI для setup)
- НЕ удалять существующие mock1c тесты

## После имплементации

Когда backend+frontend готовы:
1. Re-recon через MCP, обнови `EventsPage` локаторы
2. Сними `pytest.mark.skip` для smoke
3. Активируй positive — когда backend 200 + UI отдаёт rows
4. Активируй security (RLS) — параметризовано с 2 tenants
5. Активируй long-poll — самые сложные тесты, в конце
