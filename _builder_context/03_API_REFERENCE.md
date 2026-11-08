# 03 · API reference (server.py)

These are real responses captured from the running server in **mock mode**, so model text in them comes from the deterministic stand-in. They are in `api_samples/*.json` (each file is `{status, body}`).

| Method | Path | Body / query | Returns | Notes |
|---|---|---|---|---|
| GET | `/` | – | `static/index.html` | |
| GET | `/api/state` | – | `{llm, stats, stories, log, personas, last_event, scenarios}` | The key is `log`, not `events`. |
| GET | `/api/events?since=N` | – | `{events:[{seq, t, agent, stage, input?, output?, tool?, ms?, mode?, …}], last, llm, stats}` | Polled every 700 ms by the UI. Events use the field `stage` (not `kind`). |
| GET | `/api/samples` | – | `PHONE_SAMPLES`: `[{label, sender, text}]` | 5 demo texts: bank (new number), toll (new domain), grandparent (Western Union, the unsure → teach demo), real bank alert from short code 33622, friend with a new number. |
| GET | `/api/honeypot?scenario=&decoy=` | scenario ∈ bank_alert, toll, parcel, carrier_bill, grandkid, job, poison; decoy ∈ decoy-01..03 | SSE stream of session events (scammer/decoy turns, extract, validate checks, outcome) | Paced 0.6 s per event in mock/replay mode. `poison` must end "Quarantined". |
| POST | `/api/live/start` | `{decoy}` | `{session, persona, …}` | "You be the scammer". |
| POST | `/api/live/say` | `{session, text}` | decoy reply + meta `{mode, ms, filtered}` | Turn cap applies. |
| POST | `/api/live/end` | `{session}` | extraction + validator checks + outcome | Live sessions count at most once toward corroboration, never alone. |
| POST | `/api/check` | `{text, sender, known}` | `{check_id, steps, card, cloud_bytes, state}` | **Server reference copy only.** The UI doesn't use it (the phone runs `matcher.js`). Used by tests and the benchmark. |
| GET | `/api/phone/rules` | – | `{stories[], known_good[], allowlist[], registered_senders{}, stop[], shorteners[], homoglyphs{}, thresholds, thread_window, category_steps, category_label, patterns{NAME: python_regex_source}, skill_bytes}` | Server → phone sync. |
| POST | `/api/phone/verdict` | `{decision, story_id, score}` | `{ok, stats}` | Phone → server. Verdict only, no text. |
| POST | `/api/consent` | `{text (already redacted on the phone), sender, local:{score, asks[], ranked[], fingerprint?}}`, or the legacy `{id: check_id}` | `{card, steps, sent_text, cloud_bytes, …}` | Runs rescue → policy → forge → gate. |
| POST | `/api/report` | `{story_id}` | story state | 429 if the same IP reported the same story within 10 minutes. |
| POST | `/api/approve` | `{story_id, number}` | – | ADMIN. Human review of a block-eligible number (simulated). |
| POST | `/api/seed` | – | – | ADMIN. Replays scripted decoy history so the story map has active plays. |
| POST | `/api/reset` | – | state | ADMIN. |
| POST | `/api/benchmark` | – | `{mode, model, rows[{set, mode, caught, scams, false_alarms, legit, unsure, hosted}], campaign[], api_calls, thresholds, ran_at}` | ADMIN. Runs on a separate Engine. 409 if one is already running. Writes `results/benchmark.json`. |
| GET | `/api/benchmark/last` | – | last saved result or `{}` | |
| GET | `/api/finance/overview` | – | `{snapshot, indicators[4], forecast}` | |
| POST | `/api/finance/whatif` | `{scenario:[event…]}` (≤ 10) | `{before, after, deltas[{id, direction}], facts[], after_forecast[{date, checking}]}` | 400 on bad input. |
| POST | `/api/coach` | `{question}` | `{answer, numbers_cited, next_steps, tool_trace[{tool, args, result_summary}], mode}` | |

**ADMIN** means the request needs the header `x-detour-admin: 1` from localhost, or the `DEMO_TOKEN` value when that env var is set. A foreign `Origin` gets 403. The UI reads `?token=` from the page URL when it's present.

## What-if event shapes (detour/finance/engine.py `_apply_events`)

- `{"type":"payment", "amount":3000, "from":"checking"|"savings", "date":"YYYY-MM-DD", "label":"bail"}`
- `{"type":"break_cd", "date":…}`: the penalty is computed, and the proceeds go to savings.
- `{"type":"extra_loan_payment", "loan":"<loan account id>", "amount":…, "from":"savings"|"checking", "date":…}`. Account ids are in `customer.json`.
- `{"type":"lock_savings", "amount":…}`: lowers Scam Exposure.
- An unknown type raises `ValueError`, which the server turns into a 400.

## UI presets (static/index.html)

- **Bail:** payment of $3,000 from checking on 2026-11-09.
- **"Pay it from savings instead."**
- **Car payoff:** extra_loan_payment of the full auto balance from savings.
- **Lock savings:** lock_savings of the full savings balance.
