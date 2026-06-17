# MyXodim Sanity E2E

UI-only daily sanity suite for **MyXodim** (Playwright + pytest, Page Object Model),
targeting the **staging** environment.

## What it checks

- **Smoke** — all three UIs load; admin logs in (phone+password) → `/dashboard`;
  client logs in (phone+OTP) → `/home`.
- **Happy-path** — client creates a document from a template and saves it as a draft.

## Setup

```bash
python3.13 -m venv .venv
.venv/bin/pip install -e .          # installs deps from pyproject.toml
.venv/bin/python -m playwright install chromium
cp .env.example .env                # adjust if needed (defaults = staging)
```

## Run

```bash
.venv/bin/python -m pytest -m sanity         # daily set
scripts/run_sanity.sh                         # daily entrypoint (Allure + JUnit + log)
allure serve allure-results                   # view report (needs `allure` CLI)
```

Headed/debug:

```bash
.venv/bin/python -m pytest -m sanity --headed --slowmo 300
```

## Daily run + Allure TestOps

Run each morning manually; `run_sanity.sh` uploads results to Allure TestOps
when creds are set in `.env`:

```bash
# .env
ALLURE_ENDPOINT=https://<your-testops-host>
ALLURE_TOKEN=<api-token>
ALLURE_PROJECT_ID=<project-id>
ALLURE_LAUNCH_NAME=MyXodim sanity (staging)
```

```bash
scripts/run_sanity.sh          # runs sanity, then uploads via bin/allurectl
```

If creds are empty, upload is skipped and results stay local in `allure-results/`.
`bin/allurectl` (v2.18) is already installed (gitignored).

## Layout

See `CLAUDE.md` for the full reference (URLs, accounts, verified locators, rules).
Product source is cloned read-only under `_core_src/` (gitignored). The previous
BusinessHub suite is archived under `archive/legacy-2026-06/`.
