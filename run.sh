#!/usr/bin/env bash
# One command to run Detour:   ./run.sh
# Offline stand-in:            DETOUR_MOCK=1 ./run.sh
# Venue backup (recorded run): DETOUR_REPLAY=1 ./run.sh
# Record a live run for backup: DETOUR_RECORD=1 ./run.sh
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null; then
  echo "Python 3 is not installed. Install it from https://www.python.org/downloads/ and run this again."; exit 1
fi
if [ ! -d .venv ]; then
  echo "First run: setting up (about a minute)..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
[ -f .env ] || { cp .env.example .env; echo "Made a .env file. Add your NVIDIA_API_KEY to it for live mode."; }

PORT="${PORT:-8000}"
( sleep 2; (open "http://localhost:$PORT" 2>/dev/null || xdg-open "http://localhost:$PORT" 2>/dev/null || true) ) &
echo "Detour is starting at http://localhost:$PORT  (press Ctrl+C to stop)"
exec python -m uvicorn server:app --host 127.0.0.1 --port "$PORT"
