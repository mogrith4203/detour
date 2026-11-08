# 07 · Runbook and environment

## Where things live

- **Mog's Mac:** the project is at `~/Documents/Archives/AI Work/Claude/hackutd-research/Detour/`, with this folder inside it as `_builder_context/`. The folder is a plain copy of the repo (no `.git`) plus `.env`, which holds the key and must never be committed.
  - `_to_delete/` in that folder is a leftover broken `.git`; Mog can delete it.
- **GitHub:** `mogrith4203/detour`, `main` (source of truth). HEAD when this was written: `7add468` + the README/bench changes. Run `git log` for the current state.
- **Cloud workspaces** (if the builder runs in one) **cannot reach NVIDIA**. The proxy returns 403, and the Mac VM shell returns HTTP 000. **Only Mog's own Terminal reaches `integrate.api.nvidia.com`.** Design every live step as a copy-paste command for Mog.

## Env vars (`.env`, see `.env.example`)

| Var | Meaning |
|---|---|
| `NVIDIA_API_KEY` | the key (only in `.env` on the Mac) |
| `NEMOTRON_MODEL` | model id. Default `nvidia/nemotron-3.5-lightning` is UNVERIFIED; `check_nemotron.py` lists the valid ids on a 404 |
| `NEMOTRON_BASE_URL` | default `https://integrate.api.nvidia.com/v1` (OpenRouter is supported via `OPENROUTER_API_KEY`) |
| `NEMOTRON_THINKING` | `off` (default) sends `enable_thinking: False` |
| `DETOUR_MOCK=1` | deterministic stand-ins, red MOCK badge |
| `DETOUR_RECORD=1` | live, and saves responses to `replays/` |
| `DETOUR_REPLAY=1` | serves `replays/`, amber REPLAY badge |
| `DEMO_TOKEN` | if set, admin calls need `x-detour-admin: <token>` (open the UI with `?token=`) |
| `HOST`, `PORT` | default 127.0.0.1:8000 |

## Commands (Mog's Mac Terminal)

```bash
cd ~/Documents/Archives/AI\ Work/Claude/hackutd-research/Detour
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt   # once
python3 check_nemotron.py          # expect 3× [PASS]: Chat, JSON output, Tool calling
DETOUR_RECORD=1 ./run.sh           # live + record; click the exact demo path once; Ctrl+C
python3 datagen.py                 # writes data/generated.jsonl (frozen test split)
python3 bench.py                   # prints the scoreboard; saves results/benchmark.json
./run.sh                           # normal live run, opens http://localhost:8000
DETOUR_REPLAY=1 ./run.sh           # venue backup
DETOUR_MOCK=1 ./run.sh             # offline stand-in
```

## Tests (run after every change)

```bash
python3 -m pytest -q tests                   # 11 tests: finance (7) + JS↔Python parity (needs node; skipped if missing)
DETOUR_MOCK=1 python3 bench.py               # must finish; mock numbers are not quotable
```

Smoke test (mock mode, no network needed). Put this in a scratch file and run it with `PYTHONPATH=. python3 smoke.py`:

```python
import os, json; os.environ["DETOUR_MOCK"]="1"
from fastapi.testclient import TestClient
import server
c=TestClient(server.app); A={"x-detour-admin":"1"}
assert c.post("/api/seed",headers=A).status_code==200
assert c.get("/api/honeypot",params={"scenario":"toll","decoy":"decoy-02"}).text.count("data:")>5
s=c.post("/api/live/start",json={"decoy":"decoy-01"}).json()["session"]
c.post("/api/live/say",json={"session":s,"text":"Grandma its me, need bail in gift cards, dont tell mom"})
assert c.post("/api/live/end",json={"session":s}).status_code==200
r=c.post("/api/consent",json={"text":"Nana it's me, can you send money through Western Union tonight?","sender":"(682) 555-0120","local":{"score":0.4,"asks":["payment request"]}}).json()
print(r["card"]["level"])
assert c.post("/api/benchmark",headers=A).status_code==200
assert c.post("/api/finance/whatif",json={"scenario":[{"type":"payment","amount":3000,"from":"checking","date":"2026-11-09"}]}).status_code==200
print(c.post("/api/coach",json={"question":"Can I afford to pay $3,000 bail for my grandson tomorrow?"}).json()["answer"][:200])
```

UI check: Playwright is usually preinstalled in Claude cloud sandboxes (`chromium.launch()` needs no options). Start `DETOUR_MOCK=1 python3 -m uvicorn server:app --port 8020`, click through all three lenses, check the console for errors, and screenshot at 1440×900.

## Keeping GitHub and the Mac folder in sync

- **In a cloud sandbox:** clone `https://github.com/mogrith4203/detour`, work, commit, push.
- **Mac folder:** git can't run in it, because the sandbox can't delete lock files there without permission. To update it from the device shell, clone into `$HOME` and then copy each tracked file into place with `cp`, file by file. `tar` and `rm` fail there. This preserves `.env`:

```bash
cd $HOME/detour-src && git pull -q && for f in $(git ls-files); do mkdir -p "$HOME/mnt/Detour/$(dirname $f)"; cp "$f" "$HOME/mnt/Detour/$f"; done
```

- If Mog grants delete permission for the folder, a real git checkout becomes possible.

## Known gotchas

- The NVIDIA model id is unverified. Run `check_nemotron.py` first.
- If tool calling fails on the endpoint, the rescue agent and coach drop to their labeled fallbacks. A future fix is JSON-ReAct (the model returns `{"tool":..,"args":..}`).
- Replay only covers the exact requests that were recorded. Any new text typed during the demo falls back to the labeled mock, so record the scripted path.
- The live "You be the scammer" session can't be replayed, because the text is new each time. On bad Wi-Fi, skip it or use a phone hotspot.
- `results/` is gitignored. The scoreboard shows `/api/benchmark/last`, so run the benchmark live before judging.
