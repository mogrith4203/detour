# 16 · Echo / PNC / Carrier API contract (backend ↔ UI). Written 6:55 AM by the lead builder.

All responses are JSON. Every simulated party is labeled in its payload with `"simulated": true`; the UI must show a
"SIMULATED" tag next to Echo delivery, carrier signals, PNC rails, canary cards and business endpoints.
Every model-backed response carries `"mode": "live" | "replay" | "mock"`; show that badge honestly.

## Phone side (browser only, never sent)
- `static/resolver.js` exposes `DetourResolver.CONTACTS` (Linda's contacts) and
  `DetourResolver.resolveClaim(claim, contacts, sender)` →
  `{match: "contact"|"business"|"none", contact_id, name, relation, number_hash, business_id, from_real_number}`.
  Python twin: `detour/resolver.py` (parity-tested). `number_hash` = first 16 hex of sha256(digits-only number).
- `DetourResolver.msgHash(text)` → sha256 hex of the normalized text (async, WebCrypto). Businesses only see this.

## Echo
- `POST /api/echo/claim {text, sender}` → `{claim:{claims_identity, kind, name, relation, business, money_ask, confidence}, mode, ms}`
- `POST /api/echo/start {customer:"linda", consented:true, target_kind:"contact"|"business", number_hash, business_id,
   msg_hash, claim_kind, relation, money_ask, sender}`
  → `{echo_id, status:"pending"|"answered"|"skipped"|"rate_limited", reason, target_label, trust, answer, outcome, simulated:true}`
  Business targets answer immediately (provenance by hash). Contacts go to the target's inbox.
  Echo payload stored server-side is printed back as `payload` (content-free; the UI can show it as JSON).
- `GET /api/echo/inbox?who=jake` → `{items:[{echo_id, prompt, asked_at}]}` (prompt has NO message content)
- `POST /api/echo/answer {echo_id, answer:"not_me"|"yes"}` → full echo record (below)
- `POST /api/echo/timeout {echo_id}` → record with `status:"no_answer"` and `fallback:[...]` steps (safe word, cooling-off, story check)
- `GET /api/echo/status?echo_id=` → record
- Record: `{echo_id, status, answer, trusted:bool, trust_reasons:[...], target_label, payload, outcome:{label, diverted, tripwires:[...],
   payments:[...], skill:{promoted, version, bytes}, message}, fallback, simulated:true}`
- `GET /api/echo/list` → `{items:[record...]}` (newest first)

## Decoy thread (after "Not me")
- `POST /api/echo/decoy_say {echo_id, text}` → `{reply, mode, canary:{token,last4,...}|null, tactic, time_burned_s, tripwires:[...]}`

## Carrier (simulated CAMARA-style)
- `GET /api/carrier/signals` → `{jake:{sim_swap, call_forwarding}, linda:{unknown_call}, simulated:true}`
- `POST /api/carrier/signals {who, sim_swap?, call_forwarding?, unknown_call?}` → same
- `GET /api/carrier/token?who=linda` → content-free risk token JSON

## PNC (simulated rails)
- `POST /api/pnc/pay {to_handle, amount, memo, linked_sender}` → payment
- `GET /api/pnc/payments` → `{items:[payment...]}`
- `POST /api/pnc/release {payment_id, by:"customer"|"trusted_contact"}` → payment
- Payment: `{id, to_handle, amount, memo, status:"sent"|"held"|"cancelled"|"released", hold_until (epoch s), signals:[{name, weight, detail}],
   decision_reasons:[...], whatif:{facts:[...]}, simulated:true}`
- `GET /api/pnc/tripwires` → `{items:[{account, source, at}]}`
- `POST /api/pnc/card_auth {token, merchant, payout_account}` → `{fired, attribution, tripwired, simulated:true}`
- `GET /api/pnc/kanon?account=` → `{prefix_sent:"abcde", chars_sent:5, matches_in_range:N, hit:bool}`

## Gauntlet
- `GET /api/gauntlet?payment_id=` → `{signals:[...], independent:N, action:"warn"|"hold"|"cancel"|"allow", rule}`
  Rule: one signal can only warn; HOLD needs ≥2 independent signal families; Echo denial is one family with the top weight.
