#!/usr/bin/env bash
# Detour live check. Run from the Detour folder:   ./live_check.sh
# Plain PASS/FAIL output. Never prints your API key.
cd "$(dirname "$0")"
set -o pipefail

pass() { echo "  [PASS] $1"; }
fail() { echo "  [FAIL] $1"; echo; echo "$2"; echo; echo "Copy everything above and send it to Claude."; exit 1; }

echo "== 1/5 Python setup =="
command -v python3 >/dev/null || fail "Python 3" "Python 3 is not installed. Get it from https://www.python.org/downloads/"
[ -d .venv ] || python3 -m venv .venv || fail "Create .venv" "Could not create the virtual environment."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt >/tmp/detour_pip.log 2>&1 || fail "Install requirements" "pip failed. Last lines:
$(tail -5 /tmp/detour_pip.log)"
pass "venv + requirements"

[ -f .env ] || { cp .env.example .env; fail ".env file" "There was no .env, so one was created. Open it, paste your key after NVIDIA_API_KEY=, save, and run this again."; }
grep -qE '^NVIDIA_API_KEY=.+|^OPENROUTER_API_KEY=.+' .env || fail ".env key" "Your .env has no key. Paste it after NVIDIA_API_KEY= and run again."
if grep -qE '^DETOUR_MOCK=1' .env; then fail ".env mode" "Your .env says DETOUR_MOCK=1. Change it to DETOUR_MOCK=0 and run again."; fi
if grep -qE '^DETOUR_REPLAY=1' .env; then fail ".env mode" "Your .env says DETOUR_REPLAY=1. Remove that line and run again."; fi
pass ".env has a key (not shown)"
# make sure a shell-level override doesn't force mock/replay
unset DETOUR_MOCK DETOUR_REPLAY DETOUR_RECORD

echo; echo "== 2/5 NVIDIA Nemotron (chat, JSON, tools, claim extraction) =="
python3 check_nemotron.py || fail "check_nemotron.py" "Nemotron check failed. The lines above say why (wrong model id, bad key, or no internet)."

echo; echo "== 3/5 Test set =="
if [ -s data/generated.jsonl ]; then
  pass "data/generated.jsonl already exists (skipped)"
else
  python3 datagen.py || fail "datagen.py" "Generating the test set failed. See the error above."
  pass "data/generated.jsonl written"
fi

echo; echo "== 4/5 Live benchmark (a few minutes) =="
python3 bench.py | tee /tmp/detour_bench.txt || fail "bench.py" "The benchmark crashed. See the error above."
grep -q "^Mode: live" /tmp/detour_bench.txt || fail "bench mode" "The benchmark did not run in LIVE mode, so its numbers can't be quoted."
if grep -q "^API errors:" /tmp/detour_bench.txt; then
  echo "  [WARN] Some API calls failed during the benchmark (see 'API errors' above). Numbers are saved but rerun if many failed."
fi
pass "results/benchmark.json saved (LIVE)"

cat <<'EOF'

== 5/5 ALL PASS ==
NEXT: run ./run.sh with DETOUR_RECORD=1 and click the demo once:

    DETOUR_RECORD=1 ./run.sh

Click list (in the browser that opens):
  1. Reset, then Load decoy history
  2. Send the sample "grandma it's jake..." text to Linda
  3. On Jake's phone, tap "Not me"; send one more scammer message; ask the decoy for payment
  4. Click "Simulate scammer cashes out the decoy's card"
  5. Toggle "Jake's line: SIM swapped" and repeat step 2
  6. Send the "Yes, it's me" path from Jake's real number
  7. Send the "Lakeview fraud dept" text, then the real Lakeview alert
  8. Open the NVIDIA lens; click Run benchmark
Then press Ctrl+C in Terminal. (Claude will send an updated click list once the new buttons ship.)
EOF
