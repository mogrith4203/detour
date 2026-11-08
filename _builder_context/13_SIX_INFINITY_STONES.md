# 13 · The six Infinity Stones: real security techniques that make Detour unlike anything else

Mog's framing: honeypot bots are one stone (Power). Find the other five: niche, real, powerful, and **buildable today**. Each stone below has:
- the real-world origin (so judges who know security nod)
- what it does in Detour
- the build
- the demo moment
- which sponsor it wins

Two stones (1 and 2) are built; four are new. **Effort estimates assume the existing codebase.** The order to build is at the bottom.

---

## 1. Power Stone: Deception personas (honeypots), BUILT

- **Origin:** deception technology and honeypots (Cliff Stoll's *The Cuckoo's Egg*, the Honeynet Project, enterprise deception platforms). Apate.ai runs this at scale for scam calls in Australia.
- **In Detour:** Nemotron decoy personas on dormant decoy lines. They are reply-only, synthetic and in-character, and they extract the scam's *story*.
- **Wins:** NVIDIA (agents), T-Mobile.

## 2. Mind Stone: Adversary-in-the-loop distillation, BUILT

- **Origin:** knowledge distillation, plus the Pyramid of Pain (David Bianco). Target what's expensive for the attacker to change (their story, their tactics), not what's cheap (phone numbers).
- **In Detour:** Nemotron turns each attack into a few-KB on-device skill. Every lesson passes 4 regression checks and can be rolled back. The network learns once, then every phone knows.
- **Wins:** NVIDIA, T-Mobile.

## 3. Reality Stone: Canary tokens planted in the scammer's hands (NEW, about 45 min). **The jaw-drop stone**

- **Origin:** honeytokens and **Canarytokens** (Thinkst). These are fake credentials that do nothing except raise an alarm when someone uses them. Attackers can't tell them from real ones.
- **In Detour:**
  - When a scammer asks a decoy for a card number, bank login, Zelle email or SSN, the decoy hands over a **canary**. It's a unique fake value minted for *that* conversation:
    - a Luhn-valid card number from a reserved fake BIN
    - a fake account number "ending 7731"
    - a unique Zelle-style email `linda.park.7731@decoy-mail.example`
  - Each canary is registered with the session, the story and a timestamp.
  - **When the scammer tries to use it**, PNC's (simulated) card authorization or login sees the canary and fires. That gives:
    - **proof of attribution:** this exact conversation, this play
    - **mule capture:** the destination account, device or merchant the scammer used becomes a tripwire (stone 6) and a node in the campaign graph (stone 4)
  - The scammer turned the decoy into a trap for themselves.
- **Build:**
  - `core.py`: `mint_canary(kind, session_id)` with a Luhn generator. Fake BIN prefix `400000` + a 2-digit tag. Never a real issuer range in production terms; label it "synthetic".
  - Registry dict, persisted with the SQLite work if X1 is done.
  - The persona prompt and mock: when asked for card or account details, reveal the canary (in character: "let me find my card... it's 4000 0012 ...").
  - Endpoint `POST /api/pnc/card_auth {card, merchant, amount, device_id, payout_account}`. If the card is a canary: return `{fired: true, session, story, minted_at, payout_account → tripwire}`.
  - UI button on the PNC lens: "Simulate: scammer tries to cash out the decoy's card".
  - Event `Canary fired` on the agent graph.
- **Demo moment:** "14 minutes ago Linda's decoy gave the scammer a card. He just tried to use it at a gift-card site. That alarm points straight at his payout account, which is now on every PNC tripwire." Judges have never seen a scam-baiting demo that *catches the scammer's money mule*.
- **Wins:** PNC (mule detection, fraud intelligence), T-Mobile, the overall security wow.

## 4. Space Stone: Infrastructure pivoting, the campaign graph (NEW, about 60 min)

- **Origin:** threat-intel **pivoting** (Maltego, VirusTotal graph). Link phone numbers, domains, wallets and payout accounts that appear together, and one scam turns into a whole ring. Also **campaign attribution**.
- **In Detour:**
  - Every indicator (callback numbers, domains, cash-out handles and wallets, canary payout accounts, sender numbers) is a node. A shared appearance in a session or story is an edge.
  - **Union-find clustering** groups them into **campaigns**: "Ring #2: 3 plays (toll, parcel, bank), 7 numbers, 2 domains, 1 Zelle mule, 1 USDT wallet."
  - Optional: Nemotron embeddings of story claims add "same script" edges (stylometry-lite). Label these as similarity, not proof.
- **Build:**
  - `intel.py`: `build_graph(smap, canaries)` returns `{nodes, edges, campaigns}`.
  - Endpoint `GET /api/intel/graph`.
  - UI: an inline-SVG force layout or a simple radial layout per campaign in the T-Mobile lens, behind a "Campaign view" toggle on the story map. Clicking a node shows where it appeared.
- **Demo moment:** "Three different scams, seven different numbers, one ring. The canary showed us its bank account."
- **Wins:** T-Mobile (network-level view), NVIDIA (embeddings), PNC.

## 5. Time Stone: Tarpit the scammer, cool down the victim (NEW, about 30 min)

- **Origin:** **tarpits** (LaBrea tarpit, SMTP tarpitting). Deliberately waste an attacker's time and resources. **Cost imposition** is a core active-defense doctrine.
  - Paired with **cooling-off periods** from consumer protection.
  - **"Hot state"** decision psychology: scams work by forcing a rushed decision, so time is the antidote.
- **In Detour:** time is used as a weapon in both directions.
  - **Against the scammer:** decoy personas run a *stall strategy*. "Hold on dear, my reading glasses...", "the bank app is asking me something", a slow, believable trickle that keeps them engaged and away from real victims. The system tracks **scammer-minutes burned** with simulated human-paced timestamps.
  - **For the victim:** the PNC payment hold (stone 6 / M3) is a **time lock**. The money is held for a cooling-off period with a visible countdown and release path, so the victim gets out of the "hot state". This is like PNC's own "Extra Time" in Low Cash Mode, applied to scams.
- **Build:**
  - The persona prompt gains a stall-tactics list; the mock uses rotating stall lines.
  - The engine sums simulated scammer time per session.
  - A header counter: "Scammer time burned: 3h 12m".
  - A hold countdown on the PNC payment.
- **Demo moment:** "Every minute he spends on our decoy is a minute he's not on a real grandmother."
- **Wins:** T-Mobile (customer protection), PNC.

## 6. Soul Stone: Trust without seeing (privacy-preserving intel sharing) (NEW, about 45 min)

- **Origin:** three real techniques.
  - **k-anonymity hash-prefix lookups**, the technique behind Have I Been Pwned's Pwned Passwords range API.
  - **Private set intersection**, which Google Password Checkup uses so neither side reveals its list.
  - **STIX 2.1 / TLP**, the OASIS standard format and Traffic Light Protocol for sharing threat intel, used by FS-ISAC, the financial-sector ISAC.
- **In Detour:** the carrier and the bank share scam intelligence **without either seeing the other's customers**.
  - **The carrier→bank risk token** (M2 in 12) is content-free: risk, play category, issue time, expiry. No text and no numbers.
  - **Tripwire lookups via a k-anonymity range query.** PNC hashes the payee (SHA-256 of the normalized handle) and sends only the **first 5 hex characters**. The carrier returns every tripwire hash suffix in that bucket, and PNC matches locally. **The carrier never learns who Linda is paying**, and PNC only learns tripwires near its own query.
  - **STIX 2.1 export** of corroborated stories, campaigns and indicators, marked `TLP:AMBER`, ready for FS-ISAC-style sharing between banks and carriers. Never includes customer data.
- **Build:**
  - `intel.py`: `range_bucket(prefix5)`.
  - Endpoint `GET /api/intel/range/{prefix}`. The PNC pay path uses it, and the UI shows "PNC sent: `3fa9c`, nothing else."
  - `GET /api/intel/stix` returns a STIX 2.1 bundle with `indicator`, `campaign`, `threat-actor` (pseudonymous ring) and `relationship` objects plus a TLP marking. Validate the shape with a test; the spec's required fields are `type`, `spec_version`, `id`, `created` and `modified`.
- **Demo moment:** "PNC just checked this payee against T-Mobile's scam intel. Here is everything PNC sent: five characters. T-Mobile still doesn't know who Linda was paying."
- **Wins:** T-Mobile (privacy by design), PNC (compliance), NVIDIA (production realism).

---

## The gauntlet: all six in one demo flow (about 2 minutes)

1. **Power:** a judge plays the scammer and the decoy stalls (**Time**), burning their minutes.
2. The scammer asks for Grandma's card, and the decoy hands over a **canary** (**Reality**).
3. The extractor pulls the story and cash-out rails, and the campaign graph links them to an existing ring (**Space**).
4. The **Mind** skill reaches every phone. Linda's phone warns on the same play from a new number.
5. The carrier→bank **risk token** goes out, and the tripwire check runs over the **k-anonymity range** (**Soul**).
6. Linda tries to Zelle $3,000. PNC **holds** it (Time lock): the what-if shows Low Cash Mode, the Nemotron coach explains, and a button calls her Trusted Contact.
7. **Canary fires:** "the scammer just tried to use the decoy's card; his payout account is now a tripwire at every bank in the share."

Closing line: **"Every other scam tool waits to be attacked. Ours turns the attack itself into the trap."**

## Build order (after P0), with honesty rules

1. M1 tripwires + M2 risk token + M3 payment hold (12): these are the base the stones plug into.
2. **Reality (canaries)**: highest wow per minute.
3. **Soul (range lookup + token display + STIX)**.
4. **Time (stall strategy + burn counter + hold countdown)**.
5. **Space (campaign graph)**.

Honesty rules:
- Canaries, card authorizations, payout accounts, the carrier API and the ISAC sharing are all **simulated**, and the UI says so.
- Canary values must be clearly synthetic (a reserved fake BIN, `.example` domains), never anything that could collide with a real card or person.
- Embedding similarity is described as "similar script", never as proof.
- Every stone has a mock stand-in and tests.

## Vocabulary for the team (to say it right)

| Term | Means |
|---|---|
| Deception technology / honeypot | Fake targets that attract attackers and record what they do |
| Honeytoken / canary token | Fake secret that raises an alarm when used |
| Pyramid of Pain | Hit what's hard for attackers to change (behavior), not what's easy (numbers) |
| Kill chain | The steps of an attack; break any link and the attack fails |
| Pivoting | Following shared clues from one indicator to the whole attacker setup |
| IOC (indicator of compromise) | A clue: number, domain, wallet, account |
| Tarpit | Deliberately slowing an attacker to waste their time |
| Cost imposition | Making attacks expensive for the attacker |
| k-anonymity range query | Asking about a hash bucket so the other side can't tell which item you meant |
| STIX / TLP | Standard format and sharing labels for threat intel |
| ISAC | Industry group that shares threat intel (FS-ISAC for banks) |
| Money mule | Account that receives and moves scam money |
