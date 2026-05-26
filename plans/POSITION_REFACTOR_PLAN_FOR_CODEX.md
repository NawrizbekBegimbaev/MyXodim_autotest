# Plan for Codex: Position Refactor block (BRD 3.0 — 3 separate entities)

> **Дата:** 2026-05-26
> **Recon-источник:** `recon/POSITION_REFACTOR_RECON_2026-05-26.md`
> **Bug-кандидаты:** BUG-014..017 + DOC-004 в `Bugs.txt`
> **Статус блока:** **READY** — UI существует (не blocked), нужен refactor существующих POM/тестов
> **Что делает Codex:** delete obsolete OrgPosition POM/tests + update PositionsPage/DepartmentsPage POM под текущий UI + расширить test coverage.

## Контекст

BRD 3.0 убрал концепт "Permanent Position" (аггрегат Сотрудник+Подразделение+Должность). Теперь 3 раздельные сущности:
- `/positions` → **Должности** (jobTitle)
- `/departments` → **Подразделения** (department, parent_id hierarchy)
- `/members` → **Сотрудники** (Employee + Person link)
- `/persons` → **Физлица** (Person, отдельный реестр)

**Dead route:** `/org-positions` возвращает 200 + пустой content (см. BUG-016).

**Текущее состояние (recon 2026-05-26):**
- `/positions`: heading "Должности", 4 колонки (Наименование, Код, Дата создания, Действия), фильтры Код + date range, row action "Открыть карточку"
- `/departments`: hierarchy через parentId, колонка "Филиал" (read-only), Add dialog без поля Branch (см. BUG-015)
- `/members` Add dialog: ПИНФЛ required, но Должность/Отдел не required (см. BUG-014)
- Route Builder step target: Роль / Сотрудник / Подразделение (НЕ Должность, НЕ Позиция)

## Файлы для изменения

### 1. DELETE obsolete code

#### `pages/client/organization_page.py`

Удалить класс `OrgPositionsPage` (по recon — строки 124-187). Также удалить связанный импорт `OrgPositionsPage` из `pages/client/organization_page.py` re-exports если есть.

#### `tests/client/test_inbox_org_misc.py`

Удалить 3 теста (по recon — строки 117-146):
- `test_org_positions_page_opens_*`
- `test_org_positions_*`
(точные имена — re-check через grep `grep -n "org_position" tests/client/test_inbox_org_misc.py`)

#### `data/i18n.py`

Удалить ключи `client.org_positions.*` (которых больше не используется).

#### `tests/regression/baselines/` (если есть)

Удалить snapshot файлы для /org-positions если есть в `recon/baseline/`.

### 2. UPDATE `pages/client/positions_page.py`

Текущий POM имеет `COLUMNS = ("Название должности", "Действия")` — устарел. Обновить:

```python
class PositionsPage(BasePage):
    """BRD 3.0: Должности (jobTitle) — отдельная сущность."""

    URL_PATH = "/positions"
    COLUMNS: tuple[str, ...] = (
        "Наименование",
        "Код",
        "Дата создания",
        "Действия",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading = page.get_by_role("heading", name="Должности", level=4)
        self._add_button = page.get_by_role("button", name="Добавить должность")
        self._search = page.get_by_placeholder("Поиск...")
        # NEW: фильтры
        self._code_filter = page.get_by_label("Код")
        self._date_from_filter = page.get_by_label("Дата с")
        self._date_to_filter = page.get_by_label("Дата по")
        self._reset_filters_button = page.get_by_role("button", name="Сбросить")
        self._table = page.get_by_role("main").get_by_role("table")

    # NEW: row action "Открыть карточку"
    def open_card(self, position_name: str) -> Self:
        row = self._table.locator("tbody tr").filter(has_text=position_name)
        row.get_by_role("button", name="Открыть карточку").click()
        return self

    # ... остальные методы как было
```

Также может потребоваться `PositionDetailPage` для row action "Открыть карточку" — отдельная карточка должности.

#### `pages/client/position_dialogs.py`

Текущий dialog возможно не имеет поля "Код" — добавить если recon подтвердил:

```python
class PositionCreateDialog(BasePage):
    # ...
    self._code_input = self._dialog.get_by_label("Код")  # NEW

    def fill_code(self, code: str) -> Self:
        self._code_input.fill(code)
        return self
```

### 3. UPDATE `pages/client/departments_page.py` + create `DepartmentCreateDialog`

DepartmentsPage должен иметь:
- Колонки: Наименование, Код, Родительское подразделение, Филиал, Действия
- Add button "Добавить подразделение"
- Hierarchy view (tree) — если есть в UI

`DepartmentCreateDialog` (NEW класс):
```python
class DepartmentCreateDialog(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog = page.get_by_role("dialog")
        self._name_input = self._dialog.get_by_label("Наименование*")
        self._parent_combo = self._dialog.get_by_label("Родительское подразделение")
        self._code_input = self._dialog.get_by_label("Код")
        # NOTE: BUG-015 — branch combobox отсутствует в текущем UI,
        # должен быть, но пока нет. Не добавлять локатор, ждать фикса.
        self._submit = self._dialog.get_by_role("button", name="Создать")
        self._cancel = self._dialog.get_by_role("button", name="Отмена")
```

### 4. UPDATE `pages/client/member_create_dialog.py`

Уточнить:
- ПИНФЛ — required (validation aware)
- Должность/Отдел — currently NOT required в UI (см. BUG-014), но тесты должны это проверить как known issue

### 5. UPDATE `pages/client/routes_page.py`

В `RouteEditorPage` добавить методы для выбора step target. По recon — варианты:
- "Роль для согласований"
- "Сотрудник"
- "Подразделение"

(Должности и Позиции — нет.)

```python
# В RouteStepPanel или RouteEditorPage
def select_target_role(self, role_name: str) -> Self:
    self._target_type_combo.click()
    self._page.get_by_role("option", name="Роль для согласований").click()
    self._target_value_combo.click()
    self._page.get_by_role("option", name=role_name).click()
    return self

def select_target_employee(self, employee_name: str) -> Self:
    # аналогично
    ...

def select_target_department(self, department_name: str) -> Self:
    # аналогично
    ...
```

### 6. Tests — UPDATE / ADD

#### `tests/client/test_positions.py`

Расширить:
- Новая колонка "Код" — `test_positions_table_has_code_column`
- Фильтры — `test_positions_filter_by_code`, `test_positions_filter_by_date_range`, `test_positions_reset_filters_clears_query`
- Row action — `test_positions_open_card_navigates_to_detail`
- Negative — `test_position_create_duplicate_code_rejected` (если backend rejects)

#### `tests/client/test_departments.py`

Добавить:
- `test_departments_table_has_branch_column`
- `test_department_create_dialog_opens`
- `test_department_create_with_parent_succeeds`
- `test_department_create_empty_name_rejected`
- **Skip с reason BUG-015:** `test_department_create_with_branch_selection` — UI ещё не имеет поля Branch

#### `tests/client/test_members.py`

Добавить:
- `test_member_create_without_pinfl_rejected` (BRD §3.6, ПИНФЛ обязателен)
- **Skip с reason BUG-014:**
  - `test_member_create_without_jobtitle_rejected_per_brd_3_6`
  - `test_member_create_without_department_rejected_per_brd_3_6`

#### `tests/client/test_routes_constructor.py`

- `test_route_step_target_combo_has_role_employee_department_options`
- `test_route_step_with_department_target_succeeds`
- **Skip с reason DOC-004:** `test_route_step_with_position_target` (Позиция как target удалена)

### 7. Memory update (НЕ Codex)

После изменений я обновлю:
- `memory/test_fixtures.md` — выкинуть упоминания /org-positions
- Можно создать `memory/position_refactor_2026-05-26.md` если хочешь зафиксировать как историческое событие

## Проверки

```bash
.venv/bin/ruff check pages/client/positions_page.py pages/client/departments_page.py pages/client/member_create_dialog.py pages/client/organization_page.py pages/client/routes_page.py tests/client/test_positions.py tests/client/test_departments.py tests/client/test_members.py tests/client/test_inbox_org_misc.py tests/client/test_routes_constructor.py
.venv/bin/python -m mypy --strict pages/ tests/
.venv/bin/python -m pytest tests/client/test_positions.py tests/client/test_departments.py tests/client/test_members.py tests/client/test_routes_constructor.py --collect-only
.venv/bin/python -m pytest -m smoke tests/client/test_positions.py tests/client/test_departments.py --tb=short
```

Ожидаемо: passing смок-тесты на /positions и /departments (UI работает), skipped тесты с явными BUG-XX/DOC-XXX reason'ами.

## Что НЕ делать

- НЕ восстанавливай OrgPositionsPage — концепт мёртв
- НЕ закрывай BUG-014..017 / DOC-004 в Bugs.txt
- НЕ добавляй поле Branch в DepartmentCreateDialog (BUG-015 — UI его не имеет, добавление сломает локатор)
- НЕ удаляй tests/client/test_categories.py (отдельный skip под BUG-010-archive)

## Регрессионные стражи (sentinel'ы)

Добавь эти тесты — они защитят от регрессий:

```python
# Sentinel для BUG-016 (dead route)
@pytest.mark.skip(reason="BUG-016: /org-positions всё ещё 200 на 2026-05-26")
def test_org_positions_route_returns_404_or_redirects():
    """BUG-016: legacy /org-positions должен 404 или redirect"""
    # Когда BUG-016 fixed — снять skip
    ...

# Sentinel для BUG-014
@pytest.mark.skip(reason="BUG-014: jobTitle/department не required в UI")
def test_member_create_dialog_has_required_jobtitle_per_brd_3_6():
    """BUG-014: Должность должна быть required (звёздочка + validation)"""
    ...
```
