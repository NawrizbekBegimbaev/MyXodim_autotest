# BusinessHub E2E

E2E автотесты для BusinessHub (Admin UI / Client UI / Mock 1C).
Playwright + pytest, **UI-only** (никаких HTTP-вызовов из тестов — см. CLAUDE.md §13).

## Цифры здоровья

| Метрика | Значение | Заметка |
|---|---|---|
| Read-only passed | **159** | Всё что не зависит от admin auth |
| Visual regression | 3 | Pillow-based, baseline в `tests/visual/baselines/` |
| Регрессии на баги (xfail strict) | 4 | BUG-014×3 + BUG-015 (закрыт, оставлен страж) |
| Periodic recon | 18 страниц | aria-snapshot baseline в `recon/baseline/` |
| Smoke locale (UZ↔RU) | 7 | `tests/smoke/test_locale.py` |
| Регрессии role-refactor | 13 | BRD §2.3 — 4 системные роли |
| `wait_for_timeout` остаток | 73 | Все защищены (creates_data / e2e / polling) |
| Открытых багов | 6 | См. `Bugs.txt` |

## Стек

- Python 3.13
- Playwright (sync API) + pytest-playwright + Pillow (для visual)
- pytest, pytest-xdist, pytest-rerunfailures, pydantic-settings
- allure-pytest
- ruff + mypy strict

## Setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium

cp .env.example .env
# Заполни SUPER_ADMIN_PHONE, SUPER_ADMIN_PASSWORD, CLIENT_SMOKE_PHONE
```

## Профили: dev vs local

| Файл | Среда | URLs |
|---|---|---|
| `.env` | активный (по умолчанию dev) | `dev-hub-*.greatmall.uz` |
| `.env.local` | local docker-compose из `core` repo | `localhost:3040/3041/3042` |

```bash
cp .env .env.dev.bak  &&  cp .env.local .env  # → local
mv .env.dev.bak .env                            # → dev
```

**Локалка заблокирована BUG-016** — Admin auth (`+998991234567 / admin123`) даёт 401. Также не сидятся client-юзеры из README — нужно либо новые credentials, либо reseed.

## Запуск

```bash
# По маркерам
pytest -m smoke                            # ~13 тестов, ~30 сек
pytest -m "regression"                     # xfail-сторожа на открытые баги
pytest -m "visual"                         # pixel-baseline (3 теста)
pytest -m "not creates_data and not eimzo_local_only"  # полный read-only прогон

pytest -m e2e --headed                     # главный E2E (заморожен)
pytest -m "e2e and eimzo_local_only" --headed -p no:xdist  # с EIMZO

# По разделам
pytest tests/admin/                        # Admin UI
pytest tests/client/                       # Client UI
pytest tests/regression/                   # регрессионные на баги
pytest tests/visual/                       # visual diff vs baseline

# Один тест
pytest tests/admin/test_company_create.py::test_company_create_with_valid_data_returns_integration_key -v
```

## Маркеры

Все в `pytest.ini`:

| Маркер | Назначение |
|---|---|
| `smoke` | критичные базовые проверки |
| `positive` / `negative` | основные / ошибки |
| `edge_case` | граничные случаи из BRD §9 |
| `rbac` | проверка прав доступа |
| `e2e` | сквозной сценарий |
| `serial` | запускать последовательно (EIMZO, конфликты) |
| `eimzo_local_only` | требует физическую ЭЦП-флешку |
| `maintenance` | обслуживающие задачи |
| **`creates_data`** | **тест мутирует БД через UI — заморожен пока стенд общий** |
| **`regression`** | **xfail-страж на конкретный известный баг** |
| **`visual`** | **pixel-сравнение скриншотов с baseline** |
| **`allow_console_errors`** | **отключает console-guard для теста** |
| **`allow_uz_default`** | **отключает _force_ru_lang (для тестов которые проверяют UZ default)** |

## Console / network guard (autouse)

`conftest.py::_strict_console` — на каждом тесте вешает listeners:
- `console.error` → лог в stderr (через `BH_STRICT_CONSOLE=1` валит тест)
- `pageerror` → unhandled JS-исключения = всегда баг
- `[5xx]` от наших бэков → лог
- `[reqfailed]` (кроме `ERR_ABORTED` — нормальный reload-cancel) → лог

Strict-mode прогон:
```bash
BH_STRICT_CONSOLE=1 pytest -m smoke
```

Soft-mode (default) пишет в Allure attachments. Через guard уже найдены **BUG-012** (Mock 1C → 500) и **BUG-013** (ИНН=14 → 500).

## Force RU locale (autouse session)

`conftest.py::_force_ru_lang` — патчит `Browser.new_context` чтобы каждый контекст получал `init_script` ставящий `localStorage[admin-lang]=ru` и `localStorage[client-lang]=ru` ДО первой загрузки.

Без этого — после deploy 2026-05-04 фронт переехал на UZ default и все RU-ассерты ломаются. С этим — тесты locale-independent.

Opt-out: `@pytest.mark.allow_uz_default`.

## Что покрыто

### Smoke
- 3 health (Admin/Client/Mock1C доступны)
- Admin login → /dashboard
- Client login + OTP
- 7 locale (uz↔ru toggle на Admin/Client + проверка переводов)

### Read-only suite (~159 passed)
- **Admin UI** layout: tenants list/detail, /admins, /tenants/new, login boundary/security, widgets
- **Client UI** layout: documents (8 табов / 7 колонок), inbox, members, departments (NEW), positions, branches, categories, templates, routes, organization (табы), integration (hub), org-positions (с ручным созданием)
- **RBAC sidebar** (read-only) — все 12 пунктов меню для админа в 4 группах
- **Role refactor** (13 тестов) — 4 системные роли + старых нет

### Регрессии (xfail strict)
| ID | Описание | Статус |
|---|---|---|
| BUG-014 × 3 | Mixed UZ/RU — Adminlar / колонки UZ / Yopish-Yashirish | open |
| BUG-015 | Admin login phone без `+` | **FIXED** — страж остался |

### Visual regression (3)
Stable страницы без auth: Admin /login, Client /login, Mock 1C /. PIL-diff с threshold 1%.

### Periodic recon (18 страниц)
`scripts/periodic_recon.py` снимает aria-snapshot всех ключевых страниц, diff'ит с `recon/baseline/*.yml`. Запуск:
```bash
.venv/bin/python scripts/periodic_recon.py          # diff
.venv/bin/python scripts/periodic_recon.py --update  # пересоздать baseline
```

### CRUD-тесты (заморожены, `creates_data`)
~80 тестов написаны но не запускаются — стенд общий, нельзя пачкать БД. Размораживаются когда: (а) появится maintenance cleanup, (б) пофиксят BUG-016 для local стенда.

## Известные баги (см. `Bugs.txt`)

| ID | Severity | Кратко | Статус |
|---|---|---|---|
| BUG-002 | — | ПИНФЛ * + client-validation | ✅ FIXED 2026-04-30 |
| BUG-006 | Major | Фронт молча игнорирует 4xx при создании компании | open |
| BUG-007 | — | `/tenants` pagination | ✅ FIXED 2026-05-03 |
| BUG-011 | Critical | RBAC bypass через прямой URL | open |
| BUG-012 | — | Mock 1C → 500 на /api/v1/integration/1c/job-titles/batch | ✅ FIXED 2026-05-04 (по dev-команде, не верифицировано) |
| BUG-013 | Minor | ИНН=14 цифр → 500 | open |
| BUG-014 | Minor | Mixed UZ/RU — Adminlar / Foydalanuvchilar / wizard вкладки | open |
| BUG-015 | Major | Admin phone без `+` | ✅ FIXED 2026-05-04 |
| **BUG-016** | **Blocker** | **Super Admin admin123 → 401 после deploy 2026-05-04** | **open** |

Все живут в **Huly** — `Bugs.txt` это staging-копия.

## Page Object — правила

- Класс на каждую страницу. `__init__(page: Page)` инициализирует локаторы.
- Локаторы — приватные атрибуты, через `get_by_role` / `get_by_label`.
- Методы — действия и геттеры. **БЕЗ ассертов** (ассерты только в тестах).
- **MUI Switch** в строках таблицы — не button. Используем `get_by_label("...")` по aria-label на span-обёртке.
- **MUI Select** — не нативный `<select>`. Кликаем combobox + option из listbox.
- **Type hints обязательны**.

## i18n

UI работает в RU по дефолту (через `_force_ru_lang`). UZ — параметризованный smoke в `tests/smoke/test_locale.py` (через `LocaleSwitcher`).

`data/i18n.py` — словарь user-facing строк. Текущий покрытие — RU. Когда фронт перейдёт на UZ-default навсегда, можем переехать (но пока force RU надёжнее).

## Test data: подход

- Каждый тест в своих данных — суффикс `uuid4().hex[:6]`
- Префикс `[E2E]` → maintenance тест почистит (TODO когда снимут creates_data)
- Phone pool (`data/phone_pool.py`) — атомарная выдача с filelock для xdist
- `random_test_phone` — для creating-тестов
- ПИНФЛ генератор — 14 цифр, первая 1-6

## CI стратегия (когда появится remote)

Готово к `.gitlab-ci.yml`:
- **smoke** на каждый push (`-m smoke`, ~30 сек)
- **regression read-only** nightly (`-m "not creates_data and not eimzo_local_only" -n 4`, ~3 мин)
- **periodic_recon** weekly (`scripts/periodic_recon.py`, ~50 сек)
- **visual** at smoke (быстро, ~5 сек)
- **EIMZO** — только локально на машине с флешкой

## Структура

```
.
├── CLAUDE.md                 — стабильные правила для агента
├── Bugs.txt                  — staging для Huly bug-tracker'а
├── README.md
├── pyproject.toml
├── pytest.ini                — маркеры + общие addopts
├── .env / .env.local
├── conftest.py               — _force_ru_lang, _strict_console, фикстуры
├── config/settings.py
├── data/
│   ├── constants.py
│   ├── i18n.py
│   └── phone_pool.py
├── pages/
│   ├── base_page.py
│   ├── admin/                — AdminsPage, OrganizationsPage, CreateCompanyPage, …
│   ├── client/               — DocumentsPage, MembersPage, DepartmentsPage, …
│   └── components/
│       ├── locale_switcher.py — Admin/ClientLocaleSwitcher
│       └── (sidebar.py — в pages/client/)
├── tests/
│   ├── smoke/                — health + login + locale (13 тестов)
│   ├── admin/                — Admin UI (~130 тестов, частично creates_data)
│   ├── client/               — Client UI layout + RBAC (~80 тестов)
│   ├── regression/           — xfail-сторожа на открытые баги
│   ├── visual/               — pixel-baseline + PIL-helper
│   │   ├── baselines/        — committed PNG'ы
│   │   └── visual_helper.py
│   └── e2e/                  — главный сценарий (заморожен под BUG-012)
├── scripts/
│   └── periodic_recon.py     — eachly snapshot diff vs baseline
├── recon/baseline/           — 18 .yml aria-snapshot'ов
└── utils/
```

## data-testid wishlist (попросить фронт)

- `login-phone-input`, `login-password-input`, `login-submit`
- `otp-input`, `otp-submit`
- `company-create-button`, `company-name-input`, `company-inn-input`
- `document-action-approve`, `document-action-sign`, `document-action-reject`, `document-action-return`
- `menu-{section}` (inbox / my-documents / templates / routes / members / positions / departments)

## Открытые блокеры

1. **BUG-016** — без admin auth заморожены ~50% тестов (130+)
2. **CRUD freeze** — пока стенд общий, ~80 тестов creates_data деселектятся
3. **EIMZO local** — требует физический ключ
4. **Local docker-compose** — заблокирован BUG-016 + отсутствием client-side seed
