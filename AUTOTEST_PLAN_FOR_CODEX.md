# AUTOTEST PLAN FOR CODEX — BusinessHub E2E rewrite under new UI

> Дата: 2026-05-18
> Цель: переписать существующие POM и тесты под обновлённый UI dev-стенда после двух
> подряд redesign-волн (2026-05-03 sidebar redesign + 2026-05-13/2026-05-18 backend
> namespace migration + 2026-05-18 HR module deploy + DB wipe).
> Аудитория: Codex (другой ИИ-агент без доступа к памяти предыдущих сессий) и
> следующий human-инженер на проекте.
> Контекст: см. CLAUDE.md проекта (Playwright + Python + POM, UI-only, no API calls).
> Этот документ self-contained — Codex должен прочитать **только этот файл +
> /Users/n.begimbayevgreatmall.uz/Documents/Bussiness /CLAUDE.md** и сможет
> приступить к работе.

---

## 0. КРИТИЧЕСКИЙ КОНТЕКСТ

### 0.1 Стек и правила
- Python 3.11+, Playwright sync API, pytest, POM
- UI-only — никаких httpx/requests/API-вызовов в тестах (см. CLAUDE.md §6, §13)
- Page Object: класс на страницу, локаторы в `__init__`, методы без ассертов,
  type hints (см. CLAUDE.md §8)
- Локаторы — `get_by_role(role, name=...)` приоритет 1, далее
  `get_by_label/get_by_placeholder/get_by_test_id/get_by_text`, CSS — последний
  fallback. **Запрещено**: Svelte/MUI generated classes, XPath без обоснования.
- Ассерты только в тестах через `expect(locator).to_*` (auto-retrying). Никаких
  `time.sleep` / `wait_for_timeout` / `if locator.is_visible(): ...` (см. §9).
- Все user-facing строки через `data.i18n.t("...")` словарь (см. §12).
- Тестовые данные через `data/phone_pool.py` (filelock-atomic) +
  `data/constants.py` (см. §5). Префикс имён тестовых сущностей: `[E2E] `.

### 0.2 Бэкенд-фронтенд карта (2026-05-18)
Фронтенд `assets/sdk.gen-*.js` (auto-generated OpenAPI client) дёргает:

| Раздел | Endpoint |
|---|---|
| Auth | `POST /api/v1/auth/otp/request`, `POST /api/v1/auth/otp/verify` |
| Self | `GET /api/v1/users/me`, `GET /api/v1/users/tenant` |
| Members | `GET/POST /api/v1/users/members`, `PATCH /api/v1/users/members/{userId}` |
| Roles | `GET/POST /api/v1/users/roles`, `PATCH /api/v1/users/roles/{id}` |
| Positions | `GET/POST /api/v1/users/positions`, `PATCH/DELETE /{id}` |
| Job titles | `GET/POST /api/v1/users/job-titles`, `PATCH/DELETE /{id}` |
| Branches | `GET/POST /api/v1/branches`, `PATCH/DELETE /{id}` |
| Documents | `GET/POST /api/v1/edms/documents`, ряд `/{id}/approve|coordinate|sign|cancel|archive|submit|verify`, `/file`, `/signature-bundle`, `/inbox`, `/inbox/counts` |
| Templates | `GET/POST /api/v1/edms/templates`, `/categories`, `/{id}`, `/{templateId}/pdf-file*` |
| Workflows | `GET/POST /api/v1/edms/workflows`, `/{id}`, `/{id}/deploy` |
| HR (NEW) | `GET /api/v1/hr/payslips`, `/hr/vacation-balance`, `/hr/work-schedule` |
| Reports (NEW) | `GET /api/v1/reports/documents/summary` |

**Не существует на фронте**:
- `/api/v1/departments` — Departments UI рендерится без backend wiring (404 OK)
- `/api/v1/users/categories` или любые `/categories` — фича удалена (BUG-010)

**Admin UI** использует отдельный namespace `/api/v1/admin/*`
(`POST /api/v1/admin/auth/login`, `GET/POST /api/v1/admin/tenants`,
`GET /api/v1/admin/stats`, и т.д.).

### 0.3 Текущая ветка
- Branch: `main`
- Не commit'ить пока не получим явный запрос. Все правки в working tree.

---

## 1. ТЕКУЩЕЕ СОСТОЯНИЕ DEV (recon 2026-05-18)

### 1.1 Status-table по страницам Client UI

| URL | Heading | Уровень | Sidebar group | Backend | Notes |
|---|---|---|---|---|---|
| `/home` | "Добро пожаловать, {имя или phone}" | h1 | Рабочее место > top | OK | 5 виджетов (HR + docs/tasks) |
| `/payslip` | "Расчётные листы" | h6 | Рабочее место > Мой кабинет | OK (404 пустой) | placeholder "Выберите расчётный лист" |
| `/work-schedule` | НЕТ | — | Мой кабинет | OK (404 пустой) | только "Нет данных" |
| `/vacation` | НЕТ | — | Мой кабинет | OK (404 пустой) | только "Нет данных" |
| `/inbox` | "Требуют подписи" | h4 | Документы > top | OK | **полный redesign** — date filter, 5 columns, кнопка "История" |
| `/documents` | "Документы" | h4 | Документы > top | OK | **полный redesign** — view toggle Канбан/Таблица, 6 columns, удалены status tabs |
| `/templates` | "Шаблоны" | h4 | Справочники > Документооборот | OK | "Добавить шаблон", "Всего 0 шаблонов" |
| `/routes` | "Шаблоны маршрутов" | h4 | Документооборот | OK | 6 columns, "Version" англ. |
| `/members` | "Пользователи" | h4 | Оргструктура | OK | 6 columns, "Отключить себя" disabled (BUG-018 FIX) |
| `/branches` | "Филиалы" | h4 | Оргструктура | OK | **UNBLOCKED**, auto-seed "Главный офис" |
| `/departments` | "Отделы" | h4 | Оргструктура | OK | 6 columns, 2 фильтра |
| `/persons` | "Физические лица" | h4 | Оргструктура | OK | 9 columns, dialog "Добавить физлицо" |
| `/positions` | "Должности" | h4 | Оргструктура | OK | 2 columns, no seed data (BUG-019 FIX) |
| `/org-positions` | "Штатные позиции" | h4 | Оргструктура | OK | tabs Список/Иерархия, 6 columns |
| `/organization` | "Настройки организации" | h4 | Настройки | OK | tabs Данные/Филиалы, показывает Tenant ID (security smell) |
| `/integration` | "Интеграция" | h4 | Настройки | OK | 3 tabs + 3 cards, 1C modal "Подключено" с masked key |
| `/roles` | "Роли и права" | h4 | Настройки | OK | 4 system roles, Администратор 50/50 (BUG-011 FIX), 4 perm-groups: Документооборот/Кадры/Финансы/Настройки |
| `/forbidden` | "Доступ запрещён" | h4 | — | n/a | стандартный 403 |
| `/categories` | redirect | — | — | n/a | → `/forbidden?from=/categories`, BUG-010 FIXED |
| `/tenant-select` | "Организация не найдена" (h6) | — | — | n/a | пустой state для multi-tenant (или без tenants) |
| `/login` | "Добро пожаловать в BusinessHub" | h5 | — | OK | phone + OTP flow |

### 1.2 Admin UI

| URL | State | Notes |
|---|---|---|
| `/login` | h6 "BusinessHub Admin" | phone + password, broken (BUG-029) |
| `/dashboard` и др. | UNREACHABLE | blocked by BUG-029 |

### 1.3 Открытые блокеры

| BUG | Severity | Impact на autotest writing |
|---|---|---|
| BUG-027 (Admin UI) | Major | `dev-hub-admin.greatmall.uz/runtime/env.js` всё ещё `API_URL: ""`. Прод-юзеры в Yandex с cached env.js не смогут логиниться. Тесты, открывающие Admin UI через MCP, должны делать первый hit + reload + clear cache (или conftest должен переопределять env через init script). Client UI этой проблемы НЕТ — env.js там корректный с Cache-Control: no-store. |
| BUG-028 | Minor | RFC 7807 `type: http://localhost:8080/problems/help.html#...` в любом 4xx/5xx. Cosmetic. |
| BUG-029 | Major | Admin UI login сломан → нельзя писать тесты, требующие Super Admin UI flow (CompanyCreate / CompanyList / TenantsLayout / AdminLogin smoke). Все 17 типичных паролей выдают 401 `ADMIN_AUTH_INVALID_CREDENTIALS`. Endpoint живёт: `POST /api/v1/admin/auth/login` flat `{phone, password}`. |

### 1.4 Что НЕ нашёл (всё работает)

- BUG-010, BUG-011, BUG-018, BUG-019, BUG-026 — все FIXED, см. §8.
- `runtime/env.js` Client UI — FIXED (correct API_URL + no-store cache headers).

### 1.5 Новые наблюдения, которые могут быть багами (см. §10 RECOMMENDATIONS)

- В Add Role detail / `/roles/{uuid}` сводка показывает "50 / 50" но 4 категории
  суммируют 48 (12+19+5+12). Возможно `Дашборд` и `Отчёты` permissions хранятся
  в БД, но скрыты в UI.
- "Slug" (en) в `/organization > Данные`, "persons" (en) в `/roles`,
  "organization"/"integration" (en) в `/roles` детал — i18n gaps.
- "Tenant ID" UUID показан plain в `/organization > Данные` — спорно для security.
- `/integration` 1C card одновременно показывает кнопку "Настроить" и badge
  "Скоро" — UX-двойственность.
- `/documents` sidebar link называется "**Мои задания**" но heading "Документы"
  — naming-разрыв.
- `/members` breadcrumb "Оргструктура / **Сотрудники**" но heading "Пользователи"
  — naming-разрыв.
- `/routes` heading "Шаблоны маршрутов" но sidebar link "Маршруты" —
  naming-разрыв.
- POST `/api/v1/auth/otp/verify` принимает поле `otp` (не `code` как в старом
  контракте) — потенциальный breaking change documented как notable.

---

## 2. ФИКСТУРЫ (test users / tenants)

### 2.1 Что есть на стенде сейчас

**Tenant: `[E2E recon] 8dgk1l`** (recon-провижн 2026-05-18)
- tenant_id: `a51f7085-95a4-4b71-930f-30ef974c418e`
- slug: `e2e-recon-8dgk1l`
- inn: `534923943`
- adminUserId: `37827eb8-d61b-4c37-81ff-82c300eb8df1`
- integrationKey: `bh_live_9479ba5d751e4c8ab3d3d80c7e015b23`
- admin: `+998905555518` "Recon Admin" PINFL `11359431448530`
- Auto-seeded: 1 филиал "Главный офис". 0 positions, 0 departments, 0 employees
  (кроме admin'а).

**Director/Manager/Сотрудник**: НЕ созданы. После того как восстановим
`tests/conftest.py` фикстуры для tenant creation (через UI Admin Super) либо
напрямую (см. §3) — нужно создать 3 invitee'ев в этом tenant'е для RBAC тестов.

**Super Admin (Client UI OTP)**: `+998991234567` + OTP `123456` работает.
Realm role `PLATFORM_ADMIN`. После OTP → `/tenant-select` → пустой экран
"Организация не найдена".

**Super Admin (Admin UI password)**: СЛОМАН (BUG-029). Использовать `skip`
marker `needs_admin_creds`.

**TEST_OTP**: `123456` (dev принимает любые 6-значные).

### 2.2 Config (data/constants.py — текущий, не менять без causes)

```python
TEST_OTP: str = "123456"
E2E_ORG_PREFIX: str = "[E2E]"
E2E_PREFIX: str = "[E2E]"
AUTH_DIR: str = ".auth"
SUPER_ADMIN_STATE_FILE: str = f"{AUTH_DIR}/super_admin.json"
CLIENT_ADMIN_STATE_FILE: str = f"{AUTH_DIR}/client_admin.json"
```

### 2.3 Settings (config/settings.py — нужно обновить значения по умолчанию)

| Поле | Сейчас | Должно стать | Reason |
|---|---|---|---|
| `super_admin_phone` | `+998900000000` | `+998991234567` | actual fixture |
| `super_admin_password` | `changeme` | `<unknown>` (см. BUG-029) | broken, добавить marker |
| `client_smoke_phone` | `+998900000000` | `+998905555518` | actual fixture (recon tenant) |
| `client_smoke_org` | `SecondQaTeam` | `[E2E recon] 8dgk1l` | actual tenant name |

Codex: используй `.env.example` для документирования, фактические значения
можно положить в `.env` (gitignored). Default-ы в `Settings` должны указывать
на текущие живые фикстуры.

### 2.4 Tenant create REST shape (для maintenance/scripts/, **не для тестов**)

`POST /api/v1/admin/tenants` с Bearer `<PLATFORM_ADMIN JWT>`:
```json
{
  "tenantName": "...",
  "tenantSlug": "...",
  "tenantInn": "9-digit",
  "adminPhone": "+998XXXXXXXXX",
  "adminFirstName": "...",
  "adminLastName": "...",
  "adminPinfl": "14-digit"
}
```
Возвращает 200 + `{tenantId, adminUserId, integrationKey, message}`. Это REST,
не UI — использовать только в maintenance-скриптах для re-провижна после wipe.

---

## 3. POM CHANGES (детально, по каждому файлу)

### 3.1 CREATE `pages/client/home_page.py`

```python
from playwright.sync_api import Locator, Page
from pages.base_page import BasePage


class HomePage(BasePage):
    """Главная (с 2026-05-03) — Workspace landing с 5 виджетами и приветствием."""

    URL_PATH = "/home"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # h1 содержит имя или phone — динамическое, локатор по level only
        self._greeting: Locator = page.get_by_role("heading", level=1)
        # Подзаголовок: "понедельник, 18 мая·Администратор" — день недели + дата + role
        # 5 виджет-кнопок (вся карточка clickable):
        self._widget_payslip: Locator = page.get_by_role(
            "button", name=lambda n: n and n.startswith("Текущие начисления")
        ).first
        self._widget_vacation: Locator = page.get_by_role(
            "heading", name="Вам доступно дней отпуска", level=6
        )
        self._widget_schedule: Locator = page.get_by_role(
            "heading", name="Ваш график работы", level=6
        )
        self._widget_my_docs: Locator = page.get_by_role(
            "heading", name="Мои документы", level=6
        )
        self._widget_my_tasks: Locator = page.get_by_role(
            "heading", name="Мои задачи", level=6
        )

    @property
    def greeting(self) -> Locator:
        return self._greeting

    @property
    def widget_payslip(self) -> Locator:
        return self._widget_payslip

    @property
    def widget_vacation(self) -> Locator:
        return self._widget_vacation

    @property
    def widget_schedule(self) -> Locator:
        return self._widget_schedule

    @property
    def widget_my_docs(self) -> Locator:
        return self._widget_my_docs

    @property
    def widget_my_tasks(self) -> Locator:
        return self._widget_my_tasks
```

**i18n keys to add** в `data/i18n.py`:
```python
"client.home.widget_payslip": "Текущие начисления",
"client.home.widget_vacation": "Вам доступно дней отпуска",
"client.home.widget_schedule": "Ваш график работы",
"client.home.widget_my_docs": "Мои документы",
"client.home.widget_my_tasks": "Мои задачи",
"client.home.empty_data": "Нет данных",
```

### 3.2 CREATE `pages/client/persons_page.py`

```python
from typing import Self
from playwright.sync_api import Locator, Page
from data.i18n import t
from pages.base_page import BasePage


class PersonsPage(BasePage):
    URL_PATH = "/persons"

    COLUMNS: tuple[str, ...] = (
        "ФИО", "ПИНФЛ", "Дата рождения", "Email",
        "Телефон", "Источник", "Статус", "Действия",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.persons.title"), level=4
        )
        self._add_button: Locator = page.get_by_role(
            "button", name=t("client.persons.add_button"), exact=True
        )
        self._search: Locator = page.get_by_placeholder(
            t("client.persons.search_placeholder")
        )
        self._filter_combobox: Locator = page.get_by_role("combobox").first
        self._table: Locator = page.get_by_role("main").get_by_role("table")

    @property
    def heading(self) -> Locator: return self._heading
    @property
    def add_button(self) -> Locator: return self._add_button
    @property
    def search(self) -> Locator: return self._search
    @property
    def table(self) -> Locator: return self._table

    def click_add(self) -> Self:
        self._add_button.click()
        return self

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)
```

**i18n keys**:
```python
"client.persons.title": "Физические лица",
"client.persons.add_button": "Добавить",
"client.persons.search_placeholder": "Поиск...",
"client.persons.dialog_title": "Добавить физлицо",
"client.persons.field_full_name": "ФИО",
"client.persons.field_pinfl": "ПИНФЛ",
"client.persons.field_birth_date": "Дата рождения",
"client.persons.field_email": "Email",
"client.persons.field_phone": "Телефон",
"client.persons.dialog_submit": "Сохранить",
"client.persons.dialog_cancel": "Отмена",
```

### 3.3 CREATE `pages/client/person_create_dialog.py`

```python
from typing import Self
from playwright.sync_api import Locator, Page
from data.i18n import t
from pages.base_page import BasePage


class PersonCreateDialog(BasePage):
    """Открывается с /persons → "Добавить". Поля: fullName/pinfl/birthDate/email/phone."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.persons.dialog_title")
        )
        self._full_name: Locator = self._dialog.get_by_label(
            t("client.persons.field_full_name"), exact=True
        )
        self._pinfl: Locator = self._dialog.get_by_label(
            t("client.persons.field_pinfl"), exact=True
        )
        self._birth_date: Locator = self._dialog.get_by_label(
            t("client.persons.field_birth_date"), exact=True
        )
        self._email: Locator = self._dialog.get_by_label(
            t("client.persons.field_email"), exact=True
        )
        self._phone: Locator = self._dialog.get_by_label(
            t("client.persons.field_phone"), exact=True
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.persons.dialog_submit")
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.persons.dialog_cancel")
        )

    @property
    def dialog(self) -> Locator: return self._dialog

    def fill(self, full_name: str, pinfl: str, birth_date: str = "",
             email: str = "", phone: str = "") -> Self:
        self._full_name.fill(full_name)
        self._pinfl.fill(pinfl)
        if birth_date:
            self._birth_date.fill(birth_date)
        if email:
            self._email.fill(email)
        if phone:
            self._phone.fill(phone)
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
```

### 3.4 CREATE `pages/client/payslip_page.py`

```python
from playwright.sync_api import Locator, Page
from pages.base_page import BasePage


class PayslipPage(BasePage):
    """Расчётные листы (Мой кабинет). Пока placeholder UI."""

    URL_PATH = "/payslip"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # NB: heading level=6 (а НЕ h4 как остальные главные)
        self._heading: Locator = page.get_by_role(
            "heading", name="Расчётные листы", level=6
        )
        self._empty: Locator = page.get_by_text(
            "Расчётные листы не найдены", exact=True
        )
        self._placeholder: Locator = page.get_by_text(
            "Выберите расчётный лист", exact=True
        )

    @property
    def heading(self) -> Locator: return self._heading
    @property
    def empty(self) -> Locator: return self._empty
    @property
    def placeholder(self) -> Locator: return self._placeholder
```

### 3.5 CREATE `pages/client/work_schedule_page.py` (stub)

```python
from playwright.sync_api import Locator, Page
from pages.base_page import BasePage


class WorkSchedulePage(BasePage):
    """График работы (Мой кабинет). Пока 'Нет данных' state."""

    URL_PATH = "/work-schedule"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._empty: Locator = page.get_by_text("Нет данных", exact=True)

    @property
    def empty(self) -> Locator: return self._empty
```

### 3.6 CREATE `pages/client/vacation_page.py` (stub)

```python
from playwright.sync_api import Locator, Page
from pages.base_page import BasePage


class VacationPage(BasePage):
    """Отпуск (Мой кабинет). Пока 'Нет данных' state."""

    URL_PATH = "/vacation"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._empty: Locator = page.get_by_text("Нет данных", exact=True)

    @property
    def empty(self) -> Locator: return self._empty
```

### 3.7 CREATE `pages/client/forbidden_page.py`

```python
from playwright.sync_api import Locator, Page
from pages.base_page import BasePage


class ForbiddenPage(BasePage):
    """403-страница. Используется для assertion'ов в RBAC и BUG-010 (категории)."""

    URL_PATH = "/forbidden"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name="Доступ запрещён", level=4
        )
        self._home_button: Locator = page.get_by_role(
            "button", name="На главную"
        )

    @property
    def heading(self) -> Locator: return self._heading
    @property
    def home_button(self) -> Locator: return self._home_button

    def message_for_section(self, section: str) -> Locator:
        # Например: "У вас нет доступа к разделу «Категории»."
        return self.page.get_by_text(
            f"У вас нет доступа к разделу «{section}».", exact=True
        )
```

### 3.8 MAJOR REWRITE `pages/client/sidebar.py`

**Полностью переписать.** Новая структура (5 sections, 4 collapsible
subgroups, 17 links). Sections — top-level `<div role="button">`
(ALWAYS expanded в DOM, видно текст group label), subgroups —
`<button role="button">` (collapsible).

```python
from __future__ import annotations
from typing import Self
from playwright.sync_api import Locator, Page

# Структура sidebar (с 2026-05-18):
#   Section "Рабочее место":
#       - Главная                  /home           (top link)
#       - Subgroup "Мой кабинет":
#           - Расчётный лист       /payslip
#           - График работы        /work-schedule
#           - Отпуск               /vacation
#   Section "Документы":
#       - Входящие документы       /inbox          (top link)
#       - Мои задания              /documents      (top link)
#   Section "Справочники":
#       - Subgroup "Документооборот":
#           - Шаблоны              /templates
#           - Маршруты             /routes
#   Section "Оргструктура":
#       - Subgroup "Оргструктура":
#           - Пользователи         /members
#           - Филиалы              /branches
#           - Отделы               /departments
#           - Физические лица      /persons
#           - Должности            /positions
#           - Штатные позиции      /org-positions
#   Section "Настройки":
#       - Subgroup "Настройки":
#           - Организация          /organization
#           - Системные роли       /roles
#           - Интеграция           /integration

# (section, subgroup_or_None, label, path)
ADMIN_NAV: tuple[tuple[str, str | None, str, str], ...] = (
    ("Рабочее место", None,             "Главная",             "/home"),
    ("Рабочее место", "Мой кабинет",    "Расчётный лист",      "/payslip"),
    ("Рабочее место", "Мой кабинет",    "График работы",       "/work-schedule"),
    ("Рабочее место", "Мой кабинет",    "Отпуск",              "/vacation"),
    ("Документы",     None,             "Входящие документы",  "/inbox"),
    ("Документы",     None,             "Мои задания",         "/documents"),
    ("Справочники",   "Документооборот", "Шаблоны",            "/templates"),
    ("Справочники",   "Документооборот", "Маршруты",           "/routes"),
    ("Оргструктура",  "Оргструктура",   "Пользователи",        "/members"),
    ("Оргструктура",  "Оргструктура",   "Филиалы",             "/branches"),
    ("Оргструктура",  "Оргструктура",   "Отделы",              "/departments"),
    ("Оргструктура",  "Оргструктура",   "Физические лица",     "/persons"),
    ("Оргструктура",  "Оргструктура",   "Должности",           "/positions"),
    ("Оргструктура",  "Оргструктура",   "Штатные позиции",     "/org-positions"),
    ("Настройки",     "Настройки",      "Организация",         "/organization"),
    ("Настройки",     "Настройки",      "Системные роли",      "/roles"),
    ("Настройки",     "Настройки",      "Интеграция",          "/integration"),
)

SECTION_NAMES: tuple[str, ...] = (
    "Рабочее место", "Документы", "Справочники", "Оргструктура", "Настройки",
)
SUBGROUP_NAMES: tuple[str, ...] = (
    "Мой кабинет", "Документооборот", "Оргструктура", "Настройки",
)


class ClientSidebar:
    def __init__(self, page: Page) -> None:
        self.page = page
        self._nav: Locator = page.get_by_role("navigation").first
        # Bottom area (под separator):
        self._lang_button: Locator = page.get_by_role(
            "button", name="Switch language to O'zbekcha"
        )
        self._theme_button: Locator = page.get_by_role(
            "button", name="Toggle theme"
        )
        # Bottom user menu trigger — содержит phone + role
        self._user_menu_trigger: Locator = page.get_by_role(
            "button", name="User menu"
        )

    @property
    def nav(self) -> Locator:
        return self._nav

    def link(self, label: str) -> Locator:
        """Получить link по label. Если он в subgroup — сперва expand_subgroup."""
        return self._nav.get_by_role("link", name=label, exact=True)

    def section_header(self, name: str) -> Locator:
        """Top-level section (div role=button с aria-label). Не collapsible."""
        return self._nav.locator(f'[role="button"][aria-label="{name}"]').first

    def subgroup_button(self, name: str) -> Locator:
        """Collapsible подгруппа (button role=button с aria-label)."""
        return self._nav.locator(f'button[aria-label="{name}"]').first

    def expand_subgroup(self, name: str) -> Self:
        """Кликнуть subgroup-кнопку (Мой кабинет / Документооборот / Оргструктура / Настройки).
        Click безопасен — повторный сворачивает (toggle), но для тестов мы каждый раз
        идём с known state. Чтобы быть безопасным — проверять aria-expanded.
        """
        btn = self.subgroup_button(name)
        expanded = btn.get_attribute("aria-expanded")
        if expanded != "true":
            btn.scroll_into_view_if_needed()
            btn.click()
        return self

    def expand_all_subgroups(self) -> Self:
        for sg in SUBGROUP_NAMES:
            self.expand_subgroup(sg)
        return self

    # User menu
    @property
    def user_menu_trigger(self) -> Locator:
        return self._user_menu_trigger

    def open_user_menu(self) -> Self:
        self._user_menu_trigger.click()
        return self

    def menu_item(self, name: str) -> Locator:
        return self.page.get_by_role("menuitem", name=name, exact=True)

    def click_settings(self) -> Self:
        self.menu_item("Настройки").click()
        return self

    def click_logout(self) -> Self:
        self.menu_item("Выйти").click()
        return self

    # Language switcher
    @property
    def lang_button(self) -> Locator:
        return self._lang_button

    @property
    def theme_button(self) -> Locator:
        return self._theme_button
```

**Уровни expand для тестов**:
- Top-level links (Главная, Входящие документы, Мои задания) — всегда видны
- Subgroup links — требуют `expand_subgroup(subgroup_name)` сначала
- "Настройки" subgroup может быть за viewport — `scroll_into_view_if_needed()`
  обязателен (см. POM выше)

### 3.9 UPDATE `pages/client/member_create_dialog.py`

Изменения от текущего файла:
1. Добавить `_department` combobox
2. Required-маркер для 4 полей (Имя, Фамилия, Телефон, Системная роль)
   — текущие i18n labels должны включать `*` или искать через
   `name=lambda n: "Имя" in n` потому что реально в DOM label `"Имя *"`
3. Submit button text: "Добавить" (уже OK через i18n)
4. Combobox `field_role` — option names: "Сотрудник", "Менеджер", "Директор",
   "Администратор" (BUG-026 FIXED — все 4 доступны)

```python
from typing import Self
from playwright.sync_api import Locator, Page
from data.i18n import t
from pages.base_page import BasePage


class MemberCreateDialog(BasePage):
    """Модалка /members → "Добавить сотрудника".

    Поля:
      Required (отмечены `*` в UI):
        - Имя (input name=firstName)
        - Фамилия (input name=lastName)
        - Телефон (input name=phone)
        - Системная роль (combobox)
      Optional:
        - Отчество (input name=middleName)
        - ПИНФЛ (input name=pinfl)
        - Должность (combobox)
        - Отдел (combobox)
      Кнопки: "Отмена", "Добавить".
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._dialog: Locator = page.get_by_role(
            "dialog", name=t("client.members.dialog_title")
        )
        # Label содержит "Имя *" → используем get_by_label с exact=False
        self._first_name: Locator = self._dialog.get_by_label(
            t("client.members.field_first_name"), exact=False
        )
        self._last_name: Locator = self._dialog.get_by_label(
            t("client.members.field_last_name"), exact=False
        )
        self._middle_name: Locator = self._dialog.get_by_label(
            t("client.members.field_middle_name"), exact=True
        )
        self._phone: Locator = self._dialog.get_by_label(
            t("client.members.field_phone"), exact=False
        )
        self._pinfl: Locator = self._dialog.get_by_label(
            t("client.members.field_pinfl"), exact=True
        )
        self._role: Locator = self._dialog.get_by_role(
            "combobox", name=lambda n: bool(n) and "Системная роль" in n
        )
        self._position: Locator = self._dialog.get_by_role(
            "combobox", name=t("client.members.field_position"), exact=True
        )
        self._department: Locator = self._dialog.get_by_role(
            "combobox", name=t("client.members.field_department"), exact=True
        )
        self._submit: Locator = self._dialog.get_by_role(
            "button", name=t("client.members.dialog_submit"), exact=True
        )
        self._cancel: Locator = self._dialog.get_by_role(
            "button", name=t("client.members.dialog_cancel"), exact=True
        )

    @property
    def dialog(self) -> Locator:
        return self._dialog

    def fill_required(self, first_name: str, last_name: str,
                       phone: str, role: str) -> Self:
        self._first_name.fill(first_name)
        self._last_name.fill(last_name)
        self._phone.fill(phone)
        self.select_role(role)
        return self

    def fill_middle_name(self, value: str) -> Self:
        self._middle_name.fill(value)
        return self

    def fill_pinfl(self, value: str) -> Self:
        self._pinfl.fill(value)
        return self

    def select_role(self, label: str) -> Self:
        self._role.click()
        self.page.get_by_role("listbox").get_by_role(
            "option", name=label, exact=True
        ).click()
        return self

    def select_position(self, label: str) -> Self:
        self._position.click()
        self.page.get_by_role("listbox").get_by_role(
            "option", name=label, exact=True
        ).click()
        return self

    def select_department(self, label: str) -> Self:
        self._department.click()
        self.page.get_by_role("listbox").get_by_role(
            "option", name=label, exact=True
        ).click()
        return self

    def submit(self) -> Self:
        self._submit.click()
        return self

    def cancel(self) -> Self:
        self._cancel.click()
        return self
```

**i18n update в `data/i18n.py`**:
```python
# Добавить:
"client.members.field_role": "Системная роль",  # было "Роль"
"client.members.field_department": "Отдел",     # НОВОЕ
# Изменить:
"client.members.col_role": "Системная роль",    # было "Роль"
```

### 3.10 UPDATE `pages/client/members_page.py`

Изменения:
1. Колонки больше БЕЗ checkbox (теперь 6: Имя, Телефон, Системная роль,
   Должность, Статус, Действия — было: + checkbox)
2. `status_cell_for_phone` — индекс `.nth(4)` остаётся корректным
   (Имя=0, Телефон=1, Системная роль=2, Должность=3, Статус=4, Действия=5)
3. Row action "Отключить" может быть `disabled` для собственной строки
   (BUG-018 FIXED) — добавить метод `is_disable_button_disabled_for_phone()`
   для проверки

```python
# Добавить методы в MembersPage:

def is_disable_button_disabled_for_phone(self, phone: str) -> Locator:
    """Returns Locator для disabled-кнопки "Отключить" в строке с указанным телефоном.
    Используется для regression-теста BUG-018."""
    return self.row_by_phone(phone).get_by_role(
        "button", name=t("client.members.row_action_disable")
    )

def disable_self_tooltip(self) -> Locator:
    """Tooltip 'Нельзя отключить себя' рядом с disabled-кнопкой."""
    return self.page.get_by_text("Нельзя отключить себя", exact=True)
```

### 3.11 UPDATE `pages/client/documents_page.py`

**MAJOR REWRITE**. Список изменений:
1. Status tabs **УДАЛЕНЫ** из UI — убрать `STATUS_TABS` константу из POM
2. Появился view-toggle: "kanban view" / "table view" (`aria-pressed`)
3. URL добавлен `&view=table|kanban`
4. Появилась кнопка "Фильтр по дате"
5. Колонки полностью переименованы

```python
COLUMNS: tuple[str, ...] = (
    "Заголовок", "Статус", "Дата", "Номер", "Вид документа", "Организация",
)

VIEW_MODES: tuple[str, ...] = ("kanban view", "table view")
KANBAN_LANES: tuple[str, ...] = ("В ожидании", "В работе", "Завершён", "Отказан")

# В __init__ добавить:
self._kanban_button: Locator = page.get_by_role("button", name="kanban view")
self._table_button: Locator = page.get_by_role("button", name="table view")
self._date_filter_button: Locator = page.get_by_role("button", name="Фильтр по дате")
self._search: Locator = page.get_by_placeholder("По заголовку или номеру...")

# Методы:
def switch_to_kanban(self) -> Self:
    self._kanban_button.click()
    return self

def switch_to_table(self) -> Self:
    self._table_button.click()
    return self

def kanban_column(self, status: str) -> Locator:
    """Канбан-колонка по имени status (В ожидании/В работе/Завершён/Отказан)."""
    return self.page.get_by_role("heading", name=status, level=6).locator("..")
```

**УДАЛИТЬ** методы относящиеся к status_tabs — `tab()` и константу `STATUS_TABS`
если они нигде больше не нужны (или сохранить с deprecated комментом и `xfail`).

### 3.12 UPDATE `pages/client/inbox_page.py`

**MAJOR REWRITE**:
1. Heading "Требуют подписи" h4 + paragraph "Задания, требующие согласования,
   подписи или отказа"
2. Toolbar: button "Обновить" (icon-only, aria=Обновить), button "История"
3. Filter bar: 2 date pickers (placeholder "дд.мм.гггг") + "—" separator +
   search input "Поиск по заголовку или номеру..." + filter chip
   "В работе {count}"
4. Columns (5): №, Наименование (sortable), Инициатор, Дата начала (sortable),
   Подпись + (action cell)
5. Empty state: "Задания отсутствуют" + "На ваш аккаунт сейчас не назначено
   активных заданий на согласование."

```python
from __future__ import annotations
from typing import Self
from playwright.sync_api import Locator, Page
from data.i18n import t
from pages.base_page import BasePage


class InboxPage(BasePage):
    URL_PATH = "/inbox"

    COLUMNS: tuple[str, ...] = (
        "№", "Наименование", "Инициатор", "Дата начала", "Подпись",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name=t("client.inbox.title"), level=4
        )
        self._subtitle: Locator = page.get_by_text(
            "Задания, требующие согласования, подписи или отказа", exact=True
        )
        self._refresh_button: Locator = page.get_by_role(
            "button", name=t("client.inbox.refresh"), exact=True
        )
        self._history_button: Locator = page.get_by_role(
            "button", name=t("client.inbox.history"), exact=True
        )
        self._search: Locator = page.get_by_placeholder(
            t("client.inbox.search_placeholder")
        )
        self._date_from: Locator = page.get_by_placeholder("дд.мм.гггг").first
        self._date_to: Locator = page.get_by_placeholder("дд.мм.гггг").nth(1)
        self._table: Locator = page.get_by_role("main").get_by_role("table")

    @property
    def heading(self) -> Locator: return self._heading

    @property
    def history_button(self) -> Locator: return self._history_button

    @property
    def refresh_button(self) -> Locator: return self._refresh_button

    @property
    def search(self) -> Locator: return self._search

    @property
    def table(self) -> Locator: return self._table

    def column_header(self, name: str) -> Locator:
        return self._table.get_by_role("columnheader", name=name, exact=True)

    def filter_chip(self, label: str) -> Locator:
        """Например 'В работе' — sib содержит count."""
        return self.page.get_by_text(label, exact=True)

    def empty_message(self) -> Locator:
        return self.page.get_by_text("Задания отсутствуют", exact=True)
```

**i18n updates**:
```python
"client.inbox.title": "Требуют подписи",
"client.inbox.subtitle": "Задания, требующие согласования, подписи или отказа",
"client.inbox.refresh": "Обновить",
"client.inbox.history": "История",
"client.inbox.search_placeholder": "Поиск по заголовку или номеру...",
"client.inbox.col_number": "№",
"client.inbox.col_title": "Наименование",
"client.inbox.col_initiator": "Инициатор",
"client.inbox.col_start_date": "Дата начала",
"client.inbox.col_signature": "Подпись",
"client.inbox.empty_title": "Задания отсутствуют",
```

### 3.13 UPDATE `pages/client/organization_page.py`

Изменения:
1. Heading "Организация" → **"Настройки организации"** (h4)
2. Tabs "Данные"/"Филиалы" остаются
3. NEW: Tenant ID в data-tab — UUID показывается в DOM, можно использовать
   для extraction в тестах если нужен tenantId

```python
# В __init__:
self._heading: Locator = page.get_by_role(
    "heading", name=t("client.organization.title"), level=4
)
# i18n:
"client.organization.title": "Настройки организации",  # БЫЛО "Организация"

# Tenant ID extraction (для тестов):
def tenant_id_text(self) -> Locator:
    """Tenant ID отображается рядом с label 'Tenant ID' в табе Данные."""
    return self.page.get_by_text("Tenant ID", exact=True).locator("..")
```

### 3.14 UPDATE `pages/client/organization_page.py::IntegrationPage`

Изменения:
1. ADD status tabs "Все" / "Подключено" / "Не подключено"
2. Modal 1C: title h2 содержит "1C" + status (например "1CПодключено"),
   accessible name выходит сцепка → использовать filter+has

```python
# В IntegrationPage:
STATUS_TABS: tuple[str, ...] = ("Все", "Подключено", "Не подключено")
PROVIDERS: tuple[str, ...] = ("1C", "Bitrix24", "Налоговая система")

self._tab_all = page.get_by_role("tab", name="Все", exact=True)
self._tab_connected = page.get_by_role("tab", name="Подключено", exact=True)
self._tab_disconnected = page.get_by_role("tab", name="Не подключено", exact=True)
self._configure_1c = page.get_by_role("button", name="Настроить", exact=True)

# Modal locator (имя содержит '1C' + статус):
def modal_1c(self) -> Locator:
    return self.page.get_by_role("dialog").filter(
        has=self.page.get_by_role("heading", name="1C", level=6)
    )

def modal_show_button(self) -> Locator:
    return self.modal_1c().get_by_role("button", name="Показать", exact=True)

def modal_copy_button(self) -> Locator:
    return self.modal_1c().get_by_role("button", name="Скопировать", exact=True)

def modal_key_masked(self) -> Locator:
    """Текст •••• (32 точки) перед "Показать"-click."""
    return self.modal_1c().get_by_text("•" * 32, exact=False)
```

### 3.15 UPDATE `pages/client/positions_page.py`

```python
# COLUMNS уменьшилось до 2:
COLUMNS: tuple[str, ...] = ("Название должности", "Действия")
# heading "Должности" h4 + paragraph "Всего N должностей"
# add_button "Добавить должность"
# search "Поиск по названию..."
# Без изменений если уже там — выровнять с реальным DOM
```

### 3.16 UPDATE `pages/client/routes_page.py`

```python
COLUMNS: tuple[str, ...] = (
    "Название", "Шаги", "Статус", "Version", "Последнее изменение", "Действия",
)
# heading "Шаблоны маршрутов" h4 (не "Маршруты"!)
# add_button "Создать маршрут"
# i18n update:
"client.routes.title": "Шаблоны маршрутов",
"client.routes.add_button": "Создать маршрут",
```

### 3.17 UPDATE `pages/client/branches_page.py`

UNBLOCKED — теперь можно делать POM:

```python
COLUMNS: tuple[str, ...] = ("Филиал", "Тип", "Отделы", "Пользователи", "Действия")
VIEW_TABS: tuple[str, ...] = ("Таблица", "Иерархия")

# В __init__:
self._heading = page.get_by_role("heading", name="Филиалы", level=4)
self._subtitle = page.get_by_text(
    "Структура головного офиса и филиалов организации.", exact=True
)
self._add_button = page.get_by_role("button", name="Добавить филиал")
self._search = page.get_by_placeholder("Поиск по названию…")  # NB unicode ellipsis
self._tab_table = page.get_by_role("tab", name="Таблица", exact=True)
self._tab_hierarchy = page.get_by_role("tab", name="Иерархия", exact=True)
self._table = page.get_by_role("main").get_by_role("table")

# i18n:
"client.branches.title": "Филиалы",
"client.branches.add_button": "Добавить филиал",
"client.branches.search_placeholder": "Поиск по названию…",
```

### 3.18 UPDATE `pages/client/departments_page.py`

```python
COLUMNS: tuple[str, ...] = (
    "Название отдела", "Филиал", "Родитель", "Пользователи", "Источник", "Действия",
)
# heading "Отделы" h4 + "Всего N отделов"
# add_button "Добавить отдел"
# search "Поиск по названию..."
# 2 фильтра: combobox name="Филиал", combobox name="Источник"

# Методы:
def filter_by_branch(self, label: str) -> Self:
    self._filter_branch.click()
    self.page.get_by_role("option", name=label).click()
    return self

def filter_by_source(self, label: str) -> Self:
    self._filter_source.click()
    self.page.get_by_role("option", name=label).click()
    return self
```

### 3.19 UPDATE `pages/client/roles_page.py`

```python
# heading "Роли и права" h4 (НЕ "Системные роли")
# button "Создать роль"
# columns (3): "Название роли" | "Права доступа" | "Действия"
# row content example: "Сотрудник | Документооборот (2/12) Кадры (3/19) 5/50 | Системная"

# i18n:
"client.roles.title": "Роли и права",
"client.roles.add_button": "Создать роль",

# Permission categories (NEW):
PERM_GROUPS: tuple[str, ...] = (
    "Документооборот", "Кадры", "Финансы", "Настройки",
)

# Add role detail page POM (NEW):
```

### 3.20 CREATE `pages/client/role_detail_page.py`

```python
from playwright.sync_api import Locator, Page
from pages.base_page import BasePage


class RoleDetailPage(BasePage):
    """URL: /roles/{uuid} — редактирование роли + матрица прав."""

    # URL_PATH не статичный — uuid в пути

    GROUPS: tuple[str, ...] = ("Документооборот", "Кадры", "Финансы", "Настройки")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._heading: Locator = page.get_by_role(
            "heading", name="Редактировать роль", level=4
        )
        self._back_button: Locator = page.get_by_role("button", name="Назад")
        self._save_button: Locator = page.get_by_role("button", name="Сохранить")
        self._expand_all: Locator = page.get_by_role(
            "button", name="Развернуть все"
        )
        self._collapse_all: Locator = page.get_by_role(
            "button", name="Свернуть все"
        )

    @property
    def heading(self) -> Locator: return self._heading

    def group_summary(self, name: str) -> Locator:
        """Например 'Документооборот12/12' — header группы прав."""
        return self.page.get_by_role(
            "button", name=lambda n: bool(n) and n.startswith(name)
        ).first

    def total_summary(self) -> Locator:
        """Например '50 / 50 Права доступа' — общий счётчик."""
        return self.page.get_by_text("Права доступа", exact=False)
```

### 3.21 UPDATE `pages/client/templates_page.py`

Recon не сделал deep dive (страница пустая), но minimal:
```python
# heading "Шаблоны" h4 + paragraph "Всего N шаблонов"
# add_button "Добавить шаблон"
# search placeholder: "По названию шаблона..."
# i18n:
"client.templates.title": "Шаблоны",
"client.templates.add_button": "Добавить шаблон",
"client.templates.search_placeholder": "По названию шаблона...",
```

### 3.22 UPDATE `pages/client/select_organization_page.py`

NEW empty-state. Если у юзера 0 tenants после login — попадает сюда:
```python
# Heading "Организация не найдена" h6
# Subtitle "Ваш аккаунт не привязан ни к одной организации. Обратитесь к
#   администратору."
# Button "Выйти"

# Добавить методы:
@property
def empty_heading(self) -> Locator:
    return self.page.get_by_role(
        "heading", name="Организация не найдена", level=6
    )

@property
def empty_message(self) -> Locator:
    return self.page.get_by_text(
        "Ваш аккаунт не привязан ни к одной организации. Обратитесь к администратору.",
        exact=True,
    )

@property
def logout_button(self) -> Locator:
    return self.page.get_by_role("button", name="Выйти", exact=True)
```

### 3.23 UPDATE `pages/client/login_page.py`

NEW: subtitle "Введите данные для входа в систему" + heading h5 "Добро пожаловать
в BusinessHub". Login flow: enter phone (9 digits) → "Отправить код" →
переход к OTP с heading h5 "Код подтверждения" + paragraph "Код отправлен на
+998 90 555 55 18". OTP input placeholder ••••••.

Существующий POM покрывает базу — проверить i18n:
```python
"login.client.heading": "Добро пожаловать в BusinessHub",
"login.client.subtitle": "Введите данные для входа в систему",
"otp.heading": "Код подтверждения",
"otp.input_placeholder": "••••••",
"otp.resend_template": "Повторить через {} сек",
"otp.change_phone": "Изменить номер",
```

### 3.24 NEW component `pages/client/banner.py`

Под новым sidebar появилась шапка-banner с breadcrumb + 3 кнопки:
```python
from playwright.sync_api import Locator, Page


class ClientBanner:
    """Top banner: breadcrumb + 3 action buttons (Помощь/Уведомления/Настройки)."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self._banner: Locator = page.get_by_role("banner").first
        self._help_button: Locator = self._banner.get_by_role(
            "button", name="Помощь"
        )
        self._notifications_button: Locator = self._banner.get_by_role(
            "button", name="Уведомления"
        )
        self._settings_button: Locator = self._banner.get_by_role(
            "button", name="Настройки"
        )

    @property
    def banner(self) -> Locator:
        return self._banner

    @property
    def help_button(self) -> Locator:
        return self._help_button

    @property
    def notifications_button(self) -> Locator:
        return self._notifications_button

    @property
    def settings_button(self) -> Locator:
        return self._settings_button

    def breadcrumb_section(self) -> Locator:
        """Например 'Оргструктура' — первая часть breadcrumb."""
        return self._banner.locator("p").first

    def breadcrumb_page(self) -> Locator:
        """Например 'Сотрудники' — текущая страница."""
        return self._banner.locator("p").last
```

### 3.25 DELETE / DEPRECATE `pages/client/categories_page.py`

Фича удалена. `/categories` → 403. Файл можно либо:
- (Option A, рекомендуется) **Удалить** + grep usages, удалить тест-импорты
- (Option B) Оставить как stub с docstring "DEPRECATED: feature removed, see
  BUG-010 FIX"

Тест `tests/client/test_categories.py` уже помечен `xfail`/`skip` под BUG-010
— переписать в regression-страж (см. §4.5).

---

## 4. TEST CHANGES (детально)

### 4.1 Smoke (priority 1)

| Файл | Что делать |
|---|---|
| `tests/smoke/test_health.py` | Не трогать (если есть). Проверка что 3 URL отвечают. |
| `tests/smoke/test_admin_login.py` | **Skip** через `pytest.mark.skip(reason="BUG-029 admin auth broken")` + marker `needs_admin_creds`. |
| `tests/smoke/test_client_login.py` | Обновить landing: после OTP → либо `/tenant-select` (если ≥2 орг или 0 орг) либо `/home` (если 1 орг). Текущий тест ожидает `/dashboard|/documents|/tenant-select` — заменить на `/home|/tenant-select`. Использовать `settings.client_smoke_phone = "+998905555518"` (recon admin) + `settings.client_smoke_org = "[E2E recon] 8dgk1l"`. |
| `tests/smoke/test_sidebar_smoke.py` | **NEW**. Логин админ → expand все 4 subgroups → assert все 17 ссылок из ADMIN_NAV видны. |
| `tests/smoke/test_locale.py` | Проверить что RU локаль активна (через `_force_ru_lang` init script). Должна работать без изменений. |

Пример нового smoke:

```python
# tests/smoke/test_sidebar_smoke.py
import allure
import pytest
from playwright.sync_api import expect
from pages.client.sidebar import ClientSidebar, ADMIN_NAV, SUBGROUP_NAMES


@pytest.mark.smoke
@allure.title("Client UI sidebar содержит все 17 ссылок и 4 подгруппы")
def test_sidebar_full_navigation_visible(client_admin_page) -> None:
    sidebar = ClientSidebar(client_admin_page)
    sidebar.expand_all_subgroups()
    for section, subgroup, label, _path in ADMIN_NAV:
        with allure.step(f"Link «{label}» в section «{section}»"):
            expect(sidebar.link(label)).to_be_visible()
```

### 4.2 Positive (Client UI as Admin)

Использовать существующую фикстуру `client_admin_page` из `conftest.py`
(нужно обновить settings.client_smoke_phone/_org).

| File | Покрытие |
|---|---|
| `tests/client/test_home.py` (NEW) | 5 виджетов отображаются + heading h1 |
| `tests/client/test_documents.py` | UPDATE — heading "Документы" h4, view toggle Канбан/Таблица, columns (6 new), search placeholder "По заголовку или номеру..." |
| `tests/client/test_documents_layout.py` | UPDATE — старая STATUS_TABS константа удалена, проверить kanban_lanes (В ожидании/В работе/Завершён/Отказан) |
| `tests/client/test_documents_wizard.py` | Wizard сам не менялся, но первый шаг идёт с /documents → "Создать документ" — кнопка та же. Сохранять. |
| `tests/client/test_inbox_actions.py` | UPDATE columns (5 new), фильтры, кнопка "История" |
| `tests/client/test_inbox_org_misc.py` | UPDATE — heading + empty state |
| `tests/client/test_inbox_real_document.py` | Требует реальный документ — TBD после §4.3 |
| `tests/client/test_members_create.py` | UPDATE — добавить combobox Отдел в dialog, заменить i18n key field_role: "Системная роль" |
| `tests/client/test_members_edit_disable.py` | UPDATE — BUG-018 FIXED: проверить что "Отключить себя" disabled |
| `tests/client/test_members_negative.py` | UPDATE — required-маркеры (4 поля), submit без роли больше не silent (если BUG-026 FIXED дал inline-валидацию) |
| `tests/client/test_branches.py` | UNBLOCK — heading "Филиалы", auto-seeded "Главный офис" |
| `tests/client/test_departments_layout.py` | UPDATE — 6 columns, 2 фильтра, heading "Отделы" |
| `tests/client/test_positions.py` | UPDATE — 2 columns, BUG-019 FIXED (fresh tenant = 0 positions) |
| `tests/client/test_templates.py` | UPDATE — heading "Шаблоны", search "По названию шаблона..." |
| `tests/client/test_templates_upload.py` | TBD после tenant с реальными templates |
| `tests/client/test_routes.py` | UPDATE — heading "Шаблоны маршрутов", 6 columns |
| `tests/client/test_routes_constructor.py` | Не менять без MCP deep-dive (route builder UI) |
| `tests/client/test_roles.py` | UPDATE — heading "Роли и права", 4 system roles, columns (3) |
| `tests/client/test_roles_edit_delete.py` | UPDATE — открыть detail `/roles/{uuid}`, проверить 4 perm-groups (Документооборот/Кадры/Финансы/Настройки), BUG-011 FIXED (admin 50/50) |
| `tests/client/test_categories.py` | **CONVERT** в regression-страж — проверить что `/categories` → `/forbidden?from=/categories` (см. §4.5) |
| `tests/client/test_persons.py` (NEW) | Heading "Физические лица" h4, 9 columns, Add dialog (5 fields + Сохранить) |
| `tests/client/test_payslip.py` (NEW) | Heading h6 "Расчётные листы", placeholder "Выберите расчётный лист" |
| `tests/client/test_work_schedule.py` (NEW) | Empty "Нет данных" |
| `tests/client/test_vacation.py` (NEW) | Empty "Нет данных" |

Пример positive:

```python
# tests/client/test_persons.py
import allure
import pytest
from playwright.sync_api import Page, expect
from pages.client.persons_page import PersonsPage


@pytest.mark.positive
@allure.title("/persons — heading, 9 columns, add button, empty state")
def test_persons_page_layout(client_admin_page: Page) -> None:
    page = PersonsPage(client_admin_page).goto(settings.client_url)
    expect(page.heading).to_be_visible()
    expect(page.add_button).to_be_visible()
    expect(page.search).to_be_visible()
    for col in PersonsPage.COLUMNS:
        expect(page.column_header(col)).to_be_visible()
```

### 4.3 Negative

Для каждого positive — минимум 1 negative, по правилам CLAUDE.md §3a.
Конкретные кейсы (новые/обновлённые):

- `test_persons_negative.py` (NEW): дубль ПИНФЛ, невалидный email, невалидный
  phone в Add dialog
- `test_inbox_negative.py` (NEW): невалидные даты в фильтре, поиск без
  результатов
- `test_documents_negative.py` (UPDATE): submit wizard без selected route/template
- `test_login_negative.py` (UPDATE): сейчас работает; добавить кейс
  "phone не зарегистрирован" → ожидать тост из 404 AUTH_USER_NOT_FOUND
  (по BUG-001 — silent сейчас, ожидать `xfail` пока не починят)
- `test_members_negative.py` (UPDATE): submit без выбранной роли (BUG-026 FIXED
  — теперь должна быть inline-валидация, проверить)

### 4.4 RBAC

**Можно писать сейчас** (BUG-026 unblocked). Шаги:
1. Создать 3 invitee'ев в `[E2E recon] 8dgk1l` через Admin Member Create dialog
   (manually OR через `tests/conftest.py` session fixture):
   - Director (phone из phone_pool, role "Директор")
   - Manager (phone из phone_pool, role "Менеджер")
   - Сотрудник (phone из phone_pool, role "Сотрудник")
2. Логин каждым отдельно через 4 BrowserContext.
3. Параметризированно проверить таблицу прав из BRD §3.5 + наблюдаемое
   состояние UI.

```python
# tests/client/test_rbac.py - skeleton
import pytest

ROLES_NAV_TABLE = {
    "Администратор": {
        "/home", "/payslip", "/work-schedule", "/vacation",
        "/inbox", "/documents", "/templates", "/routes",
        "/members", "/branches", "/departments", "/persons",
        "/positions", "/org-positions",
        "/organization", "/roles", "/integration",
    },
    "Директор": {
        "/home", "/payslip", "/work-schedule", "/vacation",
        "/inbox", "/documents", "/templates", "/routes",
        "/members",
        # NOT: /branches, /roles, /integration (ожидаемо по BRD §3.5)
    },
    "Менеджер": {
        "/home", "/payslip", "/work-schedule", "/vacation",
        "/inbox", "/documents", "/templates", "/routes",
        # NOT: /integration, /roles
    },
    "Сотрудник": {
        "/home", "/payslip", "/work-schedule", "/vacation",
        "/inbox", "/documents",
        # NOT: остальное
    },
}


@pytest.mark.rbac
@pytest.mark.parametrize("role,allowed_urls", list(ROLES_NAV_TABLE.items()))
def test_role_can_access_allowed_urls(role, allowed_urls, ...):
    """Логин ролью → каждый allowed URL открывается без редиректа на /forbidden."""
    ...


@pytest.mark.rbac
@pytest.mark.parametrize("role,blocked_url", [
    ("Директор", "/branches"),
    ("Директор", "/integration"),
    ("Директор", "/roles"),
    ("Менеджер", "/integration"),
    ("Менеджер", "/roles"),
    # ... и т.д.
])
def test_role_cannot_access_blocked_url(role, blocked_url, ...):
    """Прямой URL → редирект на /forbidden."""
    ...
```

Многие из этих ассертов сейчас xfail (BUG-002/004..009 — RBAC bypass). Маркировать
`@pytest.mark.xfail(reason="BUG-002 RBAC bypass via direct URL", strict=True)`
чтобы XPASS = "баг починен, переключить".

### 4.5 Regression sentinel

Файл `tests/regression/test_bug_regressions.py` — все uncondtitional asserts
(пройдут когда баг починен, фейлятся когда снова сломали).

```python
# tests/regression/test_bug_regressions.py
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.regression
def test_bug010_categories_route_is_forbidden(client_admin_page: Page, settings) -> None:
    """BUG-010 FIXED 2026-05-18: /categories должен 403 (фича удалена)."""
    client_admin_page.goto(f"{settings.client_url}/categories")
    expect(client_admin_page).to_have_url(
        lambda u: "/forbidden" in u and "from=%2Fcategories" in u
    )
    expect(client_admin_page.get_by_text(
        "У вас нет доступа к разделу «Категории».", exact=True
    )).to_be_visible()


@pytest.mark.regression
def test_bug011_admin_role_shows_full_permissions(client_admin_page: Page, settings) -> None:
    """BUG-011 FIXED 2026-05-18: Администратор должен иметь все 50/50 прав."""
    # Открыть /roles → найти строку Администратор → проверить '50/50' или '50 / 50'
    client_admin_page.goto(f"{settings.client_url}/roles")
    admin_row = client_admin_page.get_by_role("row").filter(
        has_text="Администратор"
    ).first
    expect(admin_row).to_contain_text("50/50")


@pytest.mark.regression
def test_bug018_admin_cannot_disable_self(client_admin_page: Page, settings) -> None:
    """BUG-018 FIXED 2026-05-18: row-action "Отключить" должен быть disabled
    в собственной строке + tooltip 'Нельзя отключить себя'."""
    client_admin_page.goto(f"{settings.client_url}/members")
    # Найти строку с phone текущего юзера
    own_phone = "998905555518"  # settings.client_smoke_phone без +
    row = client_admin_page.get_by_role("row").filter(has_text=own_phone).first
    disable_btn = row.get_by_role("button", name="Отключить")
    expect(disable_btn).to_be_disabled()


@pytest.mark.regression
def test_bug019_fresh_tenant_has_no_seed_positions(client_admin_page: Page, settings) -> None:
    """BUG-019 FIXED 2026-05-18: свежий tenant должен иметь 0 должностей.
    Это assertion работает только для свежесозданного tenant'а — для постоянной
    фикстуры с уже добавленными должностями тест неверен. Запускать с
    @pytest.mark.fresh_tenant фикстурой."""
    client_admin_page.goto(f"{settings.client_url}/positions")
    expect(client_admin_page.get_by_text(
        "Должности не найдены", exact=True
    )).to_be_visible()


@pytest.mark.regression
def test_bug026_role_combobox_has_4_system_roles(client_admin_page: Page, settings) -> None:
    """BUG-026 FIXED 2026-05-18: combobox 'Системная роль' содержит 4 системные роли."""
    from pages.client.members_page import MembersPage
    from pages.client.member_create_dialog import MemberCreateDialog
    MembersPage(client_admin_page).goto(settings.client_url).click_add()
    dialog = MemberCreateDialog(client_admin_page)
    expect(dialog.dialog).to_be_visible()
    # Открыть combobox роль
    dialog._role.click()  # type: ignore[attr-defined]
    listbox = client_admin_page.get_by_role("listbox")
    for role in ("Сотрудник", "Менеджер", "Директор", "Администратор"):
        expect(listbox.get_by_role("option", name=role, exact=True)).to_be_visible()


@pytest.mark.regression
def test_bug027_client_env_js_has_correct_api_url(client_admin_page: Page, settings) -> None:
    """BUG-027 PARTIAL-FIXED для Client UI: runtime/env.js должен содержать
    канонический API_URL и Cache-Control: no-store."""
    response = client_admin_page.request.get(f"{settings.client_url}/runtime/env.js")
    assert response.status == 200
    text = response.text()
    assert "https://dev-hub-api.greatmall.uz" in text
    assert response.headers.get("cache-control", "").lower().__contains__("no-store")


# Tests for STILL OPEN bugs — xfail strict so XPASS notifies us
@pytest.mark.regression
@pytest.mark.xfail(reason="BUG-027 Admin UI: runtime/env.js still has empty API_URL", strict=True)
def test_bug027_admin_env_js_has_correct_api_url(page: Page, settings) -> None:
    """BUG-027 для Admin UI всё ещё broken (2026-05-18)."""
    response = page.request.get(f"{settings.admin_url}/runtime/env.js")
    text = response.text()
    assert "https://dev-hub-api.greatmall.uz" in text


@pytest.mark.regression
@pytest.mark.xfail(reason="BUG-028: RFC 7807 type-link leaks localhost:8080", strict=True)
def test_bug028_no_localhost_in_rfc7807_type(page: Page) -> None:
    # Достаточно вызвать любой error endpoint и assert что type не содержит localhost
    ...
```

### 4.6 E2E (главный сценарий)

`tests/e2e/test_admin_to_client_full_flow.py` сейчас сильно завязан на Admin UI
flow → **BLOCKED by BUG-029**. Замораживать через `pytest.mark.skip(reason=
"BUG-029 admin login broken")` + marker `needs_admin_creds`. Альтернативно —
переписать под PLATFORM_ADMIN OTP-flow (через Client UI как Super Admin →
direct REST tenant create), но это нарушает UI-only правило. Не делать сейчас.

---

## 5. ПОРЯДОК ИМПЛЕМЕНТАЦИИ (для Codex)

### Шаг 1 (2-3 часа, без backend dependencies)
1. UPDATE `config/settings.py` defaults (см. §2.3)
2. UPDATE `.env.example` с новыми ключами
3. UPDATE `data/i18n.py` — добавить все новые/изменённые ключи из §3
4. CREATE 5 новых POM (home/persons/person_create_dialog/payslip/work_schedule/
   vacation/forbidden) + ClientBanner — §3.1-3.7, 3.24
5. **MAJOR REWRITE** `pages/client/sidebar.py` (§3.8)
6. UPDATE member_create_dialog + members_page (§3.9, 3.10)
7. UPDATE documents_page + inbox_page (§3.11, 3.12)
8. UPDATE organization_page + integration (§3.13, 3.14)
9. UPDATE branches/departments/positions/templates/routes/roles + RoleDetailPage
   (§3.15-3.21)
10. UPDATE select_organization_page (§3.22)
11. DELETE/DEPRECATE categories_page (§3.25)
12. ВСЕ ТЕСТЫ — `pytest --collect-only` должен пройти без ImportError
    (`ruff check`, `mypy --strict` тоже)

### Шаг 2 (2-3 часа, smoke tests)
1. UPDATE `tests/smoke/test_client_login.py` под новый landing `/home`
2. CREATE `tests/smoke/test_sidebar_smoke.py` (§4.1)
3. SKIP `tests/smoke/test_admin_login.py` (`pytest.mark.skip` + marker
   `needs_admin_creds`) до фикса BUG-029
4. RUN `pytest -m smoke -n 2` локально, убедиться зелёное

### Шаг 3 (3-4 часа, positive tests)
1. UPDATE существующие client тесты (см. §4.2 таблицу)
2. CREATE tests/client/test_home.py, test_persons.py, test_payslip.py,
   test_work_schedule.py, test_vacation.py
3. RUN `pytest tests/client/ -m positive --tb=short` локально

### Шаг 4 (после ручного провижна 3 invitee'ев)
Для RBAC и multi-user сценариев нужны 3 invitee'я (Director/Manager/Сотрудник)
в текущем tenant'е `[E2E recon] 8dgk1l`. Codex может попросить human их создать
вручную через Client UI Admin или (с осторожностью) через REST + Super Admin JWT.

1. ADD 3 invitee'ев (Director/Manager/Сотрудник). Зафиксировать phones в
   `data/test_fixtures.py` или `tests/conftest.py` session fixture.
2. UPDATE `tests/client/test_rbac.py` (§4.4)
3. CREATE regression-стражи `tests/regression/test_bug_regressions.py` (§4.5)
4. RUN полный прогон без `e2e` и `needs_admin_creds`

### Шаг 5 (после фикса BUG-029)
1. Получить от dev-team валидный Super Admin пароль или новый sub-account
2. Update `config/settings.py` + `.env`
3. Снять skip с `tests/smoke/test_admin_login.py`
4. Восстановить `tests/admin/*` (test_company_create, test_admins_layout, и т.д.)
5. Восстановить `tests/e2e/test_admin_to_client_full_flow.py`

### Шаг 6 (после фикса BUG-027 Admin UI)
1. Снять `xfail` с `test_bug027_admin_env_js_has_correct_api_url`
2. Add `Cache-Control: no-store` regression assertion для Admin UI

---

## 6. MARKERS (pytest.ini)

Текущий список из pytest.ini уже хорош. Добавить:

```ini
markers =
    # ... existing markers ...
    needs_backend: blocked by BUG-024-partial — frontend ждёт endpoints (см. AUTOTEST_PLAN_FOR_CODEX.md §1)
    needs_admin_creds: blocked by BUG-029 — Admin UI Super Admin login broken
    fresh_tenant: тест требует свежий tenant (0 positions/departments/users)
    needs_invitees: тест требует 3 invitee'ев (Director/Manager/Сотрудник) — см. §5 Шаг 4
```

Существующие markers, которые мы используем:
- `smoke`, `positive`, `negative`, `edge_case`, `rbac`, `e2e`, `serial`,
  `eimzo_local_only`, `maintenance`, `allow_console_errors`, `creates_data`,
  `regression`, `visual`, `allow_uz_default`

---

## 7. КОМАНДЫ ЗАПУСКА

```bash
# Smoke (без EIMZO и Admin UI)
pytest -m "smoke and not eimzo_local_only and not needs_admin_creds" -n 4

# Positive Client UI (после Шага 3)
pytest tests/client/ -m "positive and not needs_backend and not needs_invitees"

# RBAC (после Шага 4)
pytest -m "rbac and not needs_admin_creds"

# Regression sentinels
pytest -m regression

# Полный прогон (после Шагов 1-4, до фикса BUG-029)
pytest -m "not eimzo_local_only and not needs_admin_creds and not e2e" -n auto

# E2E (только после фикса BUG-029, EIMZO connected, в headed mode)
pytest -m "e2e and eimzo_local_only" --headed -s
```

---

## 8. ИЗВЕСТНЫЕ БАГИ (status на 2026-05-18 — не закрывать, только обходить)

| BUG | Severity | Status (2026-05-18) | Impact на тесты | Workaround |
|---|---|---|---|---|
| BUG-001 | Major | OPEN | Silent fail в форме создания → негативные тесты валидации не получат toast | Тесты `xfail` на ассерт toast'а |
| BUG-002 | Critical | OPEN | RBAC bypass через direct URL | RBAC negative тесты `xfail strict` |
| BUG-003 | Major | OPEN (Mock 1C) | Mock 1C employees broken | E2E тесты пропускают этот шаг |
| BUG-004..009 | Var | OPEN (RBAC класс) | Аналогично BUG-002 | xfail RBAC |
| BUG-010 | Minor | **FIXED** | /categories → /forbidden | Regression sentinel в §4.5 |
| BUG-011 | Major | **FIXED** | Admin role 50/50 | Regression sentinel |
| BUG-012..017 | Var | OPEN (recon не делал deep) | Различные UC bugs | xfail |
| BUG-018 | Major | **FIXED** | Self-disable disabled + tooltip | Regression sentinel |
| BUG-019 | Major | **FIXED** | 0 seed positions in fresh tenant | Regression sentinel под fresh_tenant marker |
| BUG-020..023 | Var | OPEN | разные | TBD |
| BUG-024 | Critical | **FRONTEND-FIXED**, backend подняли /users/* namespace | Все business endpoints отвечают; auth остался на `/auth/otp/*` | OK для тестов |
| BUG-026 | Minor | **FIXED** | Role combobox содержит 4 опции | Regression sentinel |
| BUG-027 | Major | **PARTIAL**: Client UI fixed, Admin UI broken | Admin UI runtime/env.js = `""` | Тесты Admin UI требуют `needs_admin_creds` skip, фактический fallback на same-origin срабатывает только в incognito |
| BUG-028 | Minor | OPEN | localhost:8080 в RFC 7807 type | xfail strict regression |
| BUG-029 | Major | OPEN | Admin UI Super Admin login broken | `needs_admin_creds` marker |

### Новые потенциальные баги — добавить в §10 RECOMMENDATIONS (не в Bugs.txt)

См. §10.

---

## 9. ЧТО НЕ ДЕЛАТЬ

- **НЕ менять `/CLAUDE.md`** (стабильный config)
- **НЕ закрывать существующие баги** (BUG-001..029) в `Bugs.txt` — статус нужно
  проверять отдельным sweep'ом, не QA-агентом-в-Codex
- **НЕ удалять файлы `pages/`** без grep-проверки usages (только rename/update
  где сказано выше). `categories_page.py` — единственное исключение (§3.25)
- **НЕ писать API-level тесты** (UI-only, см. CLAUDE.md §13)
- **НЕ использовать Svelte/MUI CSS classes** как локаторы
  (`.css-xxxxxx`, `.MuiButton-root` — change-prone)
- **НЕ использовать `time.sleep()` / `wait_for_timeout()`** — нужно `expect().to_*`
  с timeout
- **НЕ удалять `tests/client/test_categories.py`** — переписать его в regression
  страж для `/categories` → 403
- **НЕ создавать новые `.md` файлы с отчётами** — этот документ единственный
  output. Финальные findings от Codex должны быть в commit message или PR description
- **НЕ ходить в `/Documents/core/`** — это продуктовый репозиторий, read-only
- **НЕ делать `git commit`** без явного запроса от human
- **НЕ запускать `pytest` параллельно с EIMZO** (одна флешка на машине)
- **НЕ полагаться на старые phones**: `+998913030519`, `+998913030301/302/303`,
  `+998904444019` — все стёрты после wipe 2026-05-18
- **НЕ полагаться на старые tenant_ids / integration_keys** из истории
  `test_fixtures.md` — все stale

---

## 10. RECOMMENDATIONS (новые потенциальные баги — на dev-team consideration)

Эти НЕ добавляйте в `Bugs.txt`. Сначала покажите human-инженеру для решения.

1. **i18n leaks**: "Slug" в `/organization > Данные`, "persons", "organization",
   "integration", "Version" в разных местах — английские строки в RU UI.
   Trivial-severity.
2. **Tenant ID in plain text**: `/organization > Данные` показывает UUID
   `Tenant ID: a51f7085-95a4-4b71-930f-30ef974c418e`. Юзер может его скопировать
   и встроить во внешние интеграции — это не secret, но информационный leak.
3. **Naming inconsistency**:
   - Sidebar "Мои задания" ↔ URL `/documents` ↔ heading "Документы"
   - Sidebar "Маршруты" ↔ URL `/routes` ↔ heading "Шаблоны маршрутов"
   - Sidebar "Пользователи" ↔ URL `/members` ↔ heading "Пользователи" ↔
     breadcrumb "Сотрудники" (4 термина для одной сущности!)
4. **/integration 1C card**: одновременно показывает кнопку "Настроить" и
   badge "Скоро" (контрадикторно). Подозреваю что badge должен скрываться
   когда integration уже подключена (создание tenant автоматически выдаёт key).
5. **Admin role permissions discrepancy**: total "50/50" но суммирование групп
   даёт 48 (Документооборот 12 + Кадры 19 + Финансы 5 + Настройки 12 = 48).
   2 невидимых permissions где-то — нужен audit.
6. **`/branches` auto-seed "Главный офис"**: после создания tenant'а
   автоматически создаётся 1 филиал "Активен/Главный офис". Если это behavior
   намеренное — задокументировать в onboarding. Если нет — bug.
7. **POST /api/v1/auth/otp/verify field name**: бэкенд требует `otp` (не `code`)
   — старая память упоминала `code`. Возможно был breaking change без
   уведомления QA. Frontend-bundle `sdk.gen-*.js` уже на новом контракте.
8. **`/work-schedule` и `/vacation` — пустые страницы без heading**. Юзер видит
   только "Нет данных" — нет даже h1 "График работы". Bare placeholder UX
   — добавить хотя бы page-title.
9. **PLATFORM_ADMIN tenants[]:[]**: Super Admin (`+998991234567`) после OTP
   получает tenants:[], попадает на `/tenant-select` с пустым state "Организация
   не найдена" — это правильно (он не tenant-user, он platform), но UX-сообщение
   misleading: говорит "Обратитесь к администратору", хотя сам Super Admin и
   есть администратор. Нужна отдельная PLATFORM_ADMIN landing page (либо редирект
   на Admin UI dashboard).
10. **All Admin UI tenants tests blocked**: 1 tenant у нас наш (`[E2E recon]`),
    2 — чужие. Это не bug, а observation: для UC-4.1 (create tenant), UC-4.2
    (list/manage), UC-4.3 (disable/enable) нужен provisioned Super Admin
    credentials (BUG-029 фикс).

---

## 11. APPENDIX A — ОБЪЁМ ИЗМЕНЕНИЙ

### Файлы CREATE (8)
- `pages/client/home_page.py`
- `pages/client/persons_page.py`
- `pages/client/person_create_dialog.py`
- `pages/client/payslip_page.py`
- `pages/client/work_schedule_page.py`
- `pages/client/vacation_page.py`
- `pages/client/forbidden_page.py`
- `pages/client/role_detail_page.py`
- `pages/client/banner.py`

### Файлы UPDATE (15)
- `pages/client/sidebar.py` (MAJOR REWRITE)
- `pages/client/member_create_dialog.py` (add Отдел)
- `pages/client/members_page.py` (BUG-018 method)
- `pages/client/documents_page.py` (rewrite view + columns)
- `pages/client/inbox_page.py` (rewrite columns + toolbar)
- `pages/client/organization_page.py` (heading text + IntegrationPage)
- `pages/client/positions_page.py` (columns const)
- `pages/client/routes_page.py` (heading "Шаблоны маршрутов")
- `pages/client/branches_page.py` (unblock)
- `pages/client/departments_page.py` (6 columns + filters)
- `pages/client/templates_page.py` (heading + search)
- `pages/client/roles_page.py` (heading "Роли и права" + 4 perm groups)
- `pages/client/select_organization_page.py` (empty state)
- `pages/client/login_page.py` (i18n keys)
- `pages/client/otp_page.py` (i18n keys)
- `data/i18n.py` (множество ключей)
- `config/settings.py` (defaults)
- `.env.example`
- `pytest.ini` (markers)

### Файлы DELETE / DEPRECATE (1)
- `pages/client/categories_page.py`

### Тесты CREATE
- `tests/smoke/test_sidebar_smoke.py`
- `tests/client/test_home.py`
- `tests/client/test_persons.py`
- `tests/client/test_persons_negative.py`
- `tests/client/test_payslip.py`
- `tests/client/test_work_schedule.py`
- `tests/client/test_vacation.py`
- `tests/client/test_inbox_negative.py`
- `tests/regression/test_bug_regressions.py` (sentinels для FIXED bugs)

### Тесты UPDATE
- `tests/smoke/test_client_login.py`
- `tests/smoke/test_admin_login.py` (skip)
- `tests/client/test_documents*.py`
- `tests/client/test_inbox_*.py`
- `tests/client/test_members_*.py`
- `tests/client/test_branches.py`
- `tests/client/test_departments_layout.py`
- `tests/client/test_positions.py`
- `tests/client/test_templates*.py`
- `tests/client/test_routes*.py`
- `tests/client/test_roles*.py`
- `tests/client/test_categories.py` (convert to regression)
- `tests/admin/*` (все skip через `needs_admin_creds`)
- `tests/e2e/*` (skip через `needs_admin_creds`)

---

## 12. APPENDIX B — Полный список новых/обновлённых i18n keys

```python
# Login / OTP (минор обновления)
"login.client.heading": "Добро пожаловать в BusinessHub",
"login.client.subtitle": "Введите данные для входа в систему",
"otp.heading": "Код подтверждения",
"otp.input_placeholder": "••••••",

# Home (NEW page)
"client.home.greeting_template": "Добро пожаловать, {}",
"client.home.widget_payslip": "Текущие начисления",
"client.home.widget_vacation": "Вам доступно дней отпуска",
"client.home.widget_schedule": "Ваш график работы",
"client.home.widget_my_docs": "Мои документы",
"client.home.widget_my_tasks": "Мои задачи",
"client.home.empty_data": "Нет данных",
"client.home.btn_all_payslips": "Все расчётные листы →",
"client.home.btn_details": "Подробнее →",

# Sidebar sections
"client.sidebar.section_workspace": "Рабочее место",
"client.sidebar.section_documents": "Документы",
"client.sidebar.section_dictionaries": "Справочники",
"client.sidebar.section_orgstructure": "Оргструктура",
"client.sidebar.section_settings": "Настройки",
"client.sidebar.subgroup_my_cabinet": "Мой кабинет",
"client.sidebar.subgroup_docflow": "Документооборот",
"client.sidebar.subgroup_orgstructure": "Оргструктура",
"client.sidebar.subgroup_settings": "Настройки",
"client.sidebar.link_home": "Главная",
"client.sidebar.link_payslip": "Расчётный лист",
"client.sidebar.link_work_schedule": "График работы",
"client.sidebar.link_vacation": "Отпуск",
"client.sidebar.link_inbox": "Входящие документы",
"client.sidebar.link_documents": "Мои задания",
"client.sidebar.link_templates": "Шаблоны",
"client.sidebar.link_routes": "Маршруты",
"client.sidebar.link_members": "Пользователи",
"client.sidebar.link_branches": "Филиалы",
"client.sidebar.link_departments": "Отделы",
"client.sidebar.link_persons": "Физические лица",
"client.sidebar.link_positions": "Должности",
"client.sidebar.link_orgpositions": "Штатные позиции",
"client.sidebar.link_organization": "Организация",
"client.sidebar.link_roles": "Системные роли",
"client.sidebar.link_integration": "Интеграция",
"client.sidebar.user_menu_settings": "Настройки",
"client.sidebar.user_menu_logout": "Выйти",

# Banner
"client.banner.help": "Помощь",
"client.banner.notifications": "Уведомления",
"client.banner.settings": "Настройки",

# Inbox
"client.inbox.title": "Требуют подписи",
"client.inbox.subtitle": "Задания, требующие согласования, подписи или отказа",
"client.inbox.refresh": "Обновить",
"client.inbox.history": "История",
"client.inbox.search_placeholder": "Поиск по заголовку или номеру...",
"client.inbox.empty_title": "Задания отсутствуют",

# Documents
"client.documents.title": "Документы",
"client.documents.create_button": "Создать документ",
"client.documents.search_placeholder": "По заголовку или номеру...",
"client.documents.view_kanban": "kanban view",
"client.documents.view_table": "table view",
"client.documents.date_filter": "Фильтр по дате",

# Members
"client.members.field_role": "Системная роль",
"client.members.field_department": "Отдел",
"client.members.col_role": "Системная роль",
"client.members.tooltip_cant_disable_self": "Нельзя отключить себя",

# Organization
"client.organization.title": "Настройки организации",

# Roles
"client.roles.title": "Роли и права",
"client.roles.add_button": "Создать роль",
"client.roles.system_badge": "Системная",
"client.roles.detail.heading": "Редактировать роль",
"client.roles.detail.expand_all": "Развернуть все",
"client.roles.detail.collapse_all": "Свернуть все",
"client.roles.detail.back": "Назад",
"client.roles.detail.save": "Сохранить",
"client.roles.group_docflow": "Документооборот",
"client.roles.group_hr": "Кадры",
"client.roles.group_finance": "Финансы",
"client.roles.group_settings": "Настройки",

# Persons
"client.persons.title": "Физические лица",
"client.persons.add_button": "Добавить",
"client.persons.search_placeholder": "Поиск...",
"client.persons.dialog_title": "Добавить физлицо",
"client.persons.field_full_name": "ФИО",
"client.persons.field_pinfl": "ПИНФЛ",
"client.persons.field_birth_date": "Дата рождения",
"client.persons.field_email": "Email",
"client.persons.field_phone": "Телефон",
"client.persons.dialog_submit": "Сохранить",
"client.persons.dialog_cancel": "Отмена",

# Payslip / WorkSchedule / Vacation
"client.payslip.title": "Расчётные листы",
"client.payslip.empty": "Расчётные листы не найдены",
"client.payslip.placeholder": "Выберите расчётный лист",
"client.work_schedule.empty": "Нет данных",
"client.vacation.empty": "Нет данных",

# Branches
"client.branches.title": "Филиалы",
"client.branches.subtitle": "Структура головного офиса и филиалов организации.",
"client.branches.add_button": "Добавить филиал",
"client.branches.search_placeholder": "Поиск по названию…",  # NB ellipsis ...
"client.branches.tab_table": "Таблица",
"client.branches.tab_hierarchy": "Иерархия",

# Templates
"client.templates.title": "Шаблоны",
"client.templates.add_button": "Добавить шаблон",
"client.templates.search_placeholder": "По названию шаблона...",

# Routes
"client.routes.title": "Шаблоны маршрутов",
"client.routes.add_button": "Создать маршрут",

# Forbidden
"client.forbidden.title": "Доступ запрещён",
"client.forbidden.message_template": "У вас нет доступа к разделу «{}».",
"client.forbidden.home_button": "На главную",

# Select organization (empty state)
"client.tenant_select.empty_heading": "Организация не найдена",
"client.tenant_select.empty_message": "Ваш аккаунт не привязан ни к одной организации. Обратитесь к администратору.",
"client.tenant_select.logout": "Выйти",
```

---

## 13. APPENDIX C — Локаторы для frontend chunks (debug aid)

Если Codex упрётся в "не вижу элемент", может быть полезно знать какой chunk
рендерит страницу:

| URL | Vite chunk |
|---|---|
| /home | `index-DK1sKi9e.js` (main bundle, ~705 KB) |
| /members | `member-DZniUr9D.js` |
| /persons | `page-C9zxXbCm.js` (вероятно, persons specific) |
| /positions | `position-CgTG2u8L.js` |
| /org-positions | `org-position-CwJs5XuQ.js` |
| /departments | `department-D8xbWeXT.js` |
| /roles | `role-BzOTNuy1.js` + `rbac-Biu6OyHb.js` |
| /routes | `route-DEGGPJxs.js` + `route-editor-BiRl_sWk.js` + `builder-DW_C4nlK.js` |
| /templates | `template-C3LOLJyr.js` + `upload-pdf-yQXS3D6G.js` + `upload-file-RbPKLVvZ.js` |
| EDMS workflows | `workflow-A2Ihdger.js` + `workflow-gthVWKfF.js` + `useDeployWorkflowMutation-D7mN2MqH.js` |
| Document detail | `detail-pane-Cc-qJApC.js` + `PdfViewer-0rT37iBo.js` |
| API client | `sdk.gen-BPDzqoFb.js` + `types.gen-JD53uSjn.js` + `schemas-IadgLkKh.js` + `instance-DtioUwsV.js` + `api-error-BgtH7rOs.js` |
| Auth/session | `session-CFjZHutR.js` + `useStore-Ch8Dhdtm.js` |
| RBAC client | `rbac-Biu6OyHb.js` |
| Common helpers | `formatDate-BXDGAdJk.js`, `initials-ChQwBxRo.js`, `redirect-DUhj2vUJ.js` |

Hashes изменятся после каждого frontend deploy — не использовать в локаторах,
только для debug.

---

## 14. APPENDIX D — Известные WORKAROUNDS для MCP/Playwright

(Codex обычно не сталкивается, но если будет писать helper в `conftest.py`:)

1. **MUI Select**: `.click()` через JS НЕ открывает dropdown. Использовать
   `dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))` ИЛИ
   Playwright-нативный `locator.click()`.
2. **React Hook Form**: НЕЛЬЗЯ устанавливать value через
   `Object.getOwnPropertyDescriptor(...).set + input event` — RHF state не
   обновится. Использовать `locator.fill()` (он триггерит правильные React events).
3. **runtime/env.js cache**: фронтенд может закэшировать старый env.js. Если
   тест начинается со старого `__ENV__.API_URL = ""` — все API-fetch'и улетают
   на localhost. Текущий conftest имеет init script с polling fallback — должен
   работать.
4. **Sidebar "Настройки" subgroup**: может быть outside viewport. Перед click
   обязательно `scroll_into_view_if_needed()`.
5. **Empty combobox placeholder** detection:
   ```python
   listbox = page.get_by_role("listbox")
   opts = listbox.get_by_role("option").all()
   real_opts = [o for o in opts if (o.text_content() or "").strip() != "Выберите..."]
   if not real_opts:
       raise RuntimeError("Combobox empty — BUG-026 family regression?")
   ```

---

> **END OF PLAN** — следующий update после прохождения Шагов 1-2 и фикса BUG-029.
> Дата составления: 2026-05-18.
> Автор recon: businesshub-qa-verifier (Claude Opus 4.7).
