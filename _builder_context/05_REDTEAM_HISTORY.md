# 05 · Red-team history (4 passes)

Passes 1–3 were design reviews in the plan doc. Pass 4 was an independent agent that attacked the running app as an NVIDIA judge, a T-Mobile judge, a PNC judge and a hacker. Status as of 5:45 AM CT Nov 8.

## Pass 1 (v1 → v2 design)

All 18 holes are closed by the v2 design:
- Cloud-reads-all-texts → on-device first.
- Model decides blocks → rules.
- Prompt injection → text is treated as data, numbers come from regex, tools are read-only.
- Spoofed-number blocking → attestation-A plus human review only.
- Duplicate stories → stable ids and merging.
- Bot fingerprinting → human-like delays and a turn cap.
- A single planted story → corroboration.
- Evidence-free verdicts → the policy layer.
- Cost → the teaching loop.
- Skill poisoning → the gate.
- Self-graded test set → generated plus blind hand-written sets.
- Unrealistic scammer → scripted plays.
- Warning text becoming a template → in-app only, no links.
- Ethics → reply-only decoys, synthetic personas, kill switch.
- Wi-Fi → replay.
- "Coach is a chatbot" → tools.
- iMessage → matched on the phone.
- Hash privacy → only bulk messages.

## Pass 2

- **Three lenses means none polished:** build order T-Mobile → NVIDIA → PNC. Done.
- **Threshold overfitting:** frozen.
- **"Graded yourself":** datagen plus Ayush's blind set. PENDING (needs the live run and Ayush).
- **Tool calling might fail on the endpoint:** `check_nemotron.py` tests it. PENDING live.
- **Coach invents figures:** number check. Done, now sign-aware.
- **Replay looks live:** badge. Done.
- **JS port drift:** parity test. Done (0 differences).
- **Consent friction:** a single tap. Done.
- **Simulated values:** labeled. Done.
- **Teammate can't run a lens:** HANDOFF.md, plus Ayush rehearses. PENDING.

## Pass 3

- **H1:** STIR/SHAKEN is voice-only → A2P for text. FIXED.
- **H2:** a legit-certification attack → risky-ask messages can never be fingerprinted good. FIXED.
- **H5:** decoy unmasking → persona filter. FIXED.
- **H7:** admin over Wi-Fi → lock. FIXED (now CSRF-proof).
- **H8:** obfuscation → normalize, punycode, shorteners. FIXED.
- **H9:** slow-burn scams → thread scoring. FIXED.
- **H11:** cost-run tool loop → 6-step cap. FIXED.
- **J1:** "everything is fake" → judge plays the scammer live. BUILT.
- **J2:** prior art → name Apate.ai and O2 Daisy. In Q&A.

## Pass 4 (independent agent attacking the running app). Most important first

| # | Sev | Finding | Status |
|---|---|---|---|
| 1 | BLOCKER | Matcher ran on the server; "0 bytes leave the phone" was false | FIXED: `matcher.js` in the browser, a parity test, network-log proof |
| 2 | BLOCKER | Story map poisonable via 2 live sessions or unlimited reports | FIXED: corroboration rules plus report rate limit |
| 3 | HIGH | Forge/gate poisoned to flag the real library text | FIXED: everyday-word check, a bigger known-good set, rate limit |
| 4 | HIGH | Real Zelle receipt / bank fraud alert flagged red | FIXED: rail-as-request regex, registered-sender cap |
| 5 | HIGH | Western Union / Venmo IRS / Spanish scams came back CLEAR | FIXED: rails, secrecy, money+pressure floor |
| 6 | HIGH | Headline bank sample on a knife edge (0.617) | FIXED: new sample text in the same play's vocabulary (warn 0.99); verify-number soft ask |
| 7 | HIGH | Test-only phrases in the regex (leak); demo sample = test item | FIXED: regex generalized, samples rewritten. Blind set still PENDING |
| 8 | HIGH | Coach number check ignored the sign | FIXED, plus code-appended safety facts |
| 9 | HIGH | Fallback coach answered the wrong questions | FIXED: word-boundary routes, amount clamp, "how much?" |
| 10 | HIGH | Scam Exposure "better" after paying bail | FIXED: direction "same" plus an explanatory fact |
| 11 | HIGH | Warning card printed the attacker's callback number | FIXED: `strip_indicators` |
| 12 | HIGH | Weak redaction; preview ≠ sent | FIXED: SSN, card, last4, address, code and owner name are redacted; the phone sends exactly the previewed text |
| 13 | MED | Thread shared across clients | FIXED: threads live in the browser |
| 14 | MED | Benchmark mutated live state | FIXED: separate Engine plus a lock |
| 15 | MED | What-if 500s on bad input | FIXED: 400 |
| 16 | MED | Real-model output types crash consent / validate / coach | FIXED: sanitizers, `_num`; garbage-stub fuzz passed |
| 17 | MED | "Unit-tested" overclaim | FIXED in wording ("4 regression checks") |
| 18 | MED | "Learns the playbook" = word counting; generic skill words | PARTLY: benign filter. Pitch says "plays from a scam taxonomy, scripted plus you live". OPEN idea: build v1 skill from Nemotron `signature_keywords` |
| 19 | MED | A judge's live play only gives an amber card | ACCEPTED: amber is the honest outcome and is now a pitch line ("one person typing can't put a play on every phone") |
| 20 | MED | Injection regex narrow | IMPROVED (disregard/forget/new rule/assistant:/mark as safe…). OPEN: optional LLM classifier pass |
| 21 | LOW | Admin CSRF | FIXED |
| 22 | LOW | Keys 1/2/3 typed into inputs | FIXED |
| 23 | LOW | Unbounded memory | FIXED: caps |
| 24 | LOW | Benchmark rescue unredacted | FIXED |

**Weakest pitch moment, per the reviewer:** a judge improvises a scam *into the phone*. Rule: in the pitch, only use the sample buttons on the phone. Judges improvise in the "You be the scammer" box.

**Question that would have sunk them:** "What runs on the phone, and does the message leave?" The honest answer now is: "A few-KB skill runs in the browser, which stands in for the phone. Only the verdict leaves; the text leaves only after consent, and redacted. You can see it in the network tab."
