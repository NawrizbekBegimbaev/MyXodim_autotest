# Plan for Codex: HR-кабинет block (BRD 3.0 — Мой кабинет)

> **Дата:** 2026-05-26
> **Recon-источник:** `recon/HR_CABINET_RECON_2026-05-26.md`
> **Bug-кандидаты:** BUG-018..022 + DOC-002 в `Bugs.txt`
> **Статус блока:** **PARTIAL** — `/home` + `/payslip` имеют структуру (Update),
>                 `/work-schedule` + `/vacation` — degenerate stubs (Skip-only)
> **Что делает Codex:** Update home_page.py + payslip_page.py, skip-mark vacation/schedule.

## Контекст

BRD 1.0 §1 говорит "Out of scope: HR" (см. DOC-002), но BRD 3.0 описывает Мой кабинет с расчётным листом, графиком работы, отпуском.

Реальное состояние (recon 2026-05-26):
- **Backend `/api/v1/hr/*`** живой:
  - `GET /hr/payslips?page&size` → 200 пустой
  - `GET /hr/vacation-balance` → 404 `HR_VACATION_BALANCE_NOT_FOUND` (contractual empty)
  - `GET /hr/work-schedule` → 404 `HR_WORK_SCHEDULE_NOT_FOUND`
  - `GET /hr/payslips/latest` → **500** (BUG-019)
  - `GET /hr/vacation/requests` → **500** (BUG-020)
- **Frontend:**
  - `/home` — 5 виджетов рендерятся, HR-три "Нет данных" (но widget есть)
  - `/payslip` — two-panel viewer skeleton, empty
  - `/work-schedule`, `/vacation` — **degenerate stubs** (один `<p>Нет данных</p>`) — см. BUG-021

Существующие POM от Codex 2026-05-19:
- `pages/client/home_page.py`
- `pages/client/payslip_page.py`
- `pages/client/work_schedule_page.py`
- `pages/client/vacation_page.py`

Все ВАЛИДНЫ (локаторы matchятся с DOM).

## Файлы для изменения

### 1. UPDATE `pages/client/home_page.py`

Добавить counter-геттеры + navigation методы для 5 виджетов:

```python
class HomePage(BasePage):
    URL_PATH = "/home"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Существующие локаторы — оставить
        self._heading = page.get_by_role("heading", level=1)
        self._widget_payslip = page.get_by_role("heading", name="Текущие начисления", level=6)
        self._widget_vacation = page.get_by_role("heading", name="Вам доступно дней отпуска", level=6)
        self._widget_schedule = page.get_by_role("heading", name="Ваш график работы", level=6)
        self._widget_my_docs = page.get_by_role("heading", name="Мои документы", level=6)
        self._widget_my_tasks = page.get_by_role("heading", name="Мои задачи", level=6)

        # NEW: CTA buttons виджетов (navigation)
        self._goto_payslip = page.get_by_role("button", name="Все расчётные листы →")
        self._goto_vacation = page.get_by_role("button", name="Подробнее →").nth(0)  # 1-й "Подробнее"
        self._goto_schedule = page.get_by_role("button", name="Подробнее →").nth(1)  # 2-й

        # NEW: counter-структуры "Мои документы" (4 sub-блока)
        self._my_docs_in_work = page.get_by_text("В работе", exact=True)
        self._my_docs_pending = page.get_by_text("В ожидании", exact=True)
        self._my_docs_completed = page.get_by_text("Завершено", exact=True)
        self._my_docs_rejected = page.get_by_text("Отказано", exact=True)

        # NEW: counter-структуры "Мои задачи" (3 sub-блока)
        self._my_tasks_pending = page.get_by_text("Ожидает согласования", exact=True)
        self._my_tasks_approved = page.get_by_text("Утверждено", exact=True)
        self._my_tasks_rejected = page.get_by_text("Отказано", exact=True).nth(1)  # disambig

    # Navigation методы
    def goto_payslip(self) -> Self:
        self._goto_payslip.click()
        return self

    def goto_vacation(self) -> Self:
        self._goto_vacation.click()
        return self

    def goto_schedule(self) -> Self:
        self._goto_schedule.click()
        return self
```

### 2. UPDATE `pages/client/payslip_page.py`

Сохранить как есть — структура skeleton корректна. НЕ добавлять download/period-filter методы (их нет в UI).

### 3. UPDATE `pages/client/work_schedule_page.py`

Добавить module-level комментарий:

```python
"""BRD 3.0 / Мой кабинет / График работы.

DOC-002 conflict: BRD 1.0 §1 заявляет HR Out-of-scope, BRD 3.0 включает.
На 2026-05-26 UI — degenerate stub (один <p>Нет данных</p>), см. BUG-021.
POM минимален пока feature не имплементирован.
"""
```

POM оставить как есть — `_empty` локатор валиден.

### 4. UPDATE `pages/client/vacation_page.py`

То же что work_schedule — комментарий про BUG-021, POM as-is.

### 5. UPDATE `tests/client/test_home.py` (если есть) или CREATE

Добавить 3 теста:

```python
def test_home_widgets_navigation_to_payslip(client_admin_page, settings):
    """BRD 3.0: клик виджета 'Текущие начисления' → /payslip"""
    home = HomePage(client_admin_page).goto(settings.client_url)
    home.goto_payslip()
    expect(client_admin_page).to_have_url(re.compile(r"/payslip$"))


def test_home_widgets_navigation_to_vacation(client_admin_page, settings):
    """BRD 3.0: клик 'Вам доступно дней отпуска' → /vacation"""
    home = HomePage(client_admin_page).goto(settings.client_url)
    home.goto_vacation()
    expect(client_admin_page).to_have_url(re.compile(r"/vacation$"))


def test_home_widgets_navigation_to_schedule(client_admin_page, settings):
    """BRD 3.0: клик 'Ваш график работы' → /work-schedule"""
    home = HomePage(client_admin_page).goto(settings.client_url)
    home.goto_schedule()
    expect(client_admin_page).to_have_url(re.compile(r"/work-schedule$"))


def test_home_my_documents_widget_has_4_status_counters(client_admin_page, settings):
    """BRD 3.0: виджет 'Мои документы' содержит 4 status sub-блока"""
    home = HomePage(client_admin_page).goto(settings.client_url)
    expect(home._my_docs_in_work).to_be_visible()
    expect(home._my_docs_pending).to_be_visible()
    expect(home._my_docs_completed).to_be_visible()
    expect(home._my_docs_rejected).to_be_visible()


def test_home_my_tasks_widget_has_3_status_counters(client_admin_page, settings):
    """BRD 3.0: виджет 'Мои задачи' содержит 3 status sub-блока"""
    home = HomePage(client_admin_page).goto(settings.client_url)
    expect(home._my_tasks_pending).to_be_visible()
    expect(home._my_tasks_approved).to_be_visible()
    # rejected — disambiguation между "Мои документы" и "Мои задачи"
    expect(home._my_tasks_rejected).to_be_visible()
```

### 6. UPDATE `tests/client/test_payslip.py` (если есть)

Оставить существующий empty_state test, добавить sentinel:

```python
@pytest.mark.skip(reason="BUG-019: GET /hr/payslips/latest 500 на пустых данных")
def test_payslip_page_does_not_crash_on_backend_500(client_admin_page, settings):
    """Sentinel BUG-019: при 500 от latest endpoint UI не должен крашиться"""
    payslip = PayslipPage(client_admin_page).goto(settings.client_url)
    expect(payslip.heading).to_be_visible()
    expect(payslip.empty_panel).to_be_visible()
```

### 7. CREATE / UPDATE `tests/client/test_work_schedule.py` + `test_vacation.py`

Добавить skip-only тесты:

```python
# test_work_schedule.py
import pytest

pytestmark = pytest.mark.skip(
    reason="BUG-021: /work-schedule degenerate stub без структуры (recon 2026-05-26)"
)


def test_work_schedule_has_calendar_or_pdf():
    """BRD 3.0: страница должна иметь календарь или PDF просмотр графика"""

def test_work_schedule_displays_current_period():
    """BRD 3.0: текущий период (месяц/неделя) должен быть выделен"""


# test_vacation.py
import pytest

pytestmark = pytest.mark.skip(
    reason="BUG-021: /vacation degenerate stub без структуры (recon 2026-05-26)"
)


def test_vacation_page_shows_days_balance():
    """BRD 3.0: счётчик 'Доступно дней отпуска'"""

def test_vacation_request_form_opens():
    """BRD 3.0: форма заявки на отпуск"""

def test_vacation_history_list_visible():
    """BRD 3.0: список предыдущих заявок"""
```

### 8. RBAC verify (BUG-CAND-F от агента — отдельная задача, не для этого блока)

Recon не проверил HR-кабинет под Менеджером/Директором/Сотрудником (был только Admin login). Это для отдельного блока RBAC.

## Проверки

```bash
.venv/bin/ruff check pages/client/home_page.py pages/client/payslip_page.py pages/client/work_schedule_page.py pages/client/vacation_page.py tests/client/test_home.py tests/client/test_payslip.py tests/client/test_work_schedule.py tests/client/test_vacation.py
.venv/bin/python -m mypy --strict pages/client/home_page.py tests/client/test_home.py
.venv/bin/python -m pytest tests/client/test_home.py tests/client/test_payslip.py tests/client/test_work_schedule.py tests/client/test_vacation.py --collect-only
.venv/bin/python -m pytest -m smoke tests/client/test_home.py tests/client/test_payslip.py --tb=short
```

Ожидаемо: smoke на /home + /payslip — passing; skip на /work-schedule + /vacation.

## Что НЕ делать

- НЕ удалять work_schedule_page.py / vacation_page.py — UI может расшириться
- НЕ добавлять download PDF methods в payslip (нет в UI)
- НЕ закрывать BUG-018..022 / DOC-002
- НЕ писать API tests на /hr/* (UI-only rule)
- НЕ убирать `_strict_console` fixture даже если HR засоряет console errors (BUG-022 нужен fix на стороне backend/frontend, не в test infra)
