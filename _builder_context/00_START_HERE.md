# START HERE: Builder handoff for "Detour" (HackUTD 2026)

> **LOCKED 6:40 AM: `15_FINAL_BUILD_SPEC.md` is the single source of truth for scope and order. Core technology: Identity Echo (file 14).** Older sections below still describe the existing code accurately.

You are taking over a hackathon project that is about 85% built. Read this file fully, then the numbered files in order. Everything you need is in this folder or in the repo one level up.

## The situation in 60 seconds

- **Event:** HackUTD 2026 "ZeroDay", UT Dallas, Nov 7–8, 2026. It is the team's first hackathon.
- **Team:** Mog (Mogindran Baladhandayutham; Collin College student; can't code fluently, so he directs while AI builds) and Ayush Bose (teammate).
- **Hard deadline:** Devpost final submission at **12:00 PM CT, Sunday Nov 8, 2026**.
  - Internal feature freeze: **9:45 AM CT**.
  - Video and Devpost final: **11:30 AM CT**.
- **Judging:** in person, 1–4 PM. Each pitch is 3 minutes plus 2 minutes of Q&A. Sponsor judges rotate between tables.
- **Devpost draft:** https://devpost.com/software/detour-myou03
  - Tracks entered: T-Mobile, NVIDIA, Design, Beginner.
  - Add PNC: its lens shipped.
  - Video rule: "Demo Video (Skits are allowed, maximum of 2 minutes)".
- **Repo:**
  - GitHub: https://github.com/mogrith4203/detour (branch main).
  - Local copy: the folder that contains this `_builder_context/` folder.
  - The local copy has no `.git`; git can't write lock files in that synced folder without delete permission. Treat GitHub as the source of truth, and keep both in sync (see 07_RUNBOOK).
- **Product:** "Detour". Nemotron agents act as decoy personas, learn scam *stories* (plays) from attackers, and teach a few-KB on-device skill so phones catch the same play from a brand-new number.
  - It is one engine with three sponsor "lenses" (tabs, keys 1/2/3): T-Mobile, NVIDIA and PNC.
  - Everything is synthetic.

## What works right now (verified in mock mode)

Full backend, all three lenses, the browser-side phone matcher with Python parity tests (11/11 tests pass), the benchmark, record/replay, red-team fixes, a CSRF-safe admin, and the finance engine plus coach.

## What has NOT happened yet (most important gaps)

1. **No live Nemotron run yet.**
   - NVIDIA's API (`integrate.api.nvidia.com`) is blocked from the cloud sandbox and from the Mac VM shell. Only Mog's own Mac Terminal reaches it.
   - Until a live run happens:
     - Every number on the scoreboard is mock and must NOT be quoted.
     - The model id `nvidia/nemotron-3.5-lightning` in `.env` is unverified.
   - `check_nemotron.py` lists the valid Nemotron ids if the default is wrong.
2. `data/generated.jsonl` doesn't exist yet. Mog runs `python3 datagen.py` on his Mac, live.
3. `data/handwritten.jsonl` is still a template. Ayush writes 10 scam + 10 legit texts **before** looking at the matcher code.
4. No recorded replays yet (`DETOUR_RECORD=1 ./run.sh`) to use as the venue Wi-Fi backup.
5. (LATER, not now) Devpost text, the 2-minute video, and the README in the team's own words. Mog's direction at 6 AM: **product only for now.**
6. Remaining polish and backlog: see 08_BACKLOG.md, which is prioritized and has acceptance criteria.

## Non-negotiable rules

- **Secrets.**
  - The NVIDIA key lives ONLY in `.env` on Mog's Mac, which is gitignored.
  - Never print it, commit it, put it in frontend code, copy it into these docs, or save it to memory.
  - Mog will rotate it after the event.
- **Honesty.**
  - Never present mock or replay output as live Nemotron output. The UI badges (LIVE / REPLAY / MOCK) must stay accurate.
  - Never quote a number that wasn't measured live.
  - Words to use:
    - "few-KB on-device skill (weighted keywords + rule checks)", never "model on the phone".
    - "4 regression checks", not "unit tests".
  - Everything simulated is labeled as simulated.
- **Don't break the demo.**
  - After every change: `python3 -m pytest -q tests` (includes the JS↔Python parity test) and the mock smoke test in 07_RUNBOOK.
  - If you change matcher logic in `detour/core.py`, port the same change to `static/matcher.js` and keep parity at 0 differences.
- **After the 9:45 freeze:** bug fixes only.
- **Mog can't code.**
  - Anything he must run, give as exact copy-paste Terminal commands with the expected output.
  - Explain what failed in plain English.
- **Commit and push** to GitHub (`main`) after each working change. Commit message trailer if your harness asks for one. Never commit `.env`, `results/`, `.venv/`.

## Read order

| File | What it gives you |
|---|---|
| 15_FINAL_BUILD_SPEC.md | **READ FIRST.** Locked scope, order, time boxes, cut lines, the demo flow, Mog's one command, definition of done |
| 14_THE_NEW_TECHNOLOGY_IDENTITY_ECHO.md | **Read second. THE CORE INVENTION.** Identity Echo: every scam pretends to be someone, so we ask that someone, over a channel only the carrier controls. Ground-truth labels, zero-false-positive diversion, identity-confirmed payments |
| 12_REINVENTION_THE_WINNING_IDEA.md | **Read third.** Carrier–bank fusion: message, moment, money A carrier–bank scam fusion center fed by AI decoys: stop the scam at the message, the moment and the money |
| 13_SIX_INFINITY_STONES.md | **Read with 12.** Six real security techniques (deception, distillation, canary tokens, pivoting, tarpits, privacy-preserving sharing), with the build, demo moment and sponsor for each |
| 11_RESEARCH_AND_PRODUCT_STRATEGY.md | **Read third.** What T-Mobile and PNC actually ship, the Nemotron model family, and the product moves that win each track |
| 01_PRODUCT_AND_SPONSORS.md | The idea, the three sponsor briefs and what each judge scores |
| 02_ARCHITECTURE_AND_CODE_MAP.md | Every module, function, data shape and threshold |
| 03_API_REFERENCE.md | Every endpoint, with real sample responses in `api_samples/` |
| 04_DECISIONS_LOG.md | Why things are the way they are (don't re-litigate settled calls) |
| 05_REDTEAM_HISTORY.md | Every weakness found in 4 red-team passes and its status |
| 06_PITCH_DEMO_QA.md | The 3-minute script, the demo click path, judge Q&A |
| 07_RUNBOOK_AND_ENV.md | How to run, test, record, replay, sync, and the network constraints |
| 08_BACKLOG.md | What to build next, in priority order, with acceptance criteria |
| 09_VOICE_AND_STYLE.md | How the team writes and speaks, so copy doesn't read as AI boilerplate |
| 10_PEOPLE_TIMELINE_LOGISTICS.md | People, schedule, deliverables, Devpost checklist |
| api_samples/ | Real JSON responses captured from the running server (mock mode) |
| screenshots/ | UI screenshots of every lens at 1440×900 |
| snapshots/ | File tree with line counts, git log, pytest and bench output |
| adopted_skills/ | Curated skills from the Anthropic-hackathon winner's open-source Claude Code setup (ECC, MIT), plus what judges and winners on X say wins. Read `adopted_skills/ADOPTION.md`, which maps each skill to a Detour task (demo video, dual-review gate, click-path audit, verification loop) |

Also available: the living plan doc "Detour Build & Pitch Plan" at https://claude.ai/artifact/4HYugmaZU73oDKsj7EV3bU. It is a Claude Docs artifact on Mog's account; if you have the docs tools, read it there. It has the full v1→v2 design rationale, red-team passes 1–3 and the schedule. The essentials are copied into these files.
