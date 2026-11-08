# 09 · Voice and style: make it sound like Mog and Ayush, not a template

**Honesty boundary.** The team used AI to build this, and HackUTD allows it. Never write anything that denies or hides AI use. If a judge asks, the answer is "yes, we directed Claude to write code fast, and we made the product, safety and pitch decisions". The goal is copy that sounds like two first-time hackathon students who know their project cold, not generic AI marketing.

> Section "What X (Twitter) showed" is filled in after browsing X with Mog's account. If it's empty, Mog wasn't signed in yet. Use the rules below.

## The team's voice

- First person plural, casual and confident: "we", "our decoys", "Linda's phone".
- Short sentences. Concrete numbers and names: Linda, $3,000 bail, 50 of 60 days, decoy-02, (972) 555-0161.
- It's their first hackathon, and they were up all night. They can say so; a little personality is good.
- Admit what broke and what's simulated. Judges trust teams that name their limits.
- Mog's register: direct, a bit blunt, technical but plain. No hype.

## Signs that read as AI-written (remove them)

- Em dashes everywhere (—). Use periods, commas or parentheses.
- Words: delve, leverage, seamless, robust, cutting-edge, revolutionize, empower, harness, unlock, elevate, game-changer, "in today's fast-paced world", "it's not just X, it's Y", "whether you're X or Y".
- Rule-of-three lists every time; perfectly parallel bullets; every section the same length.
- Emoji section headers (🚀 ✨ 🔒), headings like "Key Features" / "Conclusion", and a closing summary paragraph.
- Over-balanced hedging ("While X, it's important to note Y").
- Title Case On Every Heading.
- Generic impact claims with no number. Every claim needs a number or a concrete example.

## Devpost sections: shape (fill in with the team's own words and LIVE numbers)

- **Inspiration:** a real-feeling hook. Example: someone's grandparent got a "grandson in jail" text, or "we kept seeing the same toll scam from different numbers". Use it only if it's true for Mog or Ayush; ask them.
- **What it does:** 3–5 sentences on the loop. Decoys learn the play; phones catch the play; Nemotron is the teacher.
- **How we built it:** stack, the 5 Nemotron agents, the rules layer, the browser matcher with Python parity tests, record/replay. Mention that they used Claude as a coding partner.
- **Challenges:** STIR/SHAKEN turned out to be voice-only, so they switched to A2P registration. A red-team found that "0 bytes leave the phone" wasn't true at first, so they moved the matcher into the browser and proved it with the network log. Two typed sessions could poison a real dentist, so they rebuilt corroboration. NVIDIA API access only worked from the laptop.
- **Accomplishments:** a judge can play scammer live, the parity test, the privacy proof, and the bail what-if.
- **What we learned:** real lessons in plain words.
- **What's next:** real decoy lines with legal review, a small on-device model, screenshot checks for iMessage/WhatsApp, open-banking data for PNC.

## Commit messages and README

- Commits: short, lowercase is fine, imperative ("fix coach sign check", "move matcher to browser"). Avoid giant AI-style paragraphs. Existing history has long messages; new ones should be short.
- README: rewrite the intro in their own voice, keep the technical tables. Add a "what's real / what's fake" section (already there) and a "how to run in 1 command" line.

## What X (Twitter) showed

(Pending, to be filled after browsing X: what judges and hackathon winners post about AI-built projects, what reads as low-effort AI slop vs a strong demo, and pitch and demo-video patterns that win.)
