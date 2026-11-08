#!/usr/bin/env bash
# Double-click in Finder. Records the full demo path against LIVE Nemotron (saves replays/ for the venue backup),
# then replays it to prove the backup works. Log: results/record_demo.log
cd "$(dirname "$0")"
mkdir -p results
{
  set -o pipefail
  [ -d .venv ] || python3 -m venv .venv
  source .venv/bin/activate
  pip install -q -r requirements.txt playwright && python -m playwright install chromium >/dev/null 2>&1 || { echo "RECORD_FAILED: could not install Playwright"; exit 1; }
  echo "== RECORD (LIVE Nemotron) =="
  E2E_PORT=8041 E2E_MODE=record python tests/e2e_demo.py || { echo "RECORD_FAILED"; exit 1; }
  echo "Saved $(ls replays | wc -l | tr -d ' ') recorded responses in replays/"
  echo "== VERIFY REPLAY =="
  E2E_PORT=8042 E2E_MODE=replay python tests/e2e_demo.py || { echo "REPLAY_FAILED"; exit 1; }
  echo "RECORD_DEMO_FINISHED ok"
} 2>&1 | tee results/record_demo.log
