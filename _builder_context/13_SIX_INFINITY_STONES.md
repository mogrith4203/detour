# 13 · The six Infinity Stones (v2): six unrelated powers, each with a failsafe, bound into one gauntlet

**Design rule (Mog's):**
- Each stone controls a **completely different dimension** of a scam, so no stone can do another's job.
- Each is **strong on its own**: deployed alone, it would still stop a real class of scams.
- Each has a **failsafe** for when it fails.
- Together they leave the scammer **no way around**. To beat Detour, a scammer would have to beat six unrelated systems at once, in six different disciplines.

## A scam has six parts. Each stone owns one

Every scam has to answer six questions. Detour puts a stone on each one.

| Stone | The scam's question | Discipline it comes from | One-line power |
|---|---|---|---|
| **Soul** | *Who* is really talking? | Cryptography / authentication | Real businesses and real family **prove** themselves. Impersonators can't. |
| **Mind** | *What* are they saying? | Language / machine learning | The phone recognizes the scam **story**, from any number, without sending the text anywhere. |
| **Space** | *How* did they reach you? | Telecom network signals | The carrier sees the **delivery pattern** (unregistered sender, call in progress, SIM swap, call forwarding) without reading any content. |
| **Reality** | *Where* does the money go? | Payments / anti-money-laundering | The bank checks the **destination** (mule accounts and wallets, exposed by canary traps) before money moves. |
| **Time** | *When* must the victim act? | Behavioral psychology | Scams need panic. A **time lock** and a trusted human break the "hot state". |
| **Power** | *Who* is the attacker? | Deception / counter-intelligence | **Decoys** meet scammers first, learn their plays, burn their time, and plant traps. |

They really are unrelated: crypto signatures, NLP, network metadata, payment rails, human psychology and deception ops share no code path, no data type and no failure mode.

---

## SOUL: Proof of the real (authentication, not detection)

- **Power alone:** impersonation is the core of most scams (fake bank, fake toll agency, fake grandson). Instead of guessing what's fake, **make the real verifiable**.
  - **Signed business messages.** Verified businesses (Lakeview Credit Union, TX Toll, ParcelPost, PNC itself) sign their texts with a digital signature, and the phone verifies it on-device. Signed and valid shows a **"Verified ✓ Lakeview Credit Union"** badge. A message *claiming* to be Lakeview without a valid signature shows "Claims to be Lakeview, not verified."
    - Real-world parallels: RCS verified senders, BIMI verified logos for email, STIR/SHAKEN for calls, and the A2P sender registry we already check.
  - **Family Safe Word.** When a message claims to be family and asks for money ("Grandma it's Jake…"), the phone prompts: *"Ask them your family safe word before you do anything."* The safe word is set in advance with the Trusted Contact and never stored in plain text, only as a salted hash on the device. A scammer can't know it.
    - Real-world parallel: the FBI and FTC publicly advise families to set a code word against AI voice-clone scams.
- **Beats:** impersonation from any channel, including AI voice clones, because the safe word works on voice calls too.
- **Failsafe:**
  - A business that doesn't sign isn't marked fake; it gets "not verified" (neutral), and the decision falls to Mind, Space and Reality.
  - If there's no safe word set, prompt a **callback on a known number** from the contact book (out-of-band verification).
  - A signature can never *clear* a message that carries a payment ask to a new payee: Reality and Time still apply.
- **Build** (about 40 min):
  - Server holds demo ECDSA P-256 keys per allowlisted business. `GET /api/phone/rules` publishes their **public** keys.
  - Demo "legit" messages are signed. The phone verifies with WebCrypto `ECDSA/P-256/SHA-256`, which works in Chrome on localhost.
  - Python test signs and the JS test verifies (parity).
  - Safe-word UI: set the word (stored as a hash) → challenge sheet on family-plus-money messages.

## MIND: The story, recognized on-device (BUILT)

- **Power alone:** catches the scam's *script* from a brand-new number. Keyword skills plus rules run on the phone, few KB, privacy by design. Nemotron distills new plays into tested skills; the network learns once and every phone knows.
- **Beats:** number rotation and text-based scams.
- **Failsafe:**
  - Novel wording that misses every skill goes through:
    - the **money + pressure floor** → unsure
    - **consent** → Nemotron rescue (tools)
    - a new skill, after the 4-check gate
    - versioned **rollback** if a skill misfires
  - Never blocks on its own; it only warns.
- **Build:** done. Add rollback UI (X2) and embeddings (N1) if time allows.

## SPACE: The delivery pattern (network signals, zero content)

- **Power alone:** the carrier sees *how* a message or call arrives without reading it:
  - an **unregistered 10-digit sender** (A2P status, built)
  - the **first contact ever** from this number
  - **call in progress with an unknown number** while banking: Australia's Telstra–CBA scam indicator, Spain's Telefónica Scam Signal API
  - a **recent SIM swap** or **call forwarding on** for the customer's own line (GSMA CAMARA APIs), the classic account-takeover setup
  - a burst of the same template to many customers in minutes (a campaign blast)
- **Beats:** voice scams with no text, and brand-new scripts. It's content-agnostic, so it works when Mind is blind.
- **Failsafe:**
  - Signals unavailable (Wi-Fi calling, roaming, WhatsApp): degrade to **device-side** signals (number not in contacts, first contact).
  - Network signals alone never hold money. They raise a **content-free risk token** (consented, expires in 2 hours) that only counts in combination (see the Gauntlet).
- **Build** (about 35 min):
  - `space.py`: signal evaluation with rules.
  - Simulated network state toggles on the phone panel ("On a call with unknown number", "SIM swapped 2h ago", "Call forwarding on"), labeled simulated, CAMARA-modeled.
  - Campaign-burst detector: the same skill hit from 3+ distinct customers within 10 minutes, counted from phone verdicts, which carry no text.
  - The token is minted by `engine.ondevice()` and the toggles.
  - `GET /api/carrier/signal`, and the token JSON is shown in the UI.

## REALITY: Follow the money (destination intelligence + canary traps)

- **Power alone:** every scam ends at a payment destination. The bank checks the **payee** at the moment of payment:
  - **Cash-out tripwires:** Zelle handles, wallets and mule accounts that the decoys extracted (regex-derived, corroborated).
  - **Canary tokens:** decoys hand scammers booby-trapped fake cards, accounts and Zelle emails. When a scammer uses one, it fires with full attribution and **exposes the payout (mule) account**, which becomes a tripwire. The scammer builds our blocklist for us.
  - **Privacy:** tripwire checks use a **k-anonymity hash-prefix range lookup**. PNC sends 5 hex characters, and the carrier never learns the payee.
- **Beats:** scams on any channel (voice, WhatsApp, in person). The money still has to land somewhere.
- **Failsafe:**
  - An unseen payee (a fresh mule) falls back to **behavioral payment risk**: new payee + risky rail (Zelle, wire, crypto, gift card) + amount relative to Scam Exposure. That feeds the Gauntlet score.
  - Allowlisted billers are never tripwired.
  - Canaries are minted only in decoy sessions, from a reserved synthetic range, so they can't collide with real cards.
- **Build** (about 60 min): see M1/M3 in 12, plus `mint_canary`, `POST /api/pnc/card_auth`, and `GET /api/intel/range/{prefix}`.

## TIME: Break the panic (behavioral circuit breaker)

- **Power alone:** scams run on urgency ("in the next hour or your grandson stays in jail"). The Time stone gives a **time lock**. A first-time, large, risky-rail payment under active risk is **held for a cooling-off period**, not blocked. The hold shows:
  - a countdown
  - her own numbers: the automatic what-if says "overdrawn 50 of 60 days, triggers Low Cash Mode"
  - the Nemotron coach's plain explanation
  - a one-tap **Trusted Contact** call (the FINRA Rule 4512 concept)

  On the attacker side, decoys **tarpit** scammers (stall tactics, a scammer-minutes-burned counter), so time is used against both ends of the scam.
- **Beats:** everything that slips past detection, because it doesn't need to detect anything, only a risky moment. Even a perfect, never-seen scam dies if the victim waits a few hours and talks to her daughter.
- **Failsafe:**
  - The customer is never trapped: release after cooling-off, or immediately via Trusted Contact confirmation (dual control), or via PNC Payment Control.
  - Legit urgent payments (rent, medical) have an allowlist and pre-approved payees.
  - Hold reasons are always shown; no black box.
- **Build** (about 30 min): hold state machine (`held → released | cancelled`), countdown UI, Trusted Contact (simulated call or text), persona stall tactics, and the burn counter.

## POWER: Meet the attacker first (deception, BUILT)

- **Power alone:** decoy personas on dormant lines are reply-only and synthetic. Scammers reach them *before* most real victims. They learn the play (feeds Mind), extract cash-out rails (feeds Reality), hand over canaries (feeds Reality), stall (feeds Time) and map numbers (feeds Space's campaign view).
  - The decoys are **the intelligence source no defender-only system has**.
- **Beats:** the information gap. Every other system learns *after* victims lose money.
- **Failsafe:**
  - If scammers spot and avoid decoys: **customer reports** and **consented rescue verdicts** feed the same story map, so the system keeps learning from the protection side.
  - Burned decoy numbers rotate.
  - Corroboration rules mean one poisoned session can't hurt anyone (two independent decoy lines are needed).
  - The content-safety guard stops a decoy from ever saying something harmful.
- **Build:** done. Add stall tactics (Time) and canary handoff (Reality).

---

## The Gauntlet: how they bind (and why there's no way around it)

**1. Fusion rule (defense in depth, the "two-person rule" from security).**
- **Any single stone can only *warn*.** A money **hold** needs **two independent stones** to agree.
- Example: Reality (tripwire) + anything, or Space (risk token) + Time conditions (new payee, risky rail), or Soul (failed safe word) + Reality's payment risk.
- So one stone's false positive never costs a customer anything, and one stone's blind spot is always covered by another.

**2. Coverage matrix. Each row is a way a scammer might try to get around one stone; ✓ means that stone still catches the scam.**

| Scammer's move | Soul | Mind | Space | Reality | Time | Power |
|---|---|---|---|---|---|---|
| New phone number every time | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Brand-new script never seen | ✓ |  | ✓ | ✓ | ✓ |  |
| Voice call, no text at all | ✓ (safe word) |  | ✓ (call in progress) | ✓ | ✓ |  |
| WhatsApp / iMessage (carrier blind) | ✓ | ✓ (on device) |  | ✓ | ✓ |  |
| Fresh mule account | ✓ | ✓ | ✓ |  | ✓ | ✓ (canary exposes it) |
| Spoofs a registered sender | ✓ (no signature) | ✓ |  | ✓ | ✓ |  |
| AI voice clone of the grandson | ✓ (safe word) |  | ✓ | ✓ | ✓ |  |
| Avoids decoys entirely | ✓ | ✓ (reports) | ✓ | ✓ | ✓ |  |

**Every row has at least three ✓.** That's the "no way around it" claim, shown as a table judges can read.

**3. Privacy binding.**
- The stones talk to each other only through **content-free, consented, expiring tokens** and **k-anonymity lookups**.
- Message text never leaves the phone without consent.
- The bank never sees texts, and the carrier never sees payees.
- Corroborated intel exports as **STIX 2.1 with a TLP:AMBER** marking for industry sharing (the FS-ISAC model).

**4. Global failsafes.**
- Every stone runs in a labeled offline or mock mode.
- Every decision shows its reasons.
- Every learned skill can be rolled back.
- Every hold can be released.
- An audit log records every action.

## The demo (one continuous story, about 2 minutes)

1. **Power:** a judge plays the scammer. The decoy stalls (Time) and hands over a canary card (Reality). The play is learned, and phones get the skill (Mind).
2. **Linda's phone:**
   - The real Lakeview text shows **Verified ✓** (Soul).
   - The fake "Lakeview fraud dept" text shows **not verified** and a **story warning** (Mind).
   - "Grandma it's Jake" triggers the **safe-word prompt** (Soul).
3. **Space:** the toggle "on a call with an unknown number" raises a risk token, with the token JSON on screen and no content in it.
4. **PNC:** Linda tries to Zelle $3,000. Space and Reality's payment risk (risk token + new payee + risky rail) agree, so the payment is **HELD** (Time). The countdown starts, the Low Cash Mode what-if runs, the Nemotron coach explains, and the Trusted Contact button is ready.
5. **The canary fires:** the scammer tried the decoy's card, and his mule account is now tripwired (Reality), with a k-anonymity lookup shown on screen.
6. The coverage matrix appears as the closing visual: six unrelated stones.

## Build order after P0

1. **Time** (hold machine): everything else plugs into it.
2. **Reality** (tripwires, pay check, canaries, k-anonymity range).
3. **Space** (signals, toggles, token, burst).
4. **Soul** (signatures, safe word).
5. The **Gauntlet** fusion rule and the coverage-matrix panel.
6. Polish.

Mind and Power are already built.

## Honesty rules

- Carrier signals, card authorizations, payout accounts, Trusted Contact calls and business signing keys are **simulated**, and labeled as such in the UI.
- Canary values come from reserved synthetic ranges.
- Never claim the coverage matrix is measured. It is a design property; the benchmark measures Mind and Reality.
- If asked, "first AI honeypot" is false (Apate.ai exists). Our claim is **six unrelated defenses fused across carrier and bank**.

## Vocabulary (so the team can say it right)

| Term | Means |
|---|---|
| Authentication vs detection | Proving the real is real vs. guessing what's fake |
| Digital signature | Math proof a message came from the key holder; can't be forged |
| Out-of-band verification | Check through a different channel (call the number you already have) |
| Content-agnostic signal | Uses metadata (who, when, how), never the words |
| CAMARA / Open Gateway | Telecom industry APIs banks call (SIM swap, call forwarding, scam signal) |
| Money mule | Account that receives scam money |
| Canary token | Fake secret that raises an alarm when used |
| k-anonymity lookup | Ask about a bucket so the other side can't tell what you asked |
| Hot state | Panic state where people make bad decisions; time cools it |
| Dual control / two-person rule | Two independent parties must agree before a risky action |
| Defense in depth | Many independent layers, so no single failure is fatal |
| Deception / honeypot / tarpit | Fake targets that learn from, and waste the time of, attackers |
