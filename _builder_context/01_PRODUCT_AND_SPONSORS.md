# 01 · Product and sponsors

## UPDATED 6:20 AM: the core idea is now in 12_REINVENTION_THE_WINNING_IDEA.md

"Detour is a carrier–bank scam fusion center fed by AI decoys. It stops a scam at three chokepoints: the message, the moment, and the money." Everything below still holds; 12 adds the carrier→bank risk token and the cash-out tripwires.

## One-line pitch (NVIDIA framing, agreed with the team)

"Most AI security waits for the attack. Detour sends Nemotron out to talk to the attackers first. It learns their playbook, then teaches the phone a few-KB skill that runs right on the device. Every lesson passes 4 regression checks before it ships."

The team spoke to judges, who said "99% of people are doing scam texts". So **lead with HOW the model is used** (adversary-in-the-loop learning, distilled into tested on-device skills). Name the use case, scams, in one sentence, not as the headline. If judges ask about the use case, answer honestly and directly.

Spine sentence for any audience: **decoys learn the play; phones catch the play.** Scammers change numbers, not their plays.

## The core idea

1. **Decoy lines.** AI personas (synthetic seniors: Linda Park 71 Plano, Ray Gutierrez 66 Mesquite, Doris Whitfield 78 Sulphur Springs) sit on carrier-owned decoy numbers. They are reply-only.
2. **Learning.** When a scammer texts a decoy, Nemotron keeps them talking in character. A second Nemotron call extracts the scam's *story*: category, who it impersonates, claim, ask, payment rail and tactics.
3. **Validation.** Plain rules the model can't overrule:
   - prompt-injection scan
   - verified-business allowlist (poisoning defense)
   - A2P sender registration check for text senders. STIR/SHAKEN applies only to voice calls, so it is used only for callback numbers.
   - corroboration
4. **Teaching.** Each story becomes a few-KB **skill** (weighted keywords and phrases) that is synced to phones. The phone matcher runs in the browser (`static/matcher.js`), standing in for the phone.
5. **On-device decision.** warn / clear / unsure.
   - The message text never leaves the phone.
   - Only for "unsure", and only after the customer taps consent, a **redacted** copy goes to the Nemotron rescue agent. That agent works in a tool loop (ReAct, at most 6 steps).
6. **Closing the loop.** If rescue finds a scam, the **skill forge** (Nemotron) proposes new words. The **gate** runs 4 regression checks; if they pass, the skill version is bumped and synced. The next copy of that scam is caught on-device with zero hosted calls.
7. **PNC tie-in.** The same customer's finances: what that "$3,000 bail" would do (overdraft, runway), plus **Scam Exposure** as a new financial-health indicator.

## Sponsor briefs (in their words, as captured during research) and what each lens must prove

| Sponsor | Brief | Judged on | Lens must prove | Money shot |
|---|---|---|---|---|
| **T-Mobile** | "Protect customers from scams and fraud in ways we haven't thought of yet." Detection is a "core piece, not the whole product"; "safeguards and customer-facing experiences"; "clear next steps, honest confidence, privacy by design". **T-Mobile releases NO dataset**; teams generate their own synthetic data (confirmed by T-Mobile on Discord). | Creativity, impact, usability, security & privacy, detection accuracy | A new-number scam is caught because the *story* matches; the customer gets a clear next step; nothing personal left the phone; accuracy on a held-out synthetic set vs a number-blocklist baseline | Brand-new number → warn card, privacy meter "0 bytes left the phone" |
| **NVIDIA** | "Use Nemotron beyond a chatbot": multi-step workflows, agents that plan and execute, tool integration, real-world applicability. Their "what wins" list includes multi-agent systems, ReAct loops, tool calling, and agent simulation and eval. | Those four requirements, plus how agentic it looks | Live agent graph: each Nemotron agent's input, tool calls and output on screen. A simulation + eval pipeline. The teaching loop cutting hosted calls. | Unsure message → visible tool calls → forged skill → gate passes → next copy caught on-device, hosted-call counter doesn't move |
| **PNC** | "360° Financial Health Navigator": see the whole financial picture across checking, savings, CDs, IRAs, loans, cards and mortgages, and feel confident about the next move. Suggested: a conversational coach, 3+ health indicators, a balance and obligation forecast, a what-if simulator, "something no one has thought of yet". | Their listed features, how clear the picture is, the confidence it gives | All 8 account types in one view, 4 indicators, 60-day forecast, what-if, and a Nemotron coach with tools. New idea: **Scam Exposure** (money that could leave in the next hour) | "$3,000 bail" what-if → checking overdrawn 50 of the next 60 days. The coach answers with tool-checked numbers and adds a scam warning |

HackUTD general criteria (every judge): innovation, technical complexity, completeness, design, impact, presentation. Tips from organizers: 3-minute pitch plus 2-minute Q&A; flow is problem → solution → demo → impact; show metrics; format is flexible.

## Safe facts to cite (verify before quoting if you have web access)

- FTC: Americans reported a record **$15.9B** in fraud losses in 2025, with text the most-reported contact method. This is in the plan doc; re-verify the exact figure and year with a quick search before putting it on a slide.
- FBI IC3: **$7.7B** lost by people over 60 (per the plan doc; re-verify).
- Prior art to name proactively:
  - Apate.ai and O2's "Daisy" (AI scambaiting)
  - Nomorobo (dormant decoy numbers)
  - Singapore banks' "Money Lock" (supports Scam Exposure and lock-savings)
  - Google/Pixel scam detection and T-Mobile Scam Shield (judge a single number or message on one phone)

## What is real vs simulated (say this plainly if asked)

- **Real:** the agent pipeline, Nemotron calls (with a key), tool calling, validator rules, the in-browser matcher, the forge and gate, the finance engine and coach, and the benchmark.
- **Simulated:** scammer traffic (scripted plays, or a judge typing), decoy phone lines, sender registration values, the verified-business list, the customer phone (a browser panel), and the bank customer Linda.
