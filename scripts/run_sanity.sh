#!/usr/bin/env bash
# Daily MyXodim sanity run. Produces Allure results + JUnit xml, optionally
# uploads to Allure TestOps, exits non-zero on failure.
#
# Usage:  scripts/run_sanity.sh [extra pytest args...]
set -uo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
RESULTS="allure-results"
mkdir -p logs test-results "$RESULTS"

# Export only ALLURE_* creds from .env (safe: no file execution, tolerates
# spaces/parens in values). Python reads the rest of .env via pydantic.
if [[ -f .env ]]; then
  while IFS='=' read -r k v; do
    [[ "$k" == ALLURE_* ]] && export "$k=$v"
  done < <(grep -E '^ALLURE_[A-Z_]+=' .env)
fi

PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "ERROR: venv not found at $PY" >&2
  exit 2
fi

# Fresh results each run (TestOps launch should reflect this run only).
rm -rf "$RESULTS"; mkdir -p "$RESULTS"

echo "[$STAMP] MyXodim sanity starting against staging…"
"$PY" -m pytest -m sanity \
  --reruns 1 --reruns-delay 5 \
  --alluredir="$RESULTS" \
  --junitxml="test-results/junit-$STAMP.xml" \
  "$@"
CODE=$?
echo "[$STAMP] pytest exit code $CODE"

# --- Upload to Allure TestOps (only if configured) ---
ALLURECTL="$ROOT/bin/allurectl"
if [[ -x "$ALLURECTL" && -n "${ALLURE_ENDPOINT:-}" && -n "${ALLURE_TOKEN:-}" && -n "${ALLURE_PROJECT_ID:-}" ]]; then
  echo "[$STAMP] uploading results to Allure TestOps…"
  "$ALLURECTL" upload \
    --endpoint "$ALLURE_ENDPOINT" \
    --token "$ALLURE_TOKEN" \
    --project-id "$ALLURE_PROJECT_ID" \
    --launch-name "${ALLURE_LAUNCH_NAME:-MyXodim sanity} $STAMP" \
    "$RESULTS" || echo "[$STAMP] WARN: TestOps upload failed"
else
  echo "[$STAMP] TestOps upload skipped (set ALLURE_ENDPOINT/TOKEN/PROJECT_ID in .env to enable)."
fi

# --- Build the XLSX report locally (does NOT send to Telegram). ---
# The daily Telegram report is a curated, once-a-day deliverable (director is in
# the chat), so sending is a deliberate manual step AFTER triaging failures —
# never automatic on every run. Review the file, confirm the failures are real
# product bugs (fix any test-side breakage and re-run first), then send with:
#     .venv/bin/python scripts/report_telegram.py
echo "[$STAMP] building XLSX report (local only, not sending)…"
"$PY" scripts/report_telegram.py --results "$RESULTS" --no-send \
  || echo "[$STAMP] WARN: report build step failed"

echo "[$STAMP] done (exit $CODE). To send the report to Telegram once it is"
echo "[$STAMP] reviewed:  .venv/bin/python scripts/report_telegram.py"
exit $CODE
