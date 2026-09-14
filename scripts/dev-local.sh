#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export APP_MODE=local
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://127.0.0.1:8000}"
if [[ ! -d apps/web/node_modules ]]; then echo "apps/web/node_modules missing; run npm install in apps/web first" >&2; exit 2; fi
python -m uvicorn job_agent.api.app:app --host 127.0.0.1 --port 8000 & API_PID=$!
(cd apps/web && npm run dev -- --hostname 127.0.0.1 --port 3000) & WEB_PID=$!
echo "API PID: $API_PID | Web PID: $WEB_PID"
cleanup(){ kill "$WEB_PID" "$API_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
wait -n "$API_PID" "$WEB_PID"
