# 11 · Research and product strategy: what to build to win all three tracks

This is the research done on Nov 8, 2026 at about 6 AM CT. It gives the builder the real-world facts that make Detour feel like a product each sponsor could ship tomorrow, not a hackathon toy. Sources are at the bottom. Mog's direction: **product first; the video and Devpost come later.** The builder's job is to take the whole technical burden and make Detour production-grade and revolutionary within the time left.

## 1. NVIDIA: use more of the Nemotron family, each for a real job

build.nvidia.com lists 27 Nemotron models (Nov 2026). These matter to us:

| Model id (verify with `check_nemotron.py` / "View Code") | Type | Job in Detour |
|---|---|---|
| `nvidia/nemotron-3.5-lightning-30b-a3b` (Hugging Face: `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16`), 1M context, tool calling | LLM (MoE, about 3B active) | **Main agent model.** Our `.env` default `nvidia/nemotron-3.5-lightning` is probably missing the `-30b-a3b` suffix. Try this id first. |
| `nvidia/nemotron-3.5-bolt-e4b` | compact LLM, tool calling | Fast, cheap agent for the persona and the forge. It also supports a credible "small Nemotron could run at the edge" next step. |
| `nvidia/nemotron-3-ultra-550b-a55b` | large MoE, 1M context | Optional "deep investigator" for the hardest rescue cases, a routing story. |
| `nvidia/nemotron-3-embed-1b` / `nvidia/nemotron-3.5-embed-1b` | embedding | **Semantic story clustering and retrieval** (see P-N1). |
| `nvidia/nemotron-3.5-rerank-8b` | reranker | Rerank candidate stories inside `search_story_map`. |
| `nvidia/nemotron-3.5-content-safety` | safety/guard, multilingual | **Guardrail** on decoy outputs, plus a second injection opinion on inbound scammer text. |
| `nvidia/nemotron-ocr-v2` / `nemotron-3.5-parse` | vision OCR | **Screenshot checks**: a customer forwards a screenshot of an iMessage/WhatsApp scam, which carriers can't see. That is the real gap. |

Why this wins NVIDIA: "beyond a chatbot" judges score multi-agent work, tool use and real-world fit. Using **five Nemotron model types**, each where it belongs, shows architectural judgment, not one-model-does-everything:
- LLM agents
- embeddings for retrieval
- a reranker
- a safety guard
- OCR/vision

Add **model routing** too: bolt for cheap steps, lightning for investigation, ultra as an optional escalation. Every call should be visible on the agent graph, with its model id and latency.

## 2. T-Mobile: fit into what they already ship

What T-Mobile ships today (Scam Shield page, Nov 2026):
- Scam Likely labels and Scam Block (#662#) for **calls**.
- **Callback Protection:** an audible warning when you dial a number on the Scam Likely list.
- Network blocking of spam texts (SMS and MMS only).
- Safe Web Browsing, which blocks known malicious sites.
- ScamShield Premium ($4/month): category blocking, reverse lookup and voicemail-to-text.
- The T-Life app is the hub.

**Gaps Detour fills:**
- Texts from fresh numbers that pass network filters.
- RCS, iMessage and WhatsApp, which the carrier can't see, through on-device matching plus screenshot checks.
- Nothing today learns the *story*.

The FCC requires carriers to block texts highly likely to be illegal, such as those from invalid or unallocated numbers. Story-level detection goes beyond number validity.

**Product moves that make a T-Mobile judge nod:**
1. Frame Detour as "Scam Shield for stories", inside T-Life.
2. **Feed Callback Protection.** Callback numbers extracted from corroborated stories go onto the Scam Likely callback list, after human review. When Linda dials the "lawyer" number from the grandparent scam, she hears the warning. Show this in the T-Mobile lens: a "Call this number" tap on the phone produces the Callback Protection warning.
3. **Feed Safe Web Browsing.** Scam domains from stories become a "would block in Safe Web Browsing" list, after review.
4. **Report to 7726 (SPAM)**, the industry short code for forwarding spam texts. The phone's Report button should say "Report (also forwards to 7726)". Simulated, and labeled so.
5. Show honest confidence levels and clear next steps (already built), and privacy by design (already proven with the network log).

## 3. PNC: speak PNC's own product language

PNC Virtual Wallet (pnc.com, Nov 2026) includes:
- **Low Cash Mode** with **Extra Time** (at least 24 hours to get back to $0 before overdraft fees), Intelligent Alerts, and Payment Control (choose which checks and ACH items to pay or return).
- **Money Bar**: Free (available to spend), Scheduled Out (upcoming bills), Savings List.
- **Calendar** of bills and payments, **Spending** trends, **Budget** categories, savings goals.
- Security and fraud alerts, **PNC Easy Lock** for the debit card.
- Zelle guidance: "use only with people you know and trust", with no purchase protection.

**Product moves:**
1. **Use their vocabulary in the PNC lens.** Show a Money Bar-style strip (Free / Scheduled Out / Savings), and label the 60-day forecast as a calendar view. When the bail what-if overdraws checking, say: "This would trigger Low Cash Mode on Nov 9. Extra Time wouldn't cover it, because your next deposit is Dec 1." A PNC judge will see their product extended, not replaced.
2. **Scam Exposure fits PNC directly.** It is money movable in the next hour through Zelle or wire, minus locked savings. Pair it with a "Lock" action that sets a savings lock or Zelle hold (simulated), next to Easy Lock.
3. **Coach next steps that match PNC tools.** Turn on Intelligent Alerts at a threshold, lock savings, call the grandson at a known number, and use Payment Control.
4. **Cross-sponsor moment.** A T-Mobile story warning ("bail via Western Union") raises an in-app PNC alert: "A scam that targets people like you is active. Your Scam Exposure is $18,790." This is the "360°" story nobody else will have.

## 4. Production-grade bar (what "works in real life" means here)

- Real model ids verified live, with routing and timeouts, and graceful fallbacks that are **labeled**.
- Every agent output is schema-validated and sanitized (mostly done). Guard-model checks on decoy outputs.
- Persistence: in-memory today. A **SQLite** store for stories, skills (versioned) and the audit log means a restart doesn't wipe the demo. Use `sqlite3` from the standard library; no new dependency.
- An append-only audit log of every promotion, block approval and quarantine, with skill rollback (`rollback(story_id, version)`) exposed in the UI. A judge asks "what if a bad skill ships?" and you click roll back.
- Rate limits and caps (mostly done), and admin auth (done).
- Observability: per-agent latency, hosted-call count and token or cost estimate on the NVIDIA lens.
- Tests: parity, finance, the garbage-model fuzz, plus new tests for each feature. The UI click-path audit runs with 0 console errors.
- Accessibility: large-text mode on the phone (the customers are seniors), keyboard focus and contrast.

## 5. Revolutionary core: keep it the center

**Adversary-in-the-loop learning.** Attackers teach the defense. Nemotron distills each attack into a few-KB, unit-checked, rollback-able skill that runs on the device, so the network learns once and every phone benefits. The rest of this file exists to make that loop credible in production.

## Sources

- [build.nvidia.com Nemotron model search](https://build.nvidia.com/search?q=nemotron)
- [Nemotron 3.5 Lightning 30B A3B (Requesty listing: id, 1M context, tool calling)](https://www.requesty.ai/models/nvidia/nemotron-3.5-lightning-30b-a3b)
- [NVIDIA Safety for Agentic AI blueprint](https://build.nvidia.com/nvidia/safety-for-agentic-ai/modelcard)
- [T-Mobile Scam Shield](https://www.t-mobile.com/scamshield)
- [PNC Virtual Wallet](https://www.pnc.com/en/personal-banking/banking/checking/virtual-wallet.html)
- [FCC requires carriers to block scam texts (WTVR, 2023)](https://www.wtvr.com/news/national/fcc-now-requires-phone-carriers-to-block-scam-text-messages)
