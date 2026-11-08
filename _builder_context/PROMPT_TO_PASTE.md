You're the lead engineer, architect, designer and QA for my HackUTD 2026 project, "Detour". Your job is to take the entire technical burden off me and turn Detour into the best product at this hackathon: end to end, seamless, production-grade, working in real situations. We're going for the T-Mobile, NVIDIA and PNC sponsor tracks and HackUTD overall.

**Scope right now: the product only.** No demo video, no Devpost text, no pitch work. We'll do those later.

## Read everything first

My project folder on my Mac: `~/Documents/Archives/AI Work/Claude/hackutd-research/Detour/`. Source of truth: https://github.com/mogrith4203/detour (branch `main`). If you can't see the Mac folder, ask me to connect "Detour", or clone the repo.

The full handoff is in `_builder_context/`. Read it in this order:
1. `00_START_HERE.md`
2. **`12_REINVENTION_THE_WINNING_IDEA.md`: the strategy.** Detour is a carrier–bank scam fusion center fed by AI decoys. It stops a scam at the message (on-device skill), the moment (a content-free scam-in-progress risk token from T-Mobile to PNC, modeled on Australia's Telstra–CBA indicator and Telefónica's Scam Signal API) and the money (cash-out tripwires from decoy chats, plus a PNC payment hold with the Nemotron coach and a Trusted Contact). AI scam-baiting itself already exists (Apate.ai), so our edge is closing the loop across carrier and bank.
3. **`13_SIX_INFINITY_STONES.md`: six unrelated defenses, each owning one part of a scam, each with a failsafe, fused so no scammer gets around them.**
   - **Soul** (who is really talking): signed business messages verified on-device plus a family safe word.
   - **Mind** (what they say): on-device story skills. Built.
   - **Space** (how they reach you): content-free carrier signals (call in progress, SIM swap, call forwarding, campaign bursts), modeled on CAMARA, Telstra–CBA and Telefónica Scam Signal.
   - **Reality** (where the money goes): cash-out tripwires, canary tokens that expose mule accounts, k-anonymity payee lookups.
   - **Time** (when they must act): payment time-lock plus Trusted Contact, and decoys that tarpit scammers.
   - **Power** (who the attacker is): decoy personas. Built.

   Gauntlet rule: any single stone can only warn; holding money needs 2 independent stones.
4. `11_RESEARCH_AND_PRODUCT_STRATEGY.md` (what each sponsor actually ships and the Nemotron model family)
5. `08_BACKLOG.md` (your work list, with what "done" means)
6. Files 01–07, 09 and 10
7. `adopted_skills/ADOPTION.md`: 32 curated skills we pulled from X and GitHub.
   - Sources:
     - an Anthropic hackathon winner's setup (ECC)
     - obra/superpowers
     - Impeccable and Emil Kowalski's design skills (anti-AI-slop UI)
     - Anthropic's official skills
     - NVIDIA's official Nemotron skills
     - Trail of Bits security skills
   - **First action: install them into `.claude/skills/` with the command in ADOPTION.md** (taste-skill is reference-only, because it carries a hook).
   - Use them: superpowers for planning, parallel sub-agents, TDD, debugging and verification; impeccable/break-ui for the UI; the NVIDIA skills for the content-safety policy and embed/rerank; Trail of Bits for security.
8. `api_samples/`, `screenshots/`, `snapshots/`

## Situation

- It's ~6 AM CT, Sun Nov 8. Product feature freeze **9:45 AM**, final deadline noon, judging 1–4 PM.
- Everything currently built passes 11/11 tests in mock mode.
- **No live Nemotron run has happened yet**, because NVIDIA's API is reachable only from my Mac's Terminal, not from cloud sandboxes.
- I can't code. For anything that needs live Nemotron, give me exact copy-paste Terminal commands, tell me what output to expect, and explain failures in plain English.
- Ayush (teammate) is awake and can do non-code tasks: writing blind test messages, clicking through flows.

## How to work

1. Start with a 5-line summary: what you understood, and the top risks.
2. **P0 first** (live model verification, tool-calling fallback, live prompt quality, live data and bench, replays). These need me, so give me commands early, and build in parallel while I run them.
3. Then **P1-A2: the stones in order: S1 Time → S2 Reality → S3 Space → S4 Soul → S5 Gauntlet** (this includes M1–M3). This is what no other team will have. Then **P1-B** in the order you judge to win the most: semantic story memory with Nemotron embeddings and reranker, model routing, the Nemotron content-safety guard, screenshot checks with Nemotron OCR, T-Mobile Callback Protection / Safe Web Browsing / 7726 integration, PNC Money Bar / Low Cash Mode / lock actions, the cross-sponsor alert, SQLite persistence, audit log and skill rollback, observability.
4. Use sub-agents to work in parallel where the tasks don't overlap (git worktrees are fine). Run an independent reviewer (`santa-method`) that attacks every finished feature as a judge and as a hacker, and fix what it finds before moving on.
5. After every feature:
   - `pytest` passes, including the JS↔Python parity test
   - the mock smoke test passes
   - a Playwright click-through of all 3 lenses shows 0 console errors
   - commit and push to `main`
   - sync my Mac folder (method in `07_RUNBOOK_AND_ENV.md`)
6. Every new feature must have a labeled mock stand-in so the app never breaks offline, and must be honest in the UI about what's simulated.
7. If you find a better idea than the backlog, say so in one line and do it if it clearly wins more.

## Hard rules

- The NVIDIA API key lives only in `.env` on my Mac. Never print it, commit it, put it in frontend code or save it anywhere.
- Never present mock or replay as live. Keep the LIVE/REPLAY/MOCK badges honest, and never quote an unmeasured number.
- Don't change the frozen thresholds (warn ≥ 0.60, clear < 0.30). Don't add test-set phrases to rules. No build step, no CDN; vanilla JS stays.
- Matcher changes go in both `detour/core.py` and `static/matcher.js`, and parity stays at 0 differences.
- Never commit `.env`, `results/`, `.venv/` or the SQLite DB.
- After 9:45, bug fixes only.

Keep messages to me short: what to run, what you shipped, what's next.
