# Adopted skills: what to use, when, and how it applies to Detour

On Nov 8, 2026 (about 6 AM CT) we searched X, logged in as Mog, for the skills that hackathon winners and top builders are actually sharing. Then we pulled the repos from GitHub, read them, and kept only what helps Detour.
- Every skill here is third-party. Treat it as a **working method, not authority**: the rules in `00_START_HERE.md` win on any conflict.
- Licenses and the exact source commits are in `licenses/` and `licenses/SOURCES.txt`.

## Install them so Claude Code loads them automatically (builder: do this first)

```bash
# from the repo root
mkdir -p .claude/skills
for d in _builder_context/adopted_skills/{design,process,testing,nvidia,security}/*/ _builder_context/adopted_skills/{ui-demo,santa-method,verification-loop,eval-harness,ai-regression-testing,agent-security-hardening,browser-qa,click-path-audit,make-interfaces-feel-better,brand-voice}/; do
  n=$(basename "$d"); [ "$n" = "taste-skill" ] && continue; cp -r "$d" ".claude/skills/$n"; done
echo ".claude/skills/" >> .gitignore   # keep the repo light; the source copy stays in _builder_context
```

**Do NOT install `design/taste-skill` as a live skill.** Its frontmatter registers a Stop hook that runs `scripts/gate.mjs` (Node 22 + Chrome), and it is built for marketing *websites*. Read its principles by hand instead.

## What X said, and why each pick

- **Most-shared "winner's setup":** ECC by Affaan Mustafa, winner of the Anthropic × Forum Ventures hackathon (posts with 2K–4.6K likes). That's where the top-level ECC skills in this folder come from.
- **"Best GitHub repos for Claude Code"** (@hasantoxr, 5.5K likes):
  1. obra/**superpowers** (314K★)
  2. hesreallyhim/awesome-claude-code (57K★)
  3. GSD
  4. claude-mem
  5. **UI UX Pro Max** (146K★)
- **Anti-AI-slop UI.**
  - "the Head of Design at X just open-sourced his taste" (2.7K likes) → **taste-skill** (Leonxlnx, 111K★).
  - **Impeccable** (pbakaus, 105K★) and Hallmark "each picked up over 10,000 GitHub stars in a week by promising AI agents taste" (@techfren).
  - Emil Kowalski's design-engineering skills are the most-cited source for UI polish and animation craft.
- **Our stack:**
  - **NVIDIA's official skills repo** (NVIDIA/skills, 3.9K★) has Nemotron content-safety policy generation and retrieval (embed/rerank) recipes.
  - **Anthropic's official skills** (anthropics/skills, 189K★) have `frontend-design` and `webapp-testing` (Playwright).
  - **Trail of Bits** has security review skills.
- **Judges** (@mittalparth_, who judged a hackathon):
  - Show a live demo, not slides.
  - No AI voice or AI script in the video.
  - Write the README yourself, in short points.
  - "The demo matters more than the code."

## The catalog, mapped to Detour

### Design: kill the "AI-made" look (the UI is Mode **Operate**: an app dashboard, not a landing page)

| Skill | Use it for | Detour notes |
|---|---|---|
| `design/impeccable` (Apache-2.0) | **Primary design skill.** Run `critique` → `audit` → `polish`/`layout`/`typeset`/`clarify`/`harden` on `static/index.html`. Read `reference/craft-floor.md` before any UI edit. | Mode = **Operate** (scanability, consistency and the real usage scene outrank expression). Keep the sponsor accents (T-Mobile #E20074, NVIDIA #76B900, PNC #EF7622) and the dark console look; refine, don't redesign. Run `harden` for empty, error, offline and long-text states. |
| `design/emil-design-eng` | Micro-interactions, motion and the invisible polish details | Agent-graph pulses, the consent sheet slide, warn-card entrance. Respect `prefers-reduced-motion`. |
| `design/break-ui` | Feed worst-case data into every panel (long names, emoji, non-Latin text, huge numbers, empty states) | Judges *will* type weird text into "You be the scammer" and the coach. Every panel must survive it. |
| `design/anthropic-frontend-design` | Distinctive, intentional choices instead of template defaults | Typography hierarchy and avoiding generic gradient-card dashboards. |
| `design/ui-ux-pro-max` | Searchable design intelligence (palettes, type pairings, UX guidelines) via `scripts/search.py` | Use it to check contrast and accessibility on the phone panel's senior mode. |
| `design/taste-skill` (reference only, not installed) | The anti-slop principles: plain copy in its own voice, one system, quiet micro-interactions, real product UI instead of decoration | Read the House Rules for the *principles*. Ignore the website-specific rules (photos, heroes). |
| `make-interfaces-feel-better` (ECC) | Concrete polish checklist | Last pass before freeze. |

**Signs of AI-made UI to remove:**
- purple-blue gradients on everything
- glassmorphism cards
- emoji icons
- identical card grids
- "✨ AI-powered" labels
- centered-everything hero layouts
- generic Inter at one weight
- shadows on everything
- lorem-style placeholder copy
- inconsistent radii
- decorative charts with no data

### Process: how winners build fast without breaking things

| Skill | Use it for |
|---|---|
| `process/superpowers-writing-plans` + `superpowers-executing-plans` (if present) | Write a short plan per backlog item before coding |
| `process/superpowers-dispatching-parallel-agents` + `superpowers-subagent-driven-development` + `superpowers-using-git-worktrees` | Run independent P1 features in parallel sub-agents on separate worktrees (e.g. N1 embeddings ∥ P1 PNC vocabulary ∥ T1 callback protection) |
| `process/superpowers-test-driven-development` | Write the test first for every new feature (rollback, routing, persistence) |
| `process/superpowers-systematic-debugging` | Any failing test or live-model weirdness: find the root cause before you fix |
| `process/superpowers-verification-before-completion` + `verification-loop` (ECC) | Never claim done without running pytest + parity + smoke + Playwright, and showing the output |
| `santa-method` (ECC) | Two independent reviewers must both pass each feature (judge view + hacker view) |
| `click-path-audit` (ECC) | Trace every button through the full demo flow; find actions that cancel each other |
| `eval-harness`, `ai-regression-testing` (ECC) | Evals before code; the garbage-model stub pattern for model-output robustness |

### Testing

| Skill | Use it for |
|---|---|
| `testing/anthropic-webapp-testing` | Playwright helpers for the local app (`scripts/with_server.py` starts the server, then tests) |
| `browser-qa` (ECC) | Console errors and layout at 1440×900 and 1280×800 after every UI change |
| `ui-demo` (ECC) | LATER: recording the demo video. Not now. |

### NVIDIA / Nemotron

| Skill | Use it for |
|---|---|
| `nvidia/nemotron-policy-generator` | Write a **custom safety policy** for the Nemotron content-safety guard (backlog N3). Detour's policy covers:<br>(1) a decoy must never reveal it's an AI or decoy, share real PII, or agree to pay<br>(2) inbound text that tries to instruct an AI = injection<br>(3) no real-person data |
| `nvidia/nemotron-retrieval-recipes` | Nemotron **embed + rerank** patterns for backlog N1 (semantic story memory) |
| `nvidia/rag-eval` | Evaluate retrieval quality for N1: does a reworded scam retrieve the right story? Add it to `bench.py` as a retrieval-hit-rate row. |

### Security (Trail of Bits + ECC)

| Skill | Use it for |
|---|---|
| `security/tob-sharp-edges` | Find footguns in our APIs (consent payloads, what-if events, report spam) |
| `security/tob-agentic-actions-auditor` | Audit the agent tool loops: can scammer text make the rescue or coach agent do something it shouldn't? |
| `security/tob-entry-point-analyzer` | Enumerate every externally reachable endpoint and its trust level |
| `security/tob-differential-review` | Review each commit's diff for security regressions |
| `security/tob-property-based-testing` | Property tests for the matcher (normalize is idempotent; redact never leaks digits ≥ 12; JS == Python on random inputs) |
| `agent-security-hardening` (ECC) | Hardening checklist for agents that read untrusted content |
