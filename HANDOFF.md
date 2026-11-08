# Handoff for Ayush (read this first, ~3 min)

Mog worked overnight with Claude. Here is where things stand and what you need to do.

## 1. Your first job: write the hand-written test set (before you read any code)
Open `data/handwritten.jsonl`. Write **10 scam texts and 10 real (legit) texts**, one per line, using the two example lines as a pattern (remove the `#` at the start).
- Make the scams *new*: different wording, new numbers, some with no link or number at all.
- Make the legit ones tricky: real bank alerts, real delivery texts, a friend texting from a new number.
- Numbers must look like `(214) 555-01NN`. Websites must end in `.example`.
- **Don't look at `detour/core.py` first.** The point is that the matcher has never seen your messages, so judges can trust the score.

## 2. Run it
```bash
./run.sh                    # opens http://localhost:8000
python3 check_nemotron.py   # PASS/FAIL for chat, JSON, tool calling
python3 bench.py            # scoreboard, includes your hand-written set
```
If NVIDIA is unreachable at the venue: `DETOUR_REPLAY=1 ./run.sh` replays a recorded live run. The header turns amber and says REPLAY. We don't hide that.

## 3. The demo in three tabs (keys 1 / 2 / 3)
1. **T-Mobile: protect the customer.** On the decoy console, a decoy persona talks to a scammer. The phone then gets the same play from a new number and warns, on-device. If the phone is unsure, it asks before sending a redacted copy.
2. **NVIDIA: Nemotron as the teacher.** The live agent graph runs: decoy, extractor, validator, rescue agent with tool calls, skill forge, and a gate with 4 tests. After that, the phone handles that play alone. The scoreboard compares a blocklist, the on-device matcher, and on-device plus Nemotron.
3. **PNC: 360° financial health.** The customer is Linda. There are 4 indicators, including Scam Exposure, plus a 60-day forecast. The what-if "$3,000 bail" shows an overdraft. The coach (Nemotron + tools) answers with numbers checked against the tools.

## 4. Pitch rule for NVIDIA judges
Lead with **how the model is used**, not "scam texts". The line: *Nemotron learns from attackers, then teaches a tiny on-device model, and every lesson is unit-tested before it ships.* If they ask what it's for, say scams in one sentence.

## 5. Rules
- `.env` holds the API key. It's gitignored. Never commit it or paste it anywhere.
- Feature freeze is **9:45 AM**. After that, only fixes.
- Video (≤ 2 min) and Devpost are due by **11:30**. The hard deadline is noon.
- Everything is synthetic. Say so if asked.
