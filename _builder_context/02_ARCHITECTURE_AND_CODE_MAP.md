# 02 · Architecture and code map

Every function name with its docstring is listed in `snapshots/code_map_autogen.md`, and `snapshots/file_tree_with_line_counts.txt` has the files with line counts. This file explains how the pieces fit.

## Stack

- **Backend:** Python 3.10+, FastAPI and uvicorn, plus `openai` (used only as an OpenAI-compatible client) and `python-dotenv`. There's no database: all state is in memory per server process, and Reset clears it.
- **Frontend:** a single page (`static/index.html`) in vanilla HTML/CSS/JS, with no build step, no CDN and system fonts, so it works offline at the venue. `static/matcher.js` is the phone matcher. `static/legacy.html` is the old v1 dashboard, kept only for reference.
- **LLM:** NVIDIA Nemotron through `https://integrate.api.nvidia.com/v1` (OpenAI-compatible). The model id comes from `NEMOTRON_MODEL` in `.env`.
  - The default `nvidia/nemotron-3.5-lightning` is **unverified**.
  - Thinking is turned off with `extra_body={"chat_template_kwargs":{"enable_thinking":False}}`; if the endpoint rejects that, the client retries once without it.
  - `strip_think()` removes `<think>` blocks.

## Data flow

```
Scammer (scripted SCENARIOS, or a judge typing in "You be the scammer")
   │  SSE /api/honeypot  or  /api/live/start|say|end
   ▼
Decoy persona (Nemotron)  → persona reply filter (never admits it's an AI or a decoy; ≤ turn cap)
   ▼
Intel extractor (Nemotron, JSON) → sanitized; phone numbers and domains RE-DERIVED by regex from raw text
   ▼
Validator (rules only): injection scan · allowlist · A2P sender check · attestation (callback numbers only) · corroboration
   │   quarantines tainted sessions; the model never writes to the story map directly
   ▼
StoryMap  (stories S01…; status watch|warn; skill {keywords{word:weight}, phrases[], version}; numbers/domains with status)
   │  GET /api/phone/rules  (server → phone; skills + rule regex sources + allowlist + known-good hashes)
   ▼
PHONE (browser, static/matcher.js): normalize → risky_asks → skill_score → match → card
   │  POST /api/phone/verdict {decision, story_id, score}  ← no text, ever
   │  if unsure → consent sheet shows the exact redacted text + sender + byte count
   │  POST /api/consent {text: redacted, sender, local:{score, asks, ranked, fingerprint}}
   ▼
Rescue agent (Nemotron ReAct, ≤ 6 steps, read-only tools) → policy layer → verdict
   ▼ (scam)
Skill forge (Nemotron proposes ≤ 6 words, 2 phrases) → Gate (4 checks) → promote (version++, ≤ 3/hour/story) → phones resync
```

Every agent step calls `Engine.emit(agent, stage, **data)`. That feeds `/api/events?since=N`, which the NVIDIA lens polls every 700 ms to light up the agent graph. Benchmark runs use a separate `Engine()` instance, so they don't flood the feed or change live state.

## Matcher math (identical in `detour/core.py` and `static/matcher.js`, parity-tested)

- **Order of operations:** `normalize(text)` applies NFKC, a homoglyph map, the spaced-digit join ("9 7 2 5 5 5…") and lowercasing for tokens. Domains are punycode-decoded, and URL shorteners are flagged.
- **Risky asks** (`risky_asks`) flag any of these:
  - an unverified link
  - a shortener or punycode link
  - an unverified phone number together with a call verb, an urgency word or "verify/confirm/unlock/reactivate"
  - a payment ask (`PAYMENT_RE`): gift cards, crypto/bitcoin ATM, wire, Western Union/MoneyGram, "send cash/money", fee/fine/deposit/bail, a rail used as a request ("send it via Zelle", "Zelle me"), Spanish "enviar dinero" / "fianza"
  - secrecy ("don't tell", "keep it quiet/between us", "no le digas")
  - moving to another app
  - asking for credentials or codes
  - disguised text
- **Story score** (`skill_score`): `0.65 × keyword-match + 0.35` if there is a risky ask.
  - Keyword match is the sum of matched keyword weights / 3, capped at 1, plus phrase hits.
  - A small urgency bonus applies.
  - With no risky ask, the score is capped at 0.45.
  - A known scam number or link plus a risky ask scores 0.97 or more.
- **Money + pressure floor:** if the top score is below CLEAR, but the text has money words (`MONEY_RE`) plus authority (`AUTHORITY_RE`: irs/police/jail/bail/court/lawyer/…/abuela) or urgency, the score is raised to CLEAR (unsure). Pressure about money is never called "safe".
- **Decision:** `warn ≥ 0.60` (`MATCH`), `clear < 0.30` (`CLEAR`), otherwise **unsure**. These thresholds are FROZEN; don't tune them to the test set.
- **Card logic** (engine `check_message` = JS `checkOnPhone`), in order:
  1. A saved contact → clear.
  2. A known-good hash → clear.
  3. A warn from a registered A2P sender with no unverified link or number ask → downgraded to unsure.
  4. An unsure from a registered sender with no ask → clear ("Looks legitimate").
  5. A warn against a story still in `watch` → amber "Possible scam (still being confirmed)".
  6. Thread scoring: the last 3 messages from the same unknown sender are scored together (`THREAD_WINDOW = 3`).
- **Warning card text** never shows attacker-supplied numbers or links (`strip_indicators`). It uses the category label plus who the scam impersonates.

## Corroboration (core.py, StoryMap status refresh)

- **Formula:** `corroboration = distinct decoy lines + (1 if any live sessions AND lines ≥ 1) + (min(1, reports//3) if lines ≥ 1)`.
- **Threshold:** WARN needs corroboration ≥ 2.
- **What that means:**
  - Judge-typed live sessions alone can never warn; two live sessions can't corroborate each other.
  - Reports alone can't warn.
  - `/api/report` is rate-limited to 1 per story per client IP per 10 minutes.

## Gate (core.py `gate()`): 4 regression checks

1. **Fixes the miss:** the triggering message now scores warn.
2. **No false alarms on known-good texts:** the training-split legit EVAL messages plus `BENIGN_SMS` (about 40 everyday texts in data.py).
3. **No numbers, sites, verified businesses or everyday words in the skill.** Everyday words come from `benign_words()`, built from BENIGN_SMS plus train legit.
4. **Poisoning probe stays clean.**

All 4 must pass to promote. Promotions are rate-limited to `PROMOTIONS_PER_HOUR = 3` per story. Initial story skills drop benign words too, so brand names like "lakeview" don't become scam signals.

## Rescue agent (core.py `Agents.rescue`)

- **Input:** the redacted text, the sender and the local analysis.
- **Tools (read-only):** `search_story_map`, `get_story`, `check_allowlist`, `check_sender_registration`, `check_attestation`, `submit_verdict{verdict, story_id, confidence, evidence[], customer_message}`.
- **Loop:** at most 6 steps. Bad tool arguments go back to the model as an error result.
- **Verdict sanitizing:** non-dict → `{}`; a verdict not in scam/legit/unsure → unsure; `story_id` must exist; `confidence` is parsed with `_num()`.
- **Policy layer** (engine `decide`):
  - No tool evidence → unsure.
  - "legit" on a message with risky asks → unsure.
  - A known-good fingerprint is stored only for messages with no risky asks and confidence ≥ 0.7.

## Agents: prompts and fallbacks

All in core.py `Agents`: `scammer_turn`, `persona_reply`, `extract`, `validate`, `rescue`, `forge`.

- Every agent has a deterministic `_mock_*` fallback. On any model error the mode becomes "fallback" (or "mock" when there is no key), and the UI labels it.
- Model output is always sanitized:
  - strings truncated
  - lists coerced
  - category must be one of `CATEGORY_STEPS`
- A garbage-model fuzz test passed with no crashes: a stub server returned broken JSON, wrong types, bad tool args and "I am an AI".

## Finance (detour/finance/)

- **Data:** `customer.json` holds Linda Park (synthetic), as of Nov 2026.
  - **Accounts:** checking $2,840 (Zelle limit $2,500/day, wire limit $10,000/day), savings $9,600, CD $15,000, IRA $142,000, credit card balance $1,650 on an $8,000 limit, mortgage $96,000 with a $1,180 autopay on the 1st.
  - **Loans:** auto $8,200 at $412/month on the 12th; personal $3,100 at $185/month on the 22nd.
  - **Income:** pension **$2,050** on the 1st (raised from $1,050 so the baseline isn't already overdrawn), Social Security $2,150 on the 3rd.
  - **Spending:** bills of utilities $210 and phone $85 on the 15th, insurance $145 on the 20th; essentials $1,600 a month.
- **`engine.py`** (deterministic):
  - `load_customer`, `snapshot`, `forecast(c, days=60, events=None)`.
  - `indicators`, returning 4 values: liquidity_runway, obligation_coverage, debt_credit_health, scam_exposure.
  - `whatif(c, scenario)`, with event types `payment`, `extra_loan_payment`, `lock_savings` and CD break. Check `engine.py` for the exact supported types and fields.
  - Scam Exposure direction is forced to "same" when a scenario contains a payment, because the money already left; it is not an improvement.
- **`coach.py`** (Nemotron tool loop):
  - Tools: get_snapshot, get_indicators, run_forecast, run_whatif.
  - Every $ or % figure in the answer must exist in the tool results, **sign included**; otherwise the coach regenerates once, then falls back to a template.
  - For scam-flavored questions (bail, grandson, wire, gift card, Zelle, bitcoin, Western Union), code appends the overdraft fact and `SCAM_WARNING`, so safety doesn't depend on the model.
  - The keyword fallback router uses word boundaries and clamps amounts at $1M or less. "Afford" with no amount asks "how much?"; only bail-type questions default to $3,000.

## Record / replay (detour/llm.py)

- `DETOUR_RECORD=1` saves every live response to `replays/<sha256(model, messages, tools)[:24]>.json`.
- `DETOUR_REPLAY=1` serves those recordings, and the UI badge shows REPLAY · recorded run.
- A request with no recording raises an error, and the agent falls back to its labeled mock. So replay only covers the exact click path that was recorded: script the demo, then record that exact path.

## Security posture

- Admin routes (`/api/reset`, `/api/seed`, `/api/approve`, `/api/benchmark`):
  - need the header `x-detour-admin` (value `1` from localhost, or `DEMO_TOKEN` if that is set)
  - reject a foreign `Origin`
  - Because it's a custom header, a cross-site request triggers a CORS preflight, which the server never allows. That blocks CSRF.
- The server binds `127.0.0.1` by default (`run.sh`).
- All model and user text is escaped in the UI. XSS attempts were tested and render as text.
- In-memory dicts (live sessions, threads, pending checks) are capped.
- The finance what-if validates input (finite amount, 0 to 1e7, object events) and returns 400 on bad input, never a bare 500.
