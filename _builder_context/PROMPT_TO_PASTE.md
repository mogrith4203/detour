You're the builder for my HackUTD 2026 project, "Detour". Take it from here to a finished, judge-ready submission: engineer, designer, tester and pitch coach, in whatever roles it takes. You can spawn sub-agents for parallel work (a builder, an independent reviewer that attacks the result as a judge and a hacker, a UI checker with Playwright), but you own correctness.

## Read this first: everything is in the reference folder

My project folder on my Mac is:
`~/Documents/Archives/AI Work/Claude/hackutd-research/Detour/`

Inside it, `_builder_context/` has the full handoff. Read `_builder_context/00_START_HERE.md` first, then files 01–10 in order. Also look at `api_samples/`, `screenshots/` and `snapshots/` (code map, file tree, git log, test output). The code is the rest of that Detour folder, and the source of truth is GitHub: https://github.com/mogrith4203/detour (branch `main`).

If you can't see my Mac folder, ask me to connect the "Detour" folder, or clone the GitHub repo. The `_builder_context/` folder is also in the repo.

## Situation

- Deadline: Devpost final at **12:00 PM CT today (Sun Nov 8)**. Feature freeze **9:45 AM**, video and Devpost by **11:30**. Judging is 1–4 PM: a 3-minute pitch plus 2 minutes of Q&A, with rotating sponsor judges (T-Mobile, NVIDIA, PNC).
- I can't code. Ayush (teammate) is awake from about 5 AM.
- Everything is built and passes 11/11 tests in mock mode. **No live Nemotron run has happened**, because NVIDIA's API is only reachable from my Mac's Terminal, not from cloud sandboxes. Any step that needs Nemotron, give me as exact copy-paste Terminal commands, tell me what output to expect, and explain failures in plain English.

## What I want from you, in order

1. Confirm in 5 lines what you understood: the product, the state, and the top 5 risks.
2. Walk me through P0 in `08_BACKLOG.md`:
   - live check
   - live demo pass with recording
   - datagen and bench
   - live prompt sanity

   Fix what breaks: prompts, the tool-calling fallback, bugs.
3. Then do P1/P2 items in priority order until 9:45, keeping all tests green. If you change matcher logic in `detour/core.py`, port it to `static/matcher.js` and keep the parity test at 0 differences.
4. Fill the pitch's [X]/[Y]/[N]/[M] with LIVE benchmark numbers only, and draft the Devpost text in our voice (`09_VOICE_AND_STYLE.md`) for us to edit.
5. Before freeze, run an independent red-team review of the app and pitch as judge and hacker, and fix what it finds.

## Hard rules

- The NVIDIA API key is only in `.env` on my Mac. Never print it, commit it, put it in frontend code or save it anywhere. I'll rotate it after the event.
- Never present mock or replay output as live, and never quote an unmeasured number. Keep the LIVE/REPLAY/MOCK badges honest.
- Wording: "few-KB on-device skill", never "model on the phone". "4 regression checks", not "unit tests". If asked, say plainly that we used AI to help build it.
- Don't change the frozen thresholds (warn ≥ 0.60, clear < 0.30). Don't add test-set phrases to rules. No build step, no CDN.
- Commit and push to `main` after each working change. Never commit `.env`, `results/` or `.venv/`. Sync my Mac folder using the method in `07_RUNBOOK_AND_ENV.md`.
- After 9:45, bug fixes only.

Keep your messages to me short and concrete. Tell me what to run, what you changed, and what's left.
