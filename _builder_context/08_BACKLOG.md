# 08 · Product backlog (product only; the video and Devpost come later, so don't work on them now)

Mog's direction at 6 AM: build the best end-to-end product to win T-Mobile, NVIDIA and PNC and HackUTD overall. It should be production-grade and work in real situations. Read `11_RESEARCH_AND_PRODUCT_STRATEGY.md` first.

Each item says who does it, what to do, and what "done" means. **Mog-run** means it needs Mog's Mac Terminal, because NVIDIA is unreachable from the cloud; give him exact commands. Keep all tests green after every item, and keep matcher changes ported to `static/matcher.js` with 0 parity differences.

## P0: make it real (live Nemotron)

1. **Verify the model ids live (Mog-run).**
   - Set `NEMOTRON_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b` (the code default now) and run `python3 check_nemotron.py`.
   - **Done when:** it shows 3× PASS.
   - If it fails, use an id that `check_nemotron.py` lists.
   - Also probe `nvidia/nemotron-3.5-bolt-e4b`, `nvidia/nemotron-3-embed-1b` (or 3.5) and `nvidia/nemotron-3.5-content-safety`. Extend `check_nemotron.py` to test embeddings and the safety model.
2. **Tool-calling fallback.** If native tool calls fail on any model, implement JSON-ReAct in `Agents.rescue` and `coach._live`: the model returns `{"tool":..,"args":..}` or `{"final":..}`. Keep the 6-step cap.
3. **Live prompt quality pass (Mog-run, builder tunes).**
   - With real outputs, make sure:
     - personas stay in character
     - extraction gives a sensible category and title
     - rescue calls tools before submitting a verdict
     - the forge proposes specific, non-generic words that pass the gate
     - the coach cites only tool numbers
   - Tune the prompts, not the thresholds.
4. **Live data and benchmark (Mog-run, plus Ayush's blind set).** Run `datagen.py`, then `bench.py`.
   - **Done when:** the result is `mode: live` with no crashes on odd rows.
5. **Record replays (Mog-run)** of the full demo path with `DETOUR_RECORD=1`, as the venue backup.

## P1: product depth that wins each sponsor (see 11 for why)

| # | Feature | Sponsor | Done when |
|---|---|---|---|
| N1 | **Semantic story memory with Nemotron embeddings.** Embed the story claim and asks. `search_story_map` uses cosine similarity, then the Nemotron reranker. Story merging uses embedding similarity. The phone still uses keyword skills; embeddings live server-side in rescue. Cache vectors. Mock mode: a deterministic hash-embedding stand-in, labeled. | NVIDIA | Rescue finds the right story for a reworded scam; the graph shows "embed" and "rerank" steps with model ids |
| N2 | **Model routing.** bolt-e4b for the persona and forge, lightning for extract, rescue and coach, optional ultra escalation when rescue confidence is under 0.5. Per-agent model id, latency and calls shown on the NVIDIA lens. | NVIDIA | The agent graph shows a different model per node; the counters work |
| N3 | **Nemotron content-safety guard.** Check decoy outputs before sending, and add a second opinion on inbound text for injection. Results show as a validator check. | NVIDIA, T-Mobile | A guard pass/fail chip appears in the validator; "Disregard everything above…" gets quarantined |
| N4 | **Screenshot check.** Upload or drag a screenshot of an iMessage/WhatsApp scam → Nemotron OCR/parse → text → the same phone matcher (on-device decision) → consent → rescue. Ship 2 sample screenshots (synthetic, generated as PNG). | T-Mobile, NVIDIA | Dropping a sample screenshot produces a warn/unsure card |
| T1 | **Callback Protection integration.** Corroborated callback numbers go onto a "Callback Protection list" after human review (approve button exists). On the phone, tapping a number in a scam message gives an audible-style warning screen: "T-Mobile Callback Protection: this number is linked to an active scam." | T-Mobile | The demo flow works; only approved numbers are listed; allowlisted businesses can never be listed |
| T2 | **Safe Web Browsing feed.** Scam domains from stories become a reviewed blocklist. A link tap on the phone shows a block interstitial. | T-Mobile | Same as T1 |
| T3 | **Report → 7726.** The Report button says it also forwards to 7726 (simulated, labeled). Reports feed corroboration under the existing caps. | T-Mobile | A toast confirms; the corroboration rules are unchanged |
| T4 | **Large-text / senior mode** on the phone panel, plus a "send a copy to a family member" option on warn cards (simulated). | T-Mobile | Toggle works; contrast passes |
| P1 | **PNC vocabulary.** A Money Bar strip (Free / Scheduled Out / Savings List), forecast labeled as a calendar, **Low Cash Mode + Extra Time** callout in what-ifs that overdraw ("triggers Low Cash Mode Nov 9; Extra Time (24h) wouldn't cover it, next deposit Dec 1"). | PNC | The bail what-if shows the Low Cash Mode callout with correct dates from the engine |
| P2 | **Lock actions.** A "Lock savings from instant transfers" button and a "Hold Zelle for 24h" button (simulated), which update Scam Exposure live. The coach's next steps link to them. | PNC | Clicking lowers exposure and the indicator updates |
| P3 | **Cross-sponsor alert.** When the phone warns on a payment-type scam, the PNC lens shows a banner: "An active scam targets customers like you. Your Scam Exposure is $X. Lock savings?" | All | Shows after the grandparent warn; one click runs the lock |
| X1 | **Persistence.** SQLite (standard-library `sqlite3`, in `data/detour.db`, gitignored) for stories, versioned skills, the audit log and the callback/web lists. It survives a restart; Reset clears it. | All | Restart keeps state; tests use a temp DB |
| X2 | **Audit log + skill rollback UI.** Every promotion, quarantine and approval is logged. On the story card, a "Roll back to v(n-1)" action re-syncs phones. | NVIDIA, T-Mobile | Rollback changes the phone verdict back; logged |
| X3 | **Observability.** Tokens or cost estimate and latency per agent on the NVIDIA lens; the hosted calls saved by teaching appear as a live counter. | NVIDIA | Numbers update during the demo flow |

## P2: hardening and polish

- **UI craft pass with `impeccable` (Mode: Operate).** Run `critique`, then `audit`, then `polish` / `harden` / `clarify` on `static/index.html`. Use `break-ui` worst-case data on every panel, and `emil-design-eng` for motion. Remove every sign of AI-made UI listed in `adopted_skills/ADOPTION.md`. Keep the dark console identity and the sponsor accents. Done when the critique has no high-severity items, break-ui shows no overflow or crash, and 0 console errors.
- **Security pass** with the Trail of Bits skills: `entry-point-analyzer`, then `agentic-actions-auditor` (rescue/coach tool loops), then `sharp-edges`. Add property-based tests for the matcher and redaction (`tob-property-based-testing`).

- `click-path-audit` and `browser-qa` on the full flow, every lens, at 1440×900 and 1280×800, with 0 console errors.
- `santa-method` dual review of the product claims shown in the UI (no overclaims).
- Load test: 20 concurrent phone verdicts plus 3 consents. No errors, and the event feed stays ordered.
- Story-label sanity: only show a story title when its category matches the message topic.
- Build skill v1 from Nemotron `signature_keywords` (filtered by benign words) rather than raw counts.

## LATER (not now; Mog's call)

The demo video, Devpost text, README voice rewrite and pitch rehearsal.

## Don't do

- Don't change the `MATCH`/`CLEAR` thresholds or add test-set phrases.
- The key goes only in `.env`.
- No build step or CDN.
- Never claim a model runs on the phone.
- Never fall back silently to mock.
- Don't break the parity test.
