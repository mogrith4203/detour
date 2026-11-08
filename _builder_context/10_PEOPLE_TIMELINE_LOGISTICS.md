# 10 · People, timeline, logistics

## People

- **Mog** (Mogindran Baladhandayutham). Product lead and presenter. Collin College student (transfer goal: UT Dallas Computer Engineering).
  - Strong with hardware, PCs and AI tooling, but not fluent at coding: he directs, AI builds.
  - Wants direct, dense, technically accurate answers and calls out errors.
  - Timezone America/Chicago.
- **Ayush Bose.** Teammate. Asleep until about 5 AM, then:
  - reads `HANDOFF.md`
  - writes the blind test set
  - rehearses every lens
  - co-presents (1:15–2:35 in the script)
- **An uncle** served as an informal mentor during ideation.
- **Judges and mentors consulted earlier:**
  - They told the team "99% of people are doing scam text", which led to the NVIDIA framing.
  - A mentor (Nick) pushed "think like the hacker" and raised ethics questions about decoys. Those are answered in 05/06.

## Timeline (Sun Nov 8, 2026, CT)

| Time | What |
|---|---|
| now (~5:45 AM) | Handoff to the builder Claude. Ayush wakes up and writes `data/handwritten.jsonl` blind. |
| ASAP | Mog-run: `check_nemotron.py` → record a live run → `datagen.py` → `bench.py` |
| by 8:30 | Both main lenses run end to end live; otherwise drop PNC from the pitch (PNC is already built, so it's probably fine) |
| 9:45 | **Feature freeze.** Bug fixes only after this |
| 9:45–11:30 | Rehearse (3:00 hard), record the ≤ 2-minute video, Devpost final |
| 11:30 | Devpost final text and video uploaded |
| **12:00** | **Hard deadline** |
| 1–4 PM | In-person judging (3 min + 2 min Q&A per judge; sponsors rotate) |
| after the event | **Rotate the NVIDIA API key** |

## Devpost checklist (devpost.com/software/detour-myou03)

- [ ] Title "Detour" and a tagline in the team's voice. Candidate: "Scammers change numbers. Not their plays."
- [ ] Tracks: T-Mobile, NVIDIA, Design, Beginner, **plus PNC**.
- [ ] Video: 2:00 or less, LIVE badge visible, follows the 06 script (skits allowed).
- [ ] GitHub link: https://github.com/mogrith4203/detour
- [ ] Screenshots: one per lens. Use LIVE ones; the ones in `screenshots/` are MOCK, so retake them.
- [ ] Sections: Inspiration / What it does / How we built it / Challenges / Accomplishments / What we learned / What's next.
- [ ] "Built with": python, fastapi, javascript, nvidia-nemotron, build.nvidia.com, openai-sdk, playwright (testing), claude (AI pair-programming). Be honest about AI assistance.
- [ ] Every metric on the page is from a LIVE run, with how the data was made: synthetic, Nemotron-generated test split plus a blind hand-written set.
- [ ] "Everything is synthetic" disclaimer.
