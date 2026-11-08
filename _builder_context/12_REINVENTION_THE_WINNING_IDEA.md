# 12 · The reinvention: what makes Detour different from every other team (READ THIS BEFORE 08)

Mog's concern at 6:14 AM was right. Most teams will connect "scam detector" (T-Mobile) with "budget dashboard" (PNC) in the most obvious way, and AI scam-baiting already exists commercially. This file is the differentiated version. It **extends** what is built and replaces nothing.

## Honest market check

- **AI honeypots / scam-baiting already exist.**
  - **Apate.ai** (Australia) runs about 200,000 AI "victim" personas on calls and chats.
  - Its bots handled 600,000 scam calls for the telco TPG in six weeks.
  - It harvests crypto wallets and mule-account marketplaces, and sells that intel to banks. It raised about A$11M and works with CommBank.
  - O2's "AI Granny" (UK) was a publicity version.
  - **So never claim "first AI honeypot."** Say "Apate proved decoys work at scale in Australia."
- **Their gap:** the intel goes into bank data feeds. Their bots "waste time and gather intelligence" and don't stop the scam at the moment it happens. Nothing ties the decoy intel, the customer's phone and the customer's payment into one loop, in real time.
- **What other countries already do that the US doesn't:**
  - **Australia, CBA × Telstra "scam indicator"** (live since Oct 2023): the carrier tells the bank when a customer is **on a phone call while transferring money**, a classic sign of a live scam.
  - **Spain and the UK, Telefónica Open Gateway "Scam Signal"** (a CAMARA network API, consent-based, metadata only): the bank's fraud system asks the carrier "is this user in unusual network activity right now?" when a payment starts.
  - **GSMA CAMARA APIs** banks already call: **SIM Swap**, **Call Forwarding Signal**, Number Verification.
  - **CBA NameCheck / UK Confirmation of Payee:** check the payee before money moves. NameCheck stopped 10,000+ scam payments worth A$38M+.
  - **India (RBI/I4C):** AI mule-account detection.
- **In the US, no carrier sends a live scam-in-progress signal to a bank.** T-Mobile is a carrier and PNC is a bank, and they are both sponsors in this room. That is the opening.

## The idea in one line

**Detour is a carrier–bank scam fusion center, fed by AI decoys. It stops a scam at three chokepoints: the message, the moment, and the money.**

A scam has a kill chain (cybersecurity term): contact → pressure → payment. Everyone else defends one link. Detour defends all three with one shared intelligence source.

| Chokepoint | Who | What Detour does | Status |
|---|---|---|---|
| **1. The message** (contact) | T-Mobile phone | The on-device few-KB skill catches the *story* from a new number. Consent-gated Nemotron rescue teaches every phone. | BUILT |
| **2. The moment** (pressure) | T-Mobile → PNC | **Scam-in-progress signal.** When the phone warns, or (simulated) the customer is on a call with an unknown or scam-linked number, the carrier issues a **consented, content-free risk token** to the bank: `{risk:"high", play:"grandchild_bail", since:"6 min", basis:"on-device warn"}`. It contains no message text and no numbers. This is the US version of Australia's Telstra–CBA indicator and Spain's Scam Signal. | NEW (M2) |
| **3. The money** (payment) | PNC | **Cash-out tripwires.** The decoys pull out *where the scammer wants the money to go*: Zelle handles (phone or email), crypto wallet addresses, gift-card brands, wire or mule account names, courier pickup. These are regex-derived from raw text, like the phone numbers, so the model can't invent them. They become **payee tripwires** that PNC checks when a payment starts, even if the scam reached her by voice call or WhatsApp and her phone never saw a text. | NEW (M1) |
| **Intervention** | PNC 360° navigator + Nemotron coach | When a payment hits a tripwire or a risk token: **hold it** (a cooling-off period, not a block). Show her own numbers ("this triggers Low Cash Mode; you'd be overdrawn 50 of 60 days"). The Nemotron coach explains the play in plain words. One tap calls her **Trusted Contact** (a real US concept: FINRA Rule 4512 trusted contact person for elder protection). She stays in control and can release the hold after the cooling-off. | NEW (M3) |

**Why this is novel (the polymathic synthesis):**
- **Deception technology** (cyber honeypots) feeds **threat-intelligence fusion** (indicators shared across organizations).
- The **kill chain** applied to consumer fraud means three chokepoints, not one.
- **Pyramid of Pain**: target the scam's *story* and *cash-out rails*, which are hard to change, not its phone numbers, which are cheap to change.
- Ideas from **Australia** (telco-to-bank signal), **Spain** (Scam Signal API), the **UK** (Confirmation of Payee) and **elder-finance regulation** (Trusted Contact), with **privacy by design**: tokens instead of content, everything consent-gated.
- Nobody else at this hackathon will have the carrier and the bank talking to each other, with the scammers themselves supplying the intel.

## How each sponsor sees it

- **T-Mobile:**
  - A new product, a **network-intelligence service**, the kind T-Mobile could sell to banks the way Telstra does with CBA.
  - It reaches messages the network can't see (WhatsApp, iMessage, voice calls), because the money chokepoint catches those scams anyway.
  - Privacy by design: on-device matching, consent, content-free tokens.
- **NVIDIA:**
  - Nemotron agents with clear jobs: decoy persona (adapts in context), extractor (story + cash-out IOCs), rescue investigator (tools), skill forge (teaches phones), payment-intercept coach (tools over the finance engine). Plus the safety guard, and embeddings for story memory.
  - A multi-agent system working across **two organizations**, with rules enforcing every irreversible action.
- **PNC:**
  - The 360° navigator gets something no budgeting app has: **inbound threat awareness at the moment of payment**.
  - The what-if simulator runs **automatically on the pending payment** (pre-payment simulation).
  - Scam Exposure becomes actionable: lock savings, a payment hold, the Trusted Contact.
  - It speaks PNC's language: Low Cash Mode, Extra Time, Money Bar, Payment Control, Zelle guidance.

## Demo storyline (the one flow judges will remember)

1. The decoy (or a judge playing the scammer) gets "Grandma it's Jake, I'm in jail, send $3,000 bail via Zelle to bail.desk@… / (469) 555-0188." The extractor pulls the story and the **cash-out rail** (Zelle handle). After corroboration, the rail becomes a tripwire.
2. Linda's phone gets the same play from a new number → on-device warn. The carrier issues a **risk token** to PNC (show the token on screen: no content, just risk and play).
3. Linda opens PNC anyway and tries to Zelle $3,000 to that handle. Then she tries a different handle the scammer gave her by voice, which matches no tripwire, but the risk token is still active.
   - **PNC holds the payment.** It runs the what-if automatically ("overdrawn 50 of 60 days, triggers Low Cash Mode"), and the Nemotron coach explains the grandchild play.
   - **[Call Trusted Contact: Maria (daughter)]**
   - **[Release after 24h cooling-off]**
4. The NVIDIA lens shows every agent and tool call across both companies. The scoreboard shows scams stopped at each chokepoint.

## Build plan (fits by 9:45, because it extends existing code)

- **M1 Cash-out IOCs.**
  - `core.py`: add `payment_destinations(text)`, regex-derived like `phones()`. It finds:
    - Zelle or Venmo handles (email or phone next to a rail word)
    - BTC, ETH and USDT addresses (bech32 `bc1…`, base58 `1…`/`3…`, `0x` + 40 hex)
    - gift-card brand plus "card"
    - "wire to … account"
    - a courier or cash pickup
  - Store them on the story with a status (watch / tripwire after corroboration / allowlist-protected). Show them in the story map.
  - JS parity is not needed: this runs server-side on the decoy and bank side, not on the phone.
- **M2 Risk token.**
  - `engine.ondevice()` already receives phone verdicts. On a `warn` for a payment-type play, mint a token: `{token_id, risk, play_category, issued_at, expires_in: 2h, basis}`, bound to a demo customer id with a consent flag.
  - Add a "simulate: on a call with an unknown number" toggle on the phone panel, labeled simulated.
  - Endpoints:
    - `GET /api/carrier/signal?customer=linda` (the bank pulls the token, CAMARA-style)
    - `POST /api/carrier/consent`
  - Show the token JSON in the UI so judges can see that no message content travels.
- **M3 Payment intercept.**
  - Add `POST /api/pnc/pay {to, amount, rail, from}` → the decision engine (rules, not the model): tripwire match, active risk token, or amount over Scam Exposure, which leads to a HOLD with reasons. Otherwise the payment is released.
  - On a hold: run the what-if automatically on the pending payment, call the Nemotron coach with the reasons (tools: get_story_public, run_whatif, get_indicators), and offer the Trusted Contact and the cooling-off release.
  - Add a "Send money" panel in the PNC lens with Zelle and wire forms, prefilled with the scam handle for the demo.
- Tests: tripwire regex tests, a token expiry test, pay-decision tests (hold vs release), and a legit-payment test: paying the real electric bill or a known payee must be released.
- All of this has labeled mock stand-ins. "Simulated carrier API (modeled on CAMARA Scam Signal / Telstra–CBA)" appears in the UI.

## Risks and guardrails

- **False holds on legitimate payments.** Hold only when a tripwire matches, or when a risk token AND a new payee AND (rail = Zelle, wire or crypto) are all true. Never block outright: always a cooling-off plus a release path. Allowlisted billers are never held.
- **Privacy.** A token carries no content, has a 2-hour expiry and needs consent. Say "content-free risk token" in the UI.
- **Honesty.** The carrier API, the call-state signal and the Trusted Contact call are simulated, and the UI and docs say so. The pattern is real (Australia, Spain, UK).

## Sources

- [Apate.ai: 600,000 scam calls, wallets and mule intel (Cointelegraph)](https://cointelegraph.com/magazine/fake-ai-victims-are-scam-baiting-600000-fraudsters-every-month)
- [CommBank × Apate.ai](https://www.commbank.com.au/articles/newsroom/2025/06/apate-ai.html)
- [CBA–Telstra scam indicator switched on (iTnews)](https://www.itnews.com.au/news/cba-and-telstra-scam-indicator-feature-officially-switched-on-601754)
- [Telefónica Open Gateway Scam Signal API](https://opengateway.telefonica.com/en/apis/scam-signal)
- [CAMARA Call Forwarding Signal](https://lf-camaraproject.atlassian.net/wiki/spaces/CAM/pages/81100986)
- [GSMA Open Gateway: account takeover protection](https://www.gsma.com/solutions-and-impact/gsma-open-gateway/?p=41623)
- [Dutch banks: a busy phone signals fraud (DutchNews)](https://www.dutchnews.nl/2025/02/busy-phone-could-indicate-fraudsters-are-busy-too-say-banks)
- [I4C × RBIH AI mule detection (India)](https://www.policyedge.in/p/i4c-and-rbih-partner-to-use-ai-for-detecting-mule-accounts-and-financial-fraud)
