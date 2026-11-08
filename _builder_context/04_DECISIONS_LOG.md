# 04 · Decisions log (settled; don't re-litigate without a strong reason)

| # | Decision | Why | Rejected alternatives |
|---|---|---|---|
| D1 | One engine, three sponsor lenses (tabs; keys 1/2/3) | Every rotating sponsor judge lands on a screen built for their own brief, and switching tabs proves it's one real system | One dashboard explained out loud (loses PNC, weak for NVIDIA); three separate apps (about 3× the work, can't finish by noon) |
| D2 | Match the *story/play*, not the number | Numbers rotate in hours; plays don't. This is the Pyramid of Pain idea | A number blocklist, which is the benchmark baseline we beat |
| D3 | Rules enforce, the model judges | A model must never block or certify on its own (poisoning, injection) | v1, where the model decided blocks. Red-team pass 1 killed it |
| D4 | On-device first; Nemotron only for unsure messages, with consent | Privacy by design (T-Mobile pillar) plus cost at carrier scale | Sending every message to the cloud (v1) |
| D5 | Phone matcher really runs in the browser (`matcher.js`), parity-tested against Python | Red-team found "0 bytes leave the phone" was false when it ran server-side. The claim is now true and proven by network log | Saying "designed to run on the phone" (kept only as a fallback line) |
| D6 | Teaching loop: forge → gate (4 checks) → versioned skill | NVIDIA "beyond a chatbot" plus a measurable drop in hosted calls | Fine-tuning a model, which there was no time for |
| D7 | Corroboration needs 2 independent decoy lines; live sessions and reports add at most one each, never alone | Red-team showed two typed sessions could get a real dentist flagged | Counting any 2 sessions; unlimited reports |
| D8 | STIR/SHAKEN only for callback numbers; A2P registration (short code / 10DLC / verified toll-free) for text senders | Factual: STIR/SHAKEN is voice-only. T-Mobile judges would catch the error | Applying attestation to SMS senders (an earlier error, fixed) |
| D9 | Scammer traffic is scripted plays from a taxonomy, plus a judge typing live | Realistic, deterministic demo. A judge playing scammer is the most memorable proof | A purely LLM-generated scammer (unpredictable on stage) |
| D10 | Synthetic data only. Nemotron generates the test set (`datagen.py`, frozen test split); Ayush writes a blind hand-written set | T-Mobile released no dataset; blind data answers "you graded yourself" | Using scraped real scam texts |
| D11 | Thresholds frozen at warn ≥ 0.60 and clear < 0.30 | Avoid overfitting; say so in the pitch | Tuning to the test set |
| D12 | Record/replay is the Wi-Fi backup, always labeled REPLAY | Honesty; the venue Wi-Fi is risky | Silent mock fallback |
| D13 | Mock-mode scoreboard numbers are blurred in the UI | So nobody accidentally quotes fake numbers | Showing them |
| D14 | PNC: a deterministic finance engine; the coach is Nemotron with tools, and every figure is checked against tool results, sign included | PNC wants indicators, not a chatbot; NVIDIA dislikes plain chat | A free-form chat coach |
| D15 | Scam Exposure indicator plus lock-savings what-if | PNC's "something no one has thought of", backed by Singapore banks' Money Lock | – |
| D16 | Linda's pension set to $2,050 | The original synthetic budget was overdrawn with no scam, which ruined the bail contrast | – |
| D17 | Demo samples are NOT test-set items | The reviewer flagged leakage | – |
| D18 | Pitch wording: "few-KB skill", "4 regression checks", never "model on the phone" or "unit-tested" | Avoids overclaiming, which is fatal with judges | – |
| D19 | Lead the NVIDIA pitch with how the model is used, not "scam texts" | Judges said 99% of teams are doing scam texts | – |
| D20 | No iOS app | A browser phone panel is enough; time | Building native |
| D21 | Vanilla JS, no build, no CDN | Works offline at the venue; nothing to install | React/Vite |
