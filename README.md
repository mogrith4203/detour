# Detour

HackUTD 2026: ZeroDay · T-Mobile · NVIDIA · PNC

**Nemotron learns from attackers, then teaches a tiny on-device skill. Every lesson passes regression checks before it ships.**

Scammers swap phone numbers in hours, but they keep the same story. Detour runs Nemotron agents as decoy personas on decoy lines. They pull the *story* out of each scam conversation: who it pretends to be, what it claims, what it asks for, and how it wants to be paid. Rules the model can't overrule validate that story. It then becomes a few-KB skill that customer phones use to recognize the same play from a brand-new number.

> All data in this repo is synthetic: personas, customers, businesses, phone numbers (555-01xx) and websites (.example). No real customer data is used.

## How it works

```mermaid
flowchart LR
  A[Scammer<br/>scripted plays or a person typing] --> B[Decoy persona<br/>Nemotron]
  B --> C[Intel extractor<br/>Nemotron, JSON]
  C --> D[Validator<br/>rules]
  D --> E[(Story map)]
  E -- skills sync --> F[Phone matcher<br/>runs in the browser]
  F -- unsure + customer consents --> G[Rescue agent<br/>Nemotron + tools]
  G --> H[Skill forge<br/>Nemotron]
  H --> I[Gate<br/>4 regression checks]
  I -- promoted --> F
```

| Stage | What it does |
|---|---|
| Decoy persona | Replies in character as a synthetic decoy (e.g. "Linda Park, 71"). It never pays and never shares anything real. It ignores instructions inside scammer messages, and a filter stops it from revealing it's an AI. |
| Intel extractor | Turns the conversation into a structured story. Phone numbers and links are re-read from the raw text, so the model can't invent or drop them. |
| Validator | Rules the model can't overrule: a prompt-injection scan, a verified-business allowlist (poisoning defense), a sender-registration check (A2P short code / 10DLC, simulated), and corroboration. A story warns customers only after 2 independent decoy lines. A typed-in live session or customer reports can add at most one confirmation, and only to a play a decoy line has already seen. |
| Phone matcher | Runs in the browser (`static/matcher.js`), which stands in for the phone. It scores a message against each story's skill (weighted keywords and phrases) plus "risky asks": unverified links or callback numbers, payment rails, secrecy, moving to another app, disguised text. The result is warn, clear, or unsure. Only the verdict goes to the server for the dashboard counters; the message itself is never sent. |
| Rescue agent | Runs only for unsure messages, and only after the customer taps consent. The phone sends a redacted copy (card numbers, SSNs, codes, addresses, emails and the owner's name removed) plus the sender ID. Nemotron then works through a tool loop of at most 6 steps: `search_story_map`, `get_story`, `check_allowlist`, `check_sender_registration`, `check_attestation`, `submit_verdict`. A policy layer downgrades any verdict that has no tool evidence, and it never marks a message with a payment ask as safe. |
| Skill forge + gate | Nemotron proposes new words for the story's skill. The gate promotes them only if they fix the miss, cause no false alarms on known-good texts, contain no numbers, sites, verified businesses or everyday words, and pass a poisoning probe. A skill can be promoted at most 3 times an hour. |
| PNC navigator | Shows Linda's whole financial picture (synthetic): 4 indicators (Cash Runway, Bill Coverage, Debt & Credit, Scam Exposure), a 60-day forecast, and what-ifs, all computed by a deterministic engine. A Nemotron coach answers questions with tool calls. Every dollar figure it gives is checked against the tool results, sign included, and safety warnings are added by code, not left to the model. |

## Run it

```bash
./run.sh                       # sets up a venv, installs, opens http://localhost:8000
python3 check_nemotron.py      # PASS/FAIL for chat, JSON, tool calling and claim extraction with your key
./live_check.sh                # one-shot: venv, Nemotron check, test set, live benchmark
                               # (or double-click live_check.command / record_demo.command / start_live.command in Finder)
python3 -m pytest -q tests     # unit, Echo, and JS↔Python parity tests (mock, no network)
python3 tests/e2e_demo.py      # Playwright: full demo flow in MOCK, screenshots in results/flow/
```

`.env` holds `NVIDIA_API_KEY` and `NEMOTRON_MODEL`. Copy the exact model id from "View Code" on build.nvidia.com.

| Mode | How | Header shows |
|---|---|---|
| Live | key in `.env` | LIVE · model id |
| Record a live run | `DETOUR_RECORD=1 ./run.sh` | LIVE (and saves `replays/`) |
| Venue backup | `DETOUR_REPLAY=1 ./run.sh` | REPLAY · recorded run |
| Offline stand-in | `DETOUR_MOCK=1 ./run.sh` | MOCK · not Nemotron output |

Admin buttons (load decoy history, reset, run benchmark) work only from the demo laptop.

## Benchmark

`python3 bench.py` compares, on held-out messages:
- a number/link blocklist (today's approach)
- the phone matcher alone
- the phone matcher plus Nemotron rescue

It uses three sets: the built-in held-out split, `data/generated.jsonl` (written by Nemotron with `datagen.py`, test split frozen), and `data/handwritten.jsonl` (written by a teammate who never saw the matcher). A campaign replay then sends each test message to 5 customers to count how many hosted calls the teaching loop saves. Thresholds are frozen at warn ≥ 0.60 and clear < 0.30.

The blocklist row is low by construction, because the test messages use new numbers. The Nemotron-generated set has noisy labels: in its tune split (which we may read), several rows labeled "legit" ask for a fee or a deposit through a link, or come from a "grandchild" asking for cash. Detour's policy never marks those safe, so read false alarms on that set with that in mind. We didn't tune the matcher or thresholds to it. Only quote numbers from a live run; the UI blurs mock-mode results.

## Identity Echo

1. Nemotron reads the message and returns who it claims to be (`detour/claims.py`, JSON; a lexicon stand-in in MOCK).
2. The phone matches that claim to Linda's contacts or a verified business (`static/resolver.js`, parity-tested against `detour/resolver.py`). Contacts never leave the browser. Only a hash of the one resolved number goes out.
3. The carrier asks the real person on their own line: "Is this you?" The prompt carries no message content. An answer counts only if that line shows no SIM swap and no call forwarding.
4. For a business, the phone sends only a hash of the message. The business says whether it sent it.
5. "Not me" is a ground-truth scam label: the sender is tripwired, the thread goes to a decoy, the skill forge proposes an update that must pass the gate, and linked payments are cancelled.
6. No answer is never treated as safe: safe-word prompt, cooling-off hold, and the on-device story check keep running.

Model routing: the decoy persona runs on `nvidia/nemotron-3.5-bolt-e4b` (small, fast stalling). Claim extraction, rescue, forge and coach stay on `NEMOTRON_MODEL`, the model the benchmark measured. Model-written decoy replies are checked by `nvidia/llama-3.1-nemotron-safety-guard-8b-v3` before they're sent (the fixed canary line is not). An unsafe reply is swapped for a neutral stall line and tagged "filtered". A privacy-only flag is noted, not blocked, because the decoy's details are synthetic. If the guard can't be reached, the feed says "unchecked". On Nov 8 `probe_models.py` showed both ids answering with our key. Set `NEMOTRON_SMALL_MODEL=off` or `NEMOTRON_SAFETY_MODEL=off` to turn them off.

Money rule (`Defense.gauntlet` in `detour/echo.py`): one signal can only warn. A hold needs 2 independent signal families (message, bank, carrier, Echo). A cancel needs the Echo denial plus one more.

## What's real and what's simulated

- **Real:** the agent pipeline, Nemotron calls (with a key), tool calling, claim extraction, the validator rules, the in-browser matcher and claim resolver, the skill forge and gate, the hold/cancel rules, the finance engine, and the benchmark.
- **Simulated (labeled in the UI):** Echo delivery to the real person (Jake's phone is a browser panel), carrier signals (SIM swap, forwarding, active call; CAMARA-style), PNC payment rails, holds and tripwires, canary cards, business provenance endpoints, the scammer traffic, the decoy phone lines, sender registration, the verified-business list, the customer phone, and the bank customer.

## Layout

```
server.py              FastAPI app
detour/llm.py          Nemotron client (OpenAI-compatible; mock / record / replay)
detour/core.py         signals, matcher (reference copy), story map, agents, gate
detour/engine.py       orchestration, phone rules API, consent + rescue, benchmark
detour/claims.py       Echo claim extraction (Nemotron JSON + mock)
detour/resolver.py     claim → contact/business (Python twin of static/resolver.js)
detour/echo.py         Identity Echo, carrier signals, PNC rails, canary, k-anonymity, gauntlet
detour/finance/        PNC engine + coach
detour/data.py         synthetic personas, plays, allowlist, eval set
static/index.html      three-lens demo UI
static/matcher.js      the phone matcher (parity-tested against core.py)
static/resolver.js     the phone-side claim resolver (parity-tested against resolver.py)
bench.py · datagen.py · check_nemotron.py · run.sh
```

Team: Mogindran Baladhandayutham, Ayush Bose
