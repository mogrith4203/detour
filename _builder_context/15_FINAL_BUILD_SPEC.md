# 15 · FINAL BUILD SPEC: the single source of truth (locked 6:40 AM CT, Nov 8)

Mog approved **Identity Echo** as the core technology. This file decides scope, order and cut lines. Where it disagrees with 08, 12 or 13, **this file wins**. Files 14 (Echo), 13 (stones) and 12 (fusion) give the detail behind each item.

## The product in one paragraph

**Detour. "Every scam pretends to be someone. We ask that someone."**

When a message claims to be someone, Nemotron extracts *who* it claims to be. The phone resolves that claim against the customer's own contacts or a verified business registry. T-Mobile then asks the **real** person or business, over a channel the scammer can't touch ("Is this you?"). A real line is only trusted if it shows no SIM swap or call forwarding.

What happens next:
- **"Not me"** is a ground-truth scam label. The scammer is diverted to a Nemotron decoy, which stalls him, extracts his cash-out account and hands him a canary card. The verified label teaches every phone a few-KB on-device skill. PNC tripwires the cash-out account and cancels the pending payment. The customer sees the truth in seconds.
- **"Yes, it's me"** shows "✓ Confirmed".
- **No answer** falls back to the safe-word prompt, a cooling-off hold, and the on-device story check.

Two independent signals are needed before any money is held, and everything is consented, content-free between companies, and labeled where simulated.

## What's IN (build order). Each item is done only when its tests pass and the Playwright flow passes

| # | Item | Built on | Time box |
|---|---|---|---|
| 0 | **P0 live check:** give Mog ONE copy-paste block (see "Mog's commands"). Build in parallel while he runs it. | 07, 08 P0 | first 10 min |
| 1 | **Echo core** (E1–E2 in 08): claim extraction (Nemotron JSON + lexicon mock), phone-side contact resolver (new JS function + parity test), echo service (start/inbox/answer/status/provenance), trust check, rate limits, no-answer fallback. | 14 | 45 min |
| 2 | **Echo outcomes** (E3): on denial, ground-truth label to the forge, thread divert to the decoy (in-context continuation), cash-out rails to tripwires, cancel the linked PNC payment. On "yes", a confirmed badge. | 14, existing engine | 30 min |
| 3 | **Echo UI** (E4): Jake's mini phone, Echo chips on Linda's cards, Echo nodes on the agent graph (Claim extractor → Echo → Ground-truth label → Forge). | 14 | 30 min |
| 4 | **Time:** PNC payment hold state machine with countdown, auto what-if (Low Cash Mode wording), coach explanation, Trusted Contact button, release paths. A pending "family emergency" payment waits on the Echo. Decoy stall tactics plus a "scammer time burned" counter. | 13 Time, 12 M3 | 30 min |
| 5 | **Reality:** cash-out tripwire extraction (regex-derived), `POST /api/pnc/pay` with a rules decision, canary minting plus `POST /api/pnc/card_auth` (fires with attribution, payout becomes a tripwire), k-anonymity range lookup with "PNC sent 5 chars" shown. | 13 Reality, 12 M1 | 40 min |
| 6 | **Space:** simulated CAMARA-style toggles (SIM swapped, call forwarding on, on a call with an unknown number), the Echo trust check uses them, content-free risk token shown as JSON. | 13 Space, 12 M2 | 20 min |
| 7 | **Gauntlet rule + panel:** a single signal can only warn; a HOLD needs 2 independent signals (Echo denial counts as one, with the strongest weight). A reasons panel shows which signals fired. A coverage-matrix panel (static, from 13). | 13 | 20 min |
| 8 | **Polish and red team:** `impeccable` critique → polish (Operate mode), `break-ui` on every panel, `santa-method` dual review (judge + hacker), `click-path-audit` of the full demo, 0 console errors at 1440×900 and 1280×800. | adopted_skills | 30 min |

**Cut lines.** If behind schedule at 8:45, stop adding features and go to item 8. Cut in this order (cut first means least important):
1. coverage-matrix panel
2. k-anonymity display
3. tarpit counter
4. canary
5. Space toggles. Keep one: SIM swap.

**Never cut:** Echo core, outcomes and UI; the Time hold; tripwires; the honesty badges; tests.

**OUT for today** (mention as "next" only): Soul signed messages, campaign graph, STIX export, embeddings/rerank, OCR screenshots, model routing, SQLite persistence, Callback Protection / Safe Browsing / 7726. Exception: if everything above is done and green before 9:15, add **model routing** (small) and the **content-safety guard** on decoy output (NVIDIA points), in that order.

## The demo flow that must work end to end (in LIVE, REPLAY and MOCK modes)

1. **Reset** → **Load decoy history**: stories exist, decoys are seeded (Power + Mind, already built).
2. **Echo, scam path.**
   - The scammer (a judge in "You be the scammer", or a sample button) texts Linda: "grandma it's jake, i got arrested, need $3000 for bail, dont tell mom".
   - Linda's phone shows **Claimed: Jake (grandson) → checking with the real Jake…**
   - Jake's phone panel shows the Echo prompt, and the judge taps **Not me**.
   - Linda sees "The real Jake says this isn't him."
   - The agent graph lights up: claim extraction → Echo → ground-truth label → forge → gate → skill promoted.
   - The thread is diverted to the decoy. The scammer's next message gets a decoy reply (stall); the decoy hands over a canary card when asked for payment details.
3. **PNC.**
   - Linda's earlier pending $3,000 Zelle to the scammer's handle is **cancelled automatically** (Echo denial + tripwire = 2 signals).
   - The coach explains in plain words. The Low Cash Mode what-if is shown.
4. **Canary.** "Simulate scammer cashes out the decoy's card" → the canary fires → the payout account is tripwired → "PNC sent 5 chars" (k-anonymity).
5. **Space.** Toggle "Jake's line: SIM swapped 1h ago" and repeat step 2: the Echo answer is marked **untrusted**, so the hold stays and the reasons panel shows why.
6. **Echo, legit path.** A message from Jake's real number (or "Yes, it's me") shows **✓ Confirmed by Jake**, and the payment is released.
7. **Business Echo.** A "Lakeview fraud dept" text → provenance check with hash only → "Lakeview says they didn't send this". The real Lakeview alert → "Lakeview confirms".
8. NVIDIA lens: every agent and tool call is visible with mode and latency. The scoreboard shows LIVE numbers only.

Steps 2, 3 and 6 are the critical path. They must work flawlessly in all three modes, with zero console errors.

## Mog's commands (give him exactly this block, early; he runs it in Terminal in the Detour folder)

The builder writes `live_check.sh` that does all of this with plain PASS/FAIL output, so Mog only runs:

```bash
cd ~/Documents/Archives/AI\ Work/Claude/hackutd-research/Detour && ./live_check.sh
```

`live_check.sh` must:
1. create or activate `.venv` and install requirements
2. run `check_nemotron.py`, which must also test the claim-extraction prompt; on a model-id failure, print the valid ids and the exact line to paste into `.env`
3. run `datagen.py` (skip if `data/generated.jsonl` exists)
4. run `bench.py` and save live results
5. print "NEXT: run ./run.sh with DETOUR_RECORD=1 and click the demo once" plus the click list

Later, after the features are done, give Mog one more line: `DETOUR_RECORD=1 ./run.sh` with the exact click path above. That records the venue backup. Then tell him it's ready for the video.

## Definition of done (what the builder reports to Mog at the end, by 9:45)

- [ ] `pytest` green, including parity (old + new resolver) and all Echo, hold, tripwire and canary tests.
- [ ] Playwright runs the full demo flow above in MOCK mode with 0 console errors, and saves screenshots of each step to `results/flow/`.
- [ ] Mog confirmed `./live_check.sh` PASS, and a live run was recorded to `replays/`. If it isn't possible, the demo runs in clearly labeled MOCK/REPLAY.
- [ ] README updated with the run commands and a "what's real vs simulated" section. Facts only; the team writes the intro themselves.
- [ ] Pushed to GitHub `main` and synced to Mog's Mac folder.
- [ ] A **DEMO_SCRIPT.md** for the video: the click path, what to say at each step (short, in plain words, for Mog and Ayush to read in their own voice), and the timing (≤ 2:00). The team records and voices it themselves; no AI voice.

## Non-negotiables (repeat of the hard rules)

- **Key:** only in `.env`; never printed or committed.
- **Badges and numbers:** never claim live for mock or replay; never quote unmeasured numbers.
- **Matcher:** frozen thresholds; no test-set phrases; no build step or CDN; matcher parity stays at 0 differences.
- **Echo privacy:**
  - Echo payloads never contain message content. A test asserts this.
  - Contacts never leave the browser.
  - Businesses see only hashes.
- **Echo safety:**
  - Echo fires only for consented customers, and only on messages with a money or risky ask.
  - Echo is rate-limited.
  - "No answer" is never treated as safe.
- **Simulated parts are labeled in the UI:** Echo delivery, carrier signals, PNC rails, canary cards, business endpoints.
