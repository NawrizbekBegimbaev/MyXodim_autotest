# MyXodim — Sanity E2E Suite (Claude Code instructions)

Ты — QA Automation Engineer на проекте **MyXodim** (бывш. BusinessHub) — SaaS
документооборот, Узбекистан. Пишешь **UI-only** автотесты на Playwright (sync) +
pytest, Page Object Model. Никаких HTTP/API-вызовов из тестов. Цель сьюты —
**ежедневный sanity-прогон** против staging.

> Полный исходник продукта склонирован в `_core_src/` (read-only reference,
> gitignored). Ветка `dev`, репо `gitlab.greatmall.uz/soft-team-pro/business-hub/core`.
> Старая (BusinessHub) сьюта перемещена в `archive/legacy-2026-06/`.

> ⛔️ **СТРОГО ЗАПРЕЩЕНО менять код, импортированный из GitLab** (`_core_src/` —
> исходники продукта MyXodim/BusinessHub). Только **чтение** для справки
> (локаторы, маршруты, поведение). Никаких правок, коммитов, форматирования,
> рефакторинга, `git push` в их репозиторий. Если нужна правка в продукте —
> завести тикет/сообщить команде, а не редактировать `_core_src/`. Изменения
> делаем только в коде ЭТОЙ тестовой сьюты.

---

## 1. Окружение — STAGING (по умолчанию)

| UI | URL |
|----|-----|
| Client (сотрудник) | https://myxodim-stage.greatmall.uz |
| Admin (платформа)  | https://myxodim-admin-stage.greatmall.uz |
| Mock 1C            | https://mock1c-stage.greatmall.uz |
| API (не дёргаем)   | https://myxodim-api-stage.greatmall.uz |

URL и доступы — только через `.env` (`config/settings.py`). Не хардкодим.

**Локаль UI — RU** (не uz, несмотря на старые доки). Ассерты по русским строкам.

---

## 2. Доступы (staging)

- **Client login:** телефон + OTP. Staging принимает **любой 6-значный OTP**
  (`TEST_OTP=123456`) для зарегистрированного номера. Рабочий номер:
  `+998994002396` (роль Сотрудник, орг Greatmall/test1) → один тенант → сразу `/home`.
- **Admin login:** телефон + пароль → `+998991234567` / `admin123` → `/dashboard`.

**OTP rate-limit:** `POST /auth/otp/request` отдаёт **429**, если повторить запрос
номера в пределах ~60 сек. Поэтому клиент логинится **один раз за прогон** в
session-фикстуре `client_page`, аутентифицированный контекст переиспользуется
всеми client-тестами. Не плодить логины на один номер.

**Токены короткоживущие**, admin-токен в sessionStorage → `storage_state`
**ненадёжен**. Логинимся через UI в рамках прогона и держим живой контекст.

---

## 3. Что покрываем — 29 кейсов из BusinessHub_Sanity_Report3.xlsx

Источник истины — `BusinessHub_Sanity_Report3.xlsx` (29 кейсов). Маркер
`@pytest.mark.sanity` на всём наборе. Allure-title каждого теста = номер+название
кейса (видны в TestOps 1:1 с отчётом).

**Модель прогона (повторяет ручной проход):**
1. Платформенный админ логинится в Admin UI (session).
2. Создаётся свежая `[SANITY]`-компания + её админ (кейс 4) → у свежей компании
   чистые справочники (кейс 6 «бесплатно»).
3. Логинимся в Client UI под этим админом (один OTP/прогон) и гоняем клиентские
   кейсы 5–29.

**Статус кейсов: ✅ все 29 реализованы и зелёные.**
- Admin UI: 1 логин→/dashboard, 2 дашборд-метрики, 3 новый админ, 4 создание компании.
- Client UI: 5 логин OTP, 6 чистые справочники, 8–27 страницы/списки/формы (под
  ролью Администратор), 7 интеграция 1С (Mock1C push по ключу → импорт в клиент),
  28 RBAC (EMPLOYEE → /forbidden vs ADMINISTRATOR доступ), 29 запуск документа
  (создание из шаблона → черновик).

**Граница кейса 29:** доведён до черновика. Полный submit→«Согласовать» НЕ
автоматизирован: на странице `/documents/create` строка шага маршрута непрерывно
ре-рендерится (резолв workflow шаблона с неразрешимыми акторами) → интеракция
нестабильна. Это продуктовый UX-дефект — задокументировать и хардить отдельно.
Также `/inbox` = «Требуют подписи» (подпись), COORDINATE-задачи туда не попадают.

**Файлы:** `tests/sanity/test_admin_ui.py` (1–4), `test_client_login.py` (5),
`test_directories_clean.py` (6), `test_onec_integration.py` (7),
`test_client_pages.py` (8–27), `test_rbac.py` (28),
`test_zz_document_circulation.py` (29).

**Важно — стабильность:** НИКОГДА не использовать `wait_for_load_state("networkidle")`
— SPA держит живые соединения (поллинг уведомлений), networkidle не наступает →
30с таймаут. Полагаемся на auto-retry `expect(...).to_be_visible()`.

**Данные:** каждый прогон создаёт `[SANITY] <epoch>` компанию/админов с уникальными
телефон/ИНН/ПИНФЛ (см. `config/sanity_data.py`), не чистим (по договорённости).

---

## 4. Реальные локаторы (проверены на staging)

data-testid почти нет. Приоритет: `name`-атрибуты форм → роль/лейбл/плейсхолдер.

**Client login (`/login`):** `input[name="phone"]` (лейбл «Номер телефона»),
кнопка «Отправить код»; OTP-шаг: `input[name="otp"]` (лейбл «Код подтверждения»),
кнопка «Войти». Лендинг `/home`, heading «Добро пожаловать, …».

**Client nav (роль Сотрудник):** Главная `/home`, Расчётный лист `/payslip`,
График работы `/work-schedule`, Отпуск `/vacation`, Входящие документы `/inbox`,
Исходящие документы `/documents`.

**Документы:** список `/documents` (heading «Документы», кнопка
«Запустить документ») → `/documents/create` (heading «Создать новый документ»,
MUI-autocomplete лейбл «Вид документа», кнопка «Сохранить как черновик»). Выбор
шаблона авто-заполняет форму и строит маршрут.

**Admin login (`/login`):** `input[name="phone"]` (лейбл «Телефон»),
`input[name="password"]` (лейбл «Пароль»), кнопка «Войти» → `/dashboard`
(heading «Дашборд»). Nav: Дашборд `/dashboard`, Компании `/tenants`,
Администраторы `/admins`.

**Mock 1C (`/`):** без логина (ключ интеграции). heading «Mock 1C»,
плейсхолдер ключа «bh_live_...», кнопка «Сохранить». Вкладки (Должности/
Сотрудники/Шаблоны…) открываются только после подключения по ключу.

Списки несут query-параметры в URL (`/documents?page=…`). Матчим URL по
regex/prefix, не точной строкой.

---

## 5. Правила кода

- Page Object: класс на страницу, локаторы в `__init__`, методы — действия/геттеры
  **без ассертов**. Ассерты только в тестах через `expect(...).to_*`
  (auto-retrying). Глобальный timeout задан в `conftest.py` (`expect.set_options`).
- Контекст: `viewport 1440x900`, `locale ru-RU`, `timezone Asia/Tashkent`,
  `ignore_https_errors`. Bundled Chromium (EIMZO в sanity не нужен).
- ЗАПРЕЩЕНО: `time.sleep`, `wait_for_timeout` для синхронизации; ассерты в POM;
  хардкод URL/телефонов/таймаутов; HTTP-вызовы из тестов; logout/login через UI
  для смены пользователя.
- Артефакты при падении: trace/screenshot/video (настроено в `pytest.ini`);
  client-сессия пишет trace в `test-results/`.

---

## 6. Запуск

```bash
.venv/bin/python -m pytest -m sanity          # весь ежедневный набор
.venv/bin/python -m pytest -m smoke           # только smoke
.venv/bin/python -m pytest -m happy_path      # только happy-path
scripts/run_sanity.sh                         # daily entrypoint (Allure + JUnit)
allure serve allure-results                   # отчёт
```

Python 3.13 в `.venv`. Зависимости — `pyproject.toml`.

---

## 7. Структура

```
config/settings.py          — URL, доступы, OTP из .env (pydantic-settings)
conftest.py                 — фикстуры: cfg, browser_context_args, client_context, client_page
pages/base_page.py          — goto, wait_loaded
pages/client/               — login, home, documents, create_document
pages/admin/                — login, dashboard
pages/mock1c/               — connection
tests/smoke/                — health (3 UI), admin_login, client_login
tests/sanity/               — document_create_to_draft (happy-path)
scripts/run_sanity.sh       — ежедневный запуск
_core_src/                  — исходник продукта (reference, gitignored)
archive/legacy-2026-06/     — старая BusinessHub-сьюта
```
