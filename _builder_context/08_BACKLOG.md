# 08 · Backlog (priority order; stop at the 9:45 AM CT freeze unless it's a bug fix)

Each item lists who does it, what to do, and the acceptance criteria. "Mog-run" means it needs Mog's Mac Terminal, because NVIDIA is unreachable elsewhere. Give him exact commands.

## P0: must happen before judging

1. **Live Nemotron verification (Mog-run).**
   - **Do:** run `python3 check_nemotron.py`.
   - **Accept:** 3× PASS.
   - **If the model id 404s:** put the id it prints into `.env` and rerun.
   - **If tool calling fails:** implement a JSON-ReAct fallback in `Agents.rescue` and `coach._live`. Ask the model for `{"tool": name, "args": {...}}` or `{"final": {...}}`, then parse it with `parse_json` and loop. Keep the 6-step cap.
2. **Live demo pass plus recording (Mog-run).**
   - **Do:** `DETOUR_RECORD=1 ./run.sh`, then click exactly the pitch path in 06: Reset → Load decoy history → decoy session (bank_alert, decoy-01) → the 5 phone samples → grandparent consent → deliver again → PNC bail what-if → coach bail question → benchmark.
   - **Accept:** `replays/` is non-empty, and `DETOUR_REPLAY=1 ./run.sh` replays the same path with the REPLAY badge.
   - **Commit `replays/`?** Yes. They contain model outputs only, no secrets. Check before committing.
3. **Live data and benchmark (Mog-run, plus Ayush).**
   - **Do:** run `python3 datagen.py`. Ayush fills in `data/handwritten.jsonl` (10 scam + 10 legit) blind. Then run `python3 bench.py`.
   - **Accept:** `results/benchmark.json` has mode `live`, all three sets are present, and there are no crashes on odd generated rows.
   - **Then:** put the real numbers into the pitch brackets [X]/[Y]/[N]/[M] in 06.
4. **Live sanity of the agent prompts.** With real model output, check that:
   - the persona stays in character (the filter catches "AI/decoy")
   - extraction yields a sensible category and title
   - the rescue agent actually calls tools before `submit_verdict`
   - the forge proposes non-generic words that pass the gate
   - the coach cites only tool numbers

   **Do:** tune the prompts in `core.py` / `coach.py`, NOT the thresholds.
   **Accept:** the demo path produces the intended cards live.

## P1: high value, if time

5. **Devpost write-up** (see 10 for the checklist).
   - **Sections:** Inspiration / What it does / How we built it / Challenges / Accomplishments / What we learned / What's next / Built with.
   - **Voice:** the team's own voice (09). Mog and Ayush must edit it themselves; it's their submission.
   - **Tracks:** add PNC to T-Mobile, NVIDIA, Design and Beginner.
6. **2-minute demo video.**
   - Screen-record the live demo path with voiceover, following the 06 script, trimmed to 2:00 or less.
   - Show the LIVE badge.
   - Skits are allowed.
7. **Skill v1 from Nemotron `signature_keywords`** (red-team #18).
   - **Do:** in `StoryMap.new_story`, weight the model's `signature_keywords` (filtered by `benign_words()`) above raw transcript counts. Port any matcher-visible change to JS and keep parity.
   - **Accept:** benchmark not worse; parity 0 differences.
8. **Optional LLM injection classifier** (red-team #20).
   - **Do:** in `validate`, after the regex, ask Nemotron "does this text try to instruct an AI?" and treat yes as tainted. The regex still decides alone in mock mode.
   - **Accept:** "Disregard everything above…" is quarantined.
9. **Story labels sanity** (red-team #19).
   - **Do:** only show the best story's title when its category agrees with the message's topic. Otherwise say "Matches a known scam pattern".

## P2: polish

10. A visual "what left the phone" network panel in the T-Mobile lens: the last 5 outgoing payloads, verdict-only vs consent.
11. A large-text mode for older customers on the phone panel.
12. A "Report" flow confirmation toast already exists; add a demo of reports corroborating a play that a decoy line has already seen.
13. Accessibility pass: focus rings and aria labels on the lens tabs.
14. README "in our own words" rewrite, done by the team.

## Don't do

- Don't change `MATCH`/`CLEAR` thresholds.
- Don't add test-set phrases to regexes.
- Don't put the key anywhere but `.env`.
- Don't add a build step or CDN dependency.
- Don't claim a model runs on the phone.
- Don't silently fall back to mock in front of judges.
