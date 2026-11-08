# 14 · The new technology: IDENTITY ECHO ("ask the real one"). THIS IS THE CORE. Read before 12 and 13

At 6:31 AM Mog asked for something that is a **new technology**, not a chain of existing tools. Every pillar should be exceeded, and it should be something T-Mobile, NVIDIA and PNC haven't thought of. Here is the honest market check first, then the invention.

## What already exists (so we never claim it)

- **AI honeypots / scam-baiting:** Apate.ai, about 200K bots, Australia, CommBank and TPG.
- **Diverting detected scam calls to bots:** Apate's GSMA case study is literally titled "AI-Powered Scam Detection, **Diversion** and Real-Time Threat Intelligence". There is also a 2022 US patent application, "Scam communication engagement" (US 2023/0370543), that hands detected scam calls and texts to a conversation bot.
- **Carrier→bank "on a call while banking" signal:** Telstra–CBA (2023), Telefónica Scam Signal.
- **Payee checks:** UK Confirmation of Payee, CBA NameCheck.
- **Family safe words:** public advice from the FBI and FTC.
- **Verified senders:** RCS, BIMI, STIR/SHAKEN.

**So the honeypot, diversion, the risk signal and the payee check are all "industry standard somewhere."** Chaining them is integration, not invention. Mog was right.

## The invention: Identity Echo

**Every impersonation scam has one unfixable weakness: the person or company being impersonated is real, and they know it isn't them.**
- The real grandson knows he isn't in jail.
- The real Lakeview Credit Union knows it didn't send that text.

Today **nobody asks them**. Every defense tries to judge the *message*. Identity Echo asks the *claimed identity itself*, in real time, over a channel the scammer can't touch.

### How it works (the protocol)

1. **Claim extraction (Nemotron).** A message arrives: "Grandma it's me, I'm in jail, need $3,000." Nemotron extracts the **claimed identity**: relationship "grandson", name "Jake" if given, or "your bank", "Lakeview Credit Union", "TX toll authority".
   - This is entity resolution over messy, multilingual and slang text. That's a real agentic job, not a regex.
   - It runs on the redacted text after consent. The privacy-first path resolves on the phone against hashed contacts.
2. **Resolution (on-device, tool call).**
   - The phone resolves the claim against Linda's **own contact book** ("Jake (grandson): (214) 555-0133") or the **verified business registry** (Lakeview's provenance endpoint).
   - Contacts never leave the phone; only the resolved target is used.
3. **The Echo (the carrier's unique power).**
   - **Family:** T-Mobile sends a silent push to the **claimed person's real line**: *"Someone texting from (469) 555-0188 says they're you and is asking your grandma for money. Is that you? [Yes, it's me] [No, that's not me]"*. If Jake isn't a T-Mobile customer, it goes as a plain SMS from a verified T-Mobile short code.
   - **Business:** the carrier asks the business's **provenance endpoint**: "Did you send a message with hash H to this customer in the last hour?" The business answers yes or no. It sees only a hash, never the content.
4. **Trust check (Space binding).**
   - The Echo answer is trusted only if the claimed person's line **has no recent SIM swap and no call forwarding**. Those are network facts only a carrier has (CAMARA-style).
   - A scammer who has hijacked Jake's line is caught by *that* signal instead.
5. **Verdict with ground truth.**
   - **"No, that's not me"** is the strongest scam label that can exist: the impersonated party denied it. It doesn't need a model guess.
   - **"Yes, it's me"** lets the message through with a "✓ Confirmed by Jake" badge. The real grandson in a real emergency gets helped *faster*.

### What becomes possible that didn't exist before (emergent powers)

| New capability | Why only Echo enables it |
|---|---|
| **Ground-truth scam labels at network scale.** Every "not me" is a perfectly labeled scam, labeled by the impersonated victim. | Today's scam ML trains on guesses and user reports. Echo gives **verified labels**, so Nemotron distills on-device skills (Mind) from ground truth. The defense becomes **self-labeling**. |
| **Zero-false-positive diversion.** Only conversations the real person denied get detoured to a decoy. | Existing diversion triggers on a classifier score, which can be wrong. Echo diversion is grounded in a denial from the real person. |
| **Decoys fed with live, confirmed scammers mid-attack.** | The decoy (Power) takes over a *confirmed* live scam. It extracts the cash-out rails (Reality), hands over canary tokens, and stalls (Time). The scammer never knows the target changed. |
| **Impersonation-proof family money.** PNC holds a "family emergency" payment until the Echo answers. | The payment hold (Time) resolves in **seconds**, because a human verifier answers, instead of a 24-hour cooling-off. |
| **Business provenance without content sharing.** "Did you send this?" with only a hash. | It works for any business with an endpoint, with no signing infrastructure needed (unlike RCS or BIMI). Signed messages (Soul) are the stronger tier. |
| **Echo works on voice calls and WhatsApp too.** Linda taps "Who is this claiming to be?" and the Echo goes out. | Resolution is user-triggered, so it works on channels the carrier can't see. |

## Why it beats each sponsor's pillars

- **T-Mobile:**
  - "Protect customers in ways we haven't thought of yet": they protect the *recipient*. Echo **recruits the impersonated person as the detector**, which no carrier does.
  - It uses assets only a carrier has: reaching the real line, and trusting it by checking SIM swap and call forwarding.
  - Detection is "a core piece, not the whole product": Echo is a customer experience. A grandson's phone buzzes; a grandmother sees "✓ Confirmed by Jake".
  - Privacy by design: contacts stay on the device, businesses see only hashes, and everything is opt-in.
  - Honest confidence: a human-verified verdict, not a score.
- **NVIDIA:** Nemotron does the hard, real work, in a multi-step agentic workflow:
  - **claim extraction / entity resolution** across slang and languages
  - **tool calls** to resolve contacts and the business registry and to send and await the Echo
  - **decoy takeover** that continues a live conversation in-context
  - **skill distillation from ground-truth labels**
  - the content-safety guard on every decoy line

  The agent plans, executes, uses tools and learns. It goes well beyond a chatbot.
- **PNC:**
  - A 360° navigator that knows *who you're really paying*: family-emergency payments get **identity-confirmed in seconds** before money moves.
  - This is confidence for the next move, the exact PNC phrase.
  - It pairs with Low Cash Mode language, Scam Exposure, and the Trusted Contact who *is* the Echo target for "bank" or "lawyer" claims.

## How the six stones (13) bind to Echo (the Gauntlet, revised)

**Echo is the gauntlet.** The stones are what make it unbreakable:
- **Soul:** signed businesses are the strongest Echo tier. For family, the safe word is the fallback when the Echo target doesn't answer.
- **Mind:** a scam with no claimed identity (a job scam, a crypto "investment") falls to on-device story skills, trained on Echo ground-truth labels.
- **Space:** SIM swap and call forwarding decide whether the Echo answer can be trusted. A risk token covers the moment.
- **Reality:** the payee check plus canaries, for money that's already moving.
- **Time:** the hold until the Echo answers, and the tarpit for the scammer after diversion.
- **Power:** decoys take over denied conversations and meet scammers on dormant lines.

### Failsafes for Echo itself

| Echo failure | Failsafe |
|---|---|
| The claimed person doesn't answer in 2 minutes | Fall back to the stones: safe-word prompt, Time hold, Mind and Reality checks. Never treat no answer as "safe". |
| The claimed person's line was SIM-swapped or forwarded recently | Echo answer marked **untrusted**. Space risk is raised; hold. |
| Ambiguous claim ("it's me") | The phone asks Linda: "Who are they saying they are?", one tap from her contacts. Then Echo. |
| A scammer impersonates someone who isn't in contacts (a "lawyer", a "police officer") | Echo the **verified registry** (police and court non-emergency lines, the bank's provenance endpoint), or the Trusted Contact. Mind and Reality apply. |
| Echo spam (a scammer tries to trigger mass Echo pushes to annoy people) | Echo fires only on consented customers, rate-limited per sender and target, and only for messages with a money ask or risky ask. |
| The real person taps "Yes" by mistake | A "Yes" lifts the warning but not Reality's tripwires or Space's SIM-swap holds. Two independent stones are still needed to release a held payment. |
| Business has no provenance endpoint | Neutral "not verified" (Soul), then the other stones. |

## The demo (the moment judges remember, about 60 seconds)

The screen shows **two phones**: Linda's, and **Jake's** (a judge can hold Jake's role).

1. A judge playing the scammer texts Linda: "grandma it's jake, i got arrested, need $3000 for bail, dont tell mom."
2. Linda's phone: Nemotron extracts **claimed identity: Jake (grandson)** → resolves it to her contact → **Echo sent**. Card: "Checking with the real Jake…"
3. **Jake's phone buzzes**: "Someone says they're you and is asking Grandma for money. Is that you?" The judge taps **"No, that's not me."**
4. Instantly:
   - Linda sees **"The real Jake says this isn't him. You're safe."**
   - The scammer's conversation is **detoured to the decoy**, which keeps him talking, stalls, and hands over a canary card.
   - The play becomes a **ground-truth label**, and Nemotron forges a skill that reaches every phone.
   - The scammer's Zelle handle becomes a **PNC tripwire**.
5. PNC lens: Linda's earlier pending $3,000 Zelle is **cancelled automatically**, because the identity was denied. The coach says it in plain words.
6. Flip it: a judge texts as the **real** Jake from his registered number → Echo **"Yes"** → **"✓ Confirmed by Jake"**. A real emergency gets help faster.

## Build plan (after P0; about 90–120 min; it is now the TOP of P1)

- **Data:**
  - Linda's contact book (synthetic, stored in the browser only): Jake (grandson) (214) 555-0133 T-Mobile, Maria (daughter) (972) 555-0144, Dr. Lee.
  - Business provenance registry: Lakeview, TX Toll and ParcelPost, each with a "sent log" of message hashes. The demo legit messages are pre-logged.
- **Claim extraction:**
  - `Agents.extract_claim(text) → {claimed_type: family|business|authority|none, relation, name, org}` with Nemotron JSON, and a regex/lexicon mock: grandson/granddaughter/nieto/"it's me", bank names, "police", "IRS", "toll".
  - Phone side (JS): a light lexicon resolver against contacts. Add it to `matcher.js` *as a new function* (don't touch the scoring, to keep parity), with its own parity test.
- **Echo service** (`echo.py`, server = "carrier"):
  - `POST /api/echo/start {target_ref, claimed, sender, customer}` returns `echo_id`. It checks SIM-swap and forwarding state (Space toggles) and the rate limits.
  - `GET /api/echo/inbox?line=jake` is for Jake's phone panel.
  - `POST /api/echo/answer {echo_id, answer}`.
  - `GET /api/echo/status/{echo_id}`.
  - Business path: `POST /api/echo/provenance {org, msg_hash, customer}` → yes or no from the sent log. Only hashes travel.
- **On "not me":**
  - The story gets `ground_truth: denied` and joins the Mind forge as a labeled example.
  - A **divert** flag: subsequent scammer messages in that thread go to the decoy (reuse the live-session engine with the persona continuing in-context).
  - Extract the cash-out rails → tripwires (Reality).
  - Cancel any PNC pending payment linked to that sender (M3).
- **UI:**
  - A second mini phone, **Jake's phone**, in the T-Mobile lens, with the Echo prompt and two buttons.
  - Echo status chips on Linda's cards.
  - Echo events on the NVIDIA agent graph: "Claim extractor", "Echo", "Ground-truth label".
- **Tests:**
  - denial → divert plus label plus tripwire
  - SIM-swapped target → untrusted
  - no answer → fallback hold
  - rate limit
  - legit "yes" → confirmed badge
  - business provenance yes and no
  - Echo never sends message content to the target (assert on the payload)
- **Honesty in the UI:** "Echo delivery to Jake's phone is simulated in this demo. In production, it's a T-Mobile push or a verified short-code SMS."

## The pitch line

**"Every scam pretends to be someone. We ask that someone."**
