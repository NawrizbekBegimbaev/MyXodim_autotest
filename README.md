# BusinessHub E2E

E2E автотесты для BusinessHub (Admin UI / Client UI / Mock 1C).
Playwright + pytest, **UI-only** (никаких HTTP-вызовов из тестов — см. CLAUDE.md §13).

## Профили: dev vs local

| Файл | Среда | URLs |
|---|---|---|
| `.env` | активный (по умолчанию dev) | `dev-hub-*.greatmall.uz` |
| `.env.local` | локальный docker-compose из core repo | `localhost:3040/3041/3042` |

Переключение:

```bash
cp .env .env.dev.bak     # сохранить текущее
cp .env.local .env       # переключиться на local
# работа...
mv .env.dev.bak .env     # вернуть dev
```

Локальный setup blocker'ы (на 2026-05-03):
- BUG-015 — фронт шлёт phone без `+`, local-бэк strict отклоняет, dev lenient.
- Test-юзеры из README локально не сидятся: только Super Admin (+998991234567)
  через Liquibase. Client-side юзеры нужно создавать через Admin UI.

## Стек

- Python 3.13
- Playwright (sync API) + pytest-playwright
- pytest, pytest-xdist, pytest-rerunfailures, pydantic-settings
- allure-pytest (Allure-отчёты)
- ruff + mypy strict (CI gates)

## Setup

```bash
# 1. Виртуальное окружение
python3.13 -m venv .venv
source .venv/bin/activate

# 2. Зависимости (без editable-install)
pip install -e ".[dev]"

# 3. Браузер (Chromium для smoke/CI; системный Chrome нужен только для EIMZO)
playwright install chromium

# 4. Конфиг
cp .env.example .env
# Заполни SUPER_ADMIN_PHONE, SUPER_ADMIN_PASSWORD, CLIENT_SMOKE_PHONE
```

## Запуск

```bash
# По маркерам
pytest -m smoke                            # 5 тестов, ~5 сек — на каждый PR
pytest -m "positive or negative"           # функциональные тесты
pytest -m "not eimzo_local_only"           # всё что прокатится в CI
pytest -m e2e --headed                     # главный E2E (без EIMZO)
pytest -m "e2e and eimzo_local_only" \
       --headed -p no:xdist                # полный E2E с флешкой (только локально)

# По разделам
pytest tests/admin/                        # Admin UI (~128 тестов)
pytest tests/client/                       # Client UI (WIP)
pytest tests/smoke/                        # Smoke (5)

# Один тест
pytest tests/admin/test_company_create.py::test_company_create_with_valid_data_returns_integration_key -v
```

## Что покрыто

### Admin UI — 128 тестов (полное покрытие)

| Раздел | Тестов |
|---|---|
| UC-4.1 создание компании (positive + 10 negative + 45 boundary полей + 2 security) | 60 |
| UC-4.2 просмотр / поиск (rows, columns, search by name/inn/slug, empty, clear, special chars) | 10 |
| UC-4.3 disable/enable toggle | 2 |
| Detail page компании (имя, slug, ключ, статус, users, кнопки, breadcrumb) | 6 |
| Form buttons (Назад / Отмена / Вернуться к списку) | 3 |
| List interactions (click row → detail, records combo × 2, "Все" на дашборде) | 4 |
| Field input edge cases (paste 5000, drag&drop, emoji, RTL) | 4 |
| Login negative (wrong creds × 4 + empty) | 5 |
| Login boundary (phone variants × 7 + only-phone + only-password + 4 password variants) | 13 |
| Login security (XSS, SQLi) | 2 |
| Session / navigation (3 routes без auth + logout × 2 + refresh) | 6 |
| Widgets (language, dark mode, sidebar collapse, dashboard counters, pie chart) | 5 |
| **Итого Admin UI** | **128** |

### Smoke — 5 тестов
- 3 health (Admin/Client/Mock1C доступны)
- Admin login → /dashboard
- Client login + OTP → /tenant-select

### Client UI — WIP
Заблокировано BUG-005 + восстановлением стенда. Когда будет готово:
UC-3.6 (Сотрудники), 3.7 (Должности), маршруты, шаблоны, документы, главный E2E через Mock 1C.

## Известные баги (см. `Bugs.txt`)

| ID | Severity | Кратко |
|---|---|---|
| BUG-002 | Major | ПИНФЛ + ИНН без `*` на форме + generic error toast |
| BUG-006 | Major | Фронт Admin UI молча игнорирует 4xx при создании компании |
| BUG-007 | Major | Pagination `/tenants` сломан (10 в UI, 29 в БД) |

История по закрытым (BUG-001/003/004/008) — в git-history.

## CI стратегия

Из-за **деградации dev-стенда** при 130+ последовательных тестов
(сервер устаёт → таймауты на goto):

- **Smoke** — на каждый PR (`pytest -m smoke`, ~5 сек)
- **Regression chunked** — раз в день, бить на чанки по файлам с паузами:
  ```bash
  for f in tests/admin/test_*.py; do
      pytest "$f" --tb=line || true
      sleep 30  # дать стенду передохнуть
  done
  ```
- **Полный прогон** — раз в неделю на ночь
- **EIMZO-тесты** — только локально на машине с флешкой (`@pytest.mark.eimzo_local_only`)

## Troubleshooting

### Тесты флейкают / падают при множественном прогоне

1. **Очистить storage_state**: `rm -rf .auth/`
   (JWT в файле может протухнуть между сессиями pytest, TTL ~1 час)
2. **Подождать 1-2 минуты** — дать dev-стенду остыть
3. **Запустить отдельный test-файл** изолированно — это валидирует что тест корректный
4. **Проверить smoke**: `pytest -m smoke` — если падает, dev-стенд недоступен

### `Page.goto: Timeout 30000ms exceeded`

Сервер деградирует под нагрузкой. См. CI стратегию выше — бить на чанки.

### `expect_response timeout` в submit

Фронт-валидация заблокировала submit, POST не ушёл. Это валидное негативное
поведение — но если это positive-тест, проверить данные формы.

### Tests/admin/* падает с "Новая компания" не виден

Чаще всего это означает что storage_state протух. `rm -rf .auth/` и повторить.

## Структура

```
.
├── CLAUDE.md                  # инструкции для агента (стабильные правила)
├── Bugs.txt                   # активные баги с traceId, шагами, доказательствами
├── README.md
├── pyproject.toml             # зависимости + ruff/mypy конфиг
├── pytest.ini                 # маркеры + общие addopts
├── .env.example
├── conftest.py                # глобальные фикстуры (super_admin_state, anchor, и т.д.)
├── config/settings.py         # pydantic-settings из .env
├── data/                      # constants, i18n, phone_pool
├── pages/                     # Page Objects
│   ├── base_page.py
│   ├── admin/                 # AdminLoginPage, OrganizationsPage, CreateCompanyPage, …
│   └── client/                # ClientLoginPage, OtpPage, MembersPage, …
├── tests/
│   ├── smoke/
│   ├── admin/
│   ├── client/                # WIP
│   └── e2e/                   # WIP
├── scripts/                   # одноразовые recon-скрипты (не в CI)
├── recon/                     # снимки страниц для построения POM (gitignored)
└── utils/                     # inn_generator, auth_helpers
```

## Page Object — правила (короткая выжимка из CLAUDE.md §8)

- Класс на каждую страницу. `__init__(page: Page)` инициализирует локаторы.
- Локаторы — приватные атрибуты, через `get_by_role` / `get_by_label`.
- Методы — действия и геттеры. **БЕЗ ассертов** (ассерты только в тестах).
- **MUI Select** — не нативный `<select>`. Кликаем combobox + option из listbox.
- **MUI DataGrid `Действия`** — switch/buttons вне `<tr>`-DOM, ловим через `page.get_by_role("switch")` и индекс.
- **Type hints обязательны**.

## i18n

Вся UI-локаль = `ru-RU`. Тексты — через словарь `data/i18n.py`:

```python
from data.i18n import t
page.get_by_role("button", name=t("login.admin.submit"))
```

UZ-локаль ещё не покрыта (не было запроса).

## Test data: подход

- **Каждый тест в своих данных** — суффикс `uuid4().hex[:6]` в имени/slug/телефоне.
- **Префикс `[E2E]`** в названии компании / фамилии сотрудника → maintenance тест почистит за неделю.
- **Phone pool** (`data/phone_pool.py`) — атомарная выдача с filelock для xdist.
- **`random_test_phone`** — для creating-тестов где номер становится одноразовым.
- **ПИНФЛ генератор** — 14 цифр, первая 1-6 (требование UI-валидации).

## data-testid wishlist (попросить фронт)

Сейчас локаторы по `role + name` — устойчиво к классам, но привязаны к текстам.
Для CI и i18n будет лучше:

- `login-phone-input`, `login-password-input`, `login-submit`
- `otp-input`, `otp-submit`
- `company-create-button`, `company-name-input`, `company-inn-input`
- `document-action-approve`, `document-action-sign`, `document-action-reject`, `document-action-return`
- `menu-{section}` (inbox / my-documents / templates / routes / members / positions)

## Открытые вопросы (CLAUDE.md §14 — что осталось)

- Алгоритм UZ ИНН чек-суммы (сейчас фейк-9 цифр, бэк принимает)
- Поведение EIMZO PIN-диалога (запоминается ли в плагине)
- Mock 1C: подключение по ключу интеграции (полный flow)
