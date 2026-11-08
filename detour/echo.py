"""Identity Echo + the supporting defenses (Time, Reality, Space) and the 2-signal gauntlet.

"Every scam pretends to be someone. We ask that someone."

Everything here that stands in for a real party is SIMULATED and labeled: Echo delivery to the real person,
carrier (CAMARA-style) signals, PNC payment rails, canary cards and business provenance endpoints.

Privacy invariants (tested):
- An Echo payload never contains message content: only claim fields, a number hash, a message hash, and an ask type.
- The customer's contacts never reach the server: the phone resolves the claim and sends one number hash.
- Businesses only ever see a message hash.
"""
import copy
import hashlib
import json
import re
import time
import uuid

from .claims import extract_claim
from .core import gate, redact
from .resolver import BUSINESSES, msg_hash

# ---------------------------------------------------------------- simulated parties
# Carrier subscriber directory: number hash -> subscriber. The carrier, not the phone, knows who the hash is.
SUBSCRIBERS = {
    hashlib.sha256(b"2145550130").hexdigest()[:16]: {"who": "jake", "label": "Jake", "number": "(214) 555-0130"},
    hashlib.sha256(b"2145550131").hexdigest()[:16]: {"who": "mia", "label": "Mia", "number": "(214) 555-0131"},
    hashlib.sha256(b"4695550132").hexdigest()[:16]: {"who": "ruth", "label": "Ruth", "number": "(469) 555-0132"},
    hashlib.sha256(b"9725550133").hexdigest()[:16]: {"who": "tom", "label": "Tom", "number": "(972) 555-0133"},
}
# Messages each verified business really sent (they keep hashes of their own outbound texts).
BUSINESS_SENT = {
    "lakeview": {msg_hash("Lakeview Credit Union: a $980 charge was flagged. Open the Lakeview app to review it. "
                          "We will never ask for your PIN.")},
    "parcelpost": set(),
    "txtoll": set(),
}
CONSENTED = {"linda"}  # customers who turned Echo on

ECHO_PER_CUSTOMER = 6      # per 10 minutes
ECHO_PENDING_PER_TARGET = 2
ECHO_WINDOW_S = 600
HOLD_SECONDS = 30 * 60     # cooling-off hold
BIG_PAYMENT = 1000.0

CARD_ASK = re.compile(r"\b(card|credit|debit|number on the|cvv|expir|routing|account number|gift ?card|pay ?ment|zelle|"
                      r"send (it|the money|money)|wire|venmo|cash ?app)\b", re.I)
HANDLE_RE = re.compile(r"(?:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})|(?:\$[A-Za-z][A-Za-z0-9_]{2,20})|"
                       r"(?:@[A-Za-z][A-Za-z0-9_.]{2,30})")
PHONE_RE = re.compile(r"\(?\b(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b")
STALL_TACTICS = ["asks to repeat", "slow typing", "needs reading glasses", "bank app won't open", "asks for spelling"]


def _now():
    return time.time()


def _norm_phone(m):
    return f"({m.group(1)}) {m.group(2)}-{m.group(3)}"


def extract_rails(text):
    """Cash-out rails a scammer names: handles, emails, cashtags, phone numbers. Regex-derived, never model-invented."""
    t = text or ""
    out = [h.lower() for h in HANDLE_RE.findall(t)]
    out += [_norm_phone(m) for m in PHONE_RE.finditer(t)]
    seen, res = set(), []
    for r in out:
        if r not in seen:
            seen.add(r)
            res.append(r)
    return res[:6]


def acct_hash(account):
    return hashlib.sha256((account or "").strip().lower().encode()).hexdigest()


class Defense:
    """Echo service + carrier + PNC rails + gauntlet, bound to one Engine (for events, LLM, story map)."""

    def __init__(self, engine):
        self.engine = engine
        self.reset()

    def reset(self):
        self.echoes = {}
        self.history = []          # (customer, t)
        self.carrier = {"jake": {"sim_swap": False, "call_forwarding": False},
                        "linda": {"unknown_call": False}}
        self.payments = {}
        self.tripwires = {}        # account -> {source, at}
        self.canaries = {}         # token -> {echo_id, last4, ...}
        self.denied_senders = {}   # sender -> echo_id
        self.confirmed_senders = {}
        self.claim_texts = {}      # sender -> redacted texts the customer sent for claim extraction (consented, short-lived)

    # ------------------------------------------------------------ helpers
    def emit(self, agent, stage, **kw):
        self.engine.emit(agent, stage, **kw)

    @property
    def llm(self):
        return self.engine.llm

    # ------------------------------------------------------------ claim extraction (Nemotron)
    def claim(self, text, sender=""):
        t0 = _now()
        red = redact(text or "", ("Linda Park", "Linda"))[:1500]
        key = (sender or "unknown")[:40]
        buf = self.claim_texts.setdefault(key, [])
        buf.append(red)
        del buf[:-4]
        self.engine._cap(self.claim_texts, 100)
        self.engine.stats["bytes_to_cloud"] += len(red.encode())
        c, mode = extract_claim(self.llm, red)
        ms = int((_now() - t0) * 1000)
        self.emit("Claim extractor", "claim", input="(redacted message)", mode=mode, ms=ms,
                  output=f"{c['kind']} · name={c['name']} · relation={c['relation']} · business={c['business']} · money_ask={c['money_ask']}")
        return {"claim": c, "mode": mode, "ms": ms}

    # ------------------------------------------------------------ carrier (simulated CAMARA-style)
    def set_signals(self, who, **flags):
        line = self.carrier.setdefault(who, {})
        for k, v in flags.items():
            if v is not None and k in ("sim_swap", "call_forwarding", "unknown_call"):
                line[k] = bool(v)
        self.emit("Carrier signals (simulated)", "signals", output=json.dumps({who: line}), mode="simulated")
        return self.signals()

    def signals(self):
        return {**copy.deepcopy(self.carrier), "simulated": True}

    def risk_token(self, who):
        """Content-free risk token the carrier can share: booleans and a timestamp, no numbers, no content."""
        line = self.carrier.get(who, {})
        return {"subject": f"customer:{who}", "issued_at": int(_now()), "issuer": "T-Mobile (simulated CAMARA-style APIs)",
                "signals": {"sim_swap_24h": bool(line.get("sim_swap")), "call_forwarding": bool(line.get("call_forwarding")),
                            "active_call_unknown_number": bool(line.get("unknown_call"))},
                "contains_message_content": False, "simulated": True}

    def trust(self, who):
        line = self.carrier.get(who, {})
        reasons = []
        if line.get("sim_swap"):
            reasons.append("SIM swapped in the last hour, so the answer may come from the scammer's SIM")
        if line.get("call_forwarding"):
            reasons.append("Call/SMS forwarding is on, so the prompt may be going somewhere else")
        return (not reasons), reasons or ["No SIM swap and no forwarding on the real line"]

    # ------------------------------------------------------------ Echo service
    def start(self, body):
        customer = str(body.get("customer") or "linda")[:20]
        kind = body.get("target_kind")
        base = {"status": "skipped", "simulated": True}
        if customer not in CONSENTED or not body.get("consented"):
            return {**base, "reason": "Echo is off for this customer (no consent)."}
        if not body.get("money_ask"):
            return {**base, "reason": "No money or risky ask, so we don't bother the real person."}
        recent = [t for c, t in self.history if c == customer and _now() - t < ECHO_WINDOW_S]
        if len(recent) >= ECHO_PER_CUSTOMER:
            self.emit("Identity Echo", "rate-limit", output=f"rate limited ({len(recent)} in 10 min)", mode="rules")
            return {**base, "status": "rate_limited", "reason": "Too many Echo checks in 10 minutes. Falling back to the safe word."}
        sender = str(body.get("sender") or "")[:40]
        payload = {"type": "identity_echo", "from_customer": customer, "claim_kind": str(body.get("claim_kind") or "")[:20],
                   "relation": (str(body.get("relation"))[:20] if body.get("relation") else None), "ask": "money",
                   "asked_at": int(_now())}
        if kind == "business":
            bid = str(body.get("business_id") or "")
            biz = next((b for b in BUSINESSES if b["id"] == bid), None)
            mh = str(body.get("msg_hash") or "")
            if not biz or not re.fullmatch(r"[0-9a-f]{16}", mh):
                return {**base, "reason": "Unknown business or bad message hash."}
            payload.update(target={"business_id": bid}, msg_hash=mh)
            rec = self._new(customer, sender, payload, biz["name"], target_who=None)
            sent = mh in BUSINESS_SENT.get(bid, set())
            self.emit("Identity Echo", "provenance", input=f"hash {mh} → {biz['name']} (simulated endpoint)",
                      output="sent by them" if sent else "NOT sent by them", mode="simulated")
            return self._answer(rec, "yes" if sent else "not_me", trusted=True,
                                trust_reasons=["Business provenance endpoint answered by hash (simulated)"])
        nh = str(body.get("number_hash") or "")
        sub = SUBSCRIBERS.get(nh)
        if not sub:
            return {**base, "reason": "That contact isn't reachable through the carrier, so we fall back to the safe word."}
        pending = [e for e in self.echoes.values() if e["target_who"] == sub["who"] and e["status"] == "pending"]
        if len(pending) >= ECHO_PENDING_PER_TARGET:
            return {**base, "status": "rate_limited", "reason": f"{sub['label']} already has open Echo prompts."}
        payload["target"] = {"number_hash": nh}
        rec = self._new(customer, sender, payload, sub["label"], target_who=sub["who"])
        self.emit("Identity Echo", "deliver", input=json.dumps(payload)[:200],
                  output=f"Asked the real {sub['label']} on their own line (simulated delivery)", mode="simulated")
        return self._public(rec)

    def _new(self, customer, sender, payload, label, target_who):
        eid = uuid.uuid4().hex[:8]
        self.history.append((customer, _now()))
        del self.history[:-200]
        rec = {"echo_id": eid, "customer": customer, "sender": sender, "payload": payload, "target_label": label,
               "target_who": target_who, "status": "pending", "answer": None, "trusted": None, "trust_reasons": [],
               "outcome": None, "fallback": None, "created": _now(), "decoy": None, "simulated": True}
        self.echoes[eid] = rec
        self.engine._cap(self.echoes, 100)
        return rec

    def _public(self, rec):
        out = {k: v for k, v in rec.items() if k not in ("decoy",)}
        if rec.get("decoy"):
            out["decoy"] = {"turns": len(rec["decoy"]["convo"]), "time_burned_s": self._burned(rec)}
        return out

    def inbox(self, who):
        items = [{"echo_id": e["echo_id"], "asked_at": int(e["created"]),
                  "prompt": "Someone texting Grandma Linda says they're you and is asking for money. Is this you?"
                  if e["payload"].get("relation") else "Someone texting Linda says they're you and is asking for money. Is this you?"}
                 for e in self.echoes.values() if e["target_who"] == who and e["status"] == "pending"]
        return {"items": items, "simulated": True}

    def status(self, eid):
        rec = self.echoes.get(eid)
        return self._public(rec) if rec else None

    def list(self):
        return {"items": [self._public(e) for e in sorted(self.echoes.values(), key=lambda e: -e["created"])]}

    def answer(self, eid, answer):
        rec = self.echoes.get(eid)
        if not rec:
            return None
        if rec["status"] != "pending":
            return self._public(rec)
        trusted, reasons = self.trust(rec["target_who"])
        return self._answer(rec, answer, trusted, reasons)

    def timeout(self, eid):
        rec = self.echoes.get(eid)
        if not rec:
            return None
        if rec["status"] == "pending":
            rec["status"] = "no_answer"
            rec["fallback"] = ["No answer is never treated as safe.",
                               "Ask the caller for your family safe word.",
                               "Any payment to them waits in a cooling-off hold.",
                               "The on-device story check keeps running on new messages."]
            self.emit("Identity Echo", "no-answer", output="no answer → safe word + cooling-off hold + story check", mode="rules")
            for p in self._linked(rec["sender"]):
                self._evaluate(p)
        return self._public(rec)

    def _answer(self, rec, answer, trusted, trust_reasons):
        rec["answer"] = "not_me" if answer == "not_me" else "yes"
        rec["trusted"] = bool(trusted)
        rec["trust_reasons"] = trust_reasons
        rec["status"] = "answered"
        who = rec["target_label"]
        self.emit("Identity Echo", "answer", output=f"{who}: {'NOT ME' if rec['answer'] == 'not_me' else 'yes, it is me'}"
                  + ("" if trusted else " · UNTRUSTED (" + "; ".join(trust_reasons) + ")"), mode="simulated")
        if not trusted:
            rec["outcome"] = {"label": None, "message": f"{who}'s answer can't be trusted right now: " + "; ".join(trust_reasons)
                              + ". Nothing is released; the hold stays.", "payments": [self._pub_pay(p) for p in self._linked(rec["sender"])]}
            for p in self._linked(rec["sender"]):
                p["notes"].append(f"Echo answer from {who} was untrusted: " + "; ".join(trust_reasons))
                self._evaluate(p)
            return self._public(rec)
        if rec["answer"] == "yes":
            if rec["sender"]:
                self.confirmed_senders[rec["sender"]] = rec["echo_id"]
            released = []
            for p in self._linked(rec["sender"]):
                if p["status"] == "held":
                    p["status"] = "released"
                    p["decision_reasons"].append(f"Released: the real {who} confirmed on a trusted line.")
                    released.append(self._pub_pay(p))
            rec["outcome"] = {"label": "confirmed", "message": f"✓ Confirmed by {who}", "payments": released}
            return self._public(rec)
        rec["outcome"] = self._on_denial(rec)
        return self._public(rec)

    # ------------------------------------------------------------ outcomes of a denial
    def _on_denial(self, rec):
        who = rec["target_label"]
        sender = rec["sender"]
        is_business = "business_id" in rec["payload"].get("target", {})
        self.emit("Ground-truth label", "label", output=f"SCAM (ground truth: the real {who} said 'not me')", mode="rules")
        if sender:
            self.denied_senders[sender] = rec["echo_id"]
        trips = []
        thread = list(self.claim_texts.get(sender or "unknown", []))
        for acct in ([sender] if sender else []) + [r for t in thread for r in extract_rails(t)]:
            if acct and self._tripwire(acct, f"Echo denial {rec['echo_id']}"):
                trips.append(acct)
        skill = self._learn(thread[-1] if thread else "", "bank" if is_business else "family_emergency")
        # divert the thread to a decoy that plays Linda (the scammer never learns he was caught)
        rec["decoy"] = {"persona": "decoy-01", "convo": [{"who": "scammer", "text": t, "sender": sender} for t in thread[-3:]],
                        "diverted_at": _now(), "canary": None}
        self.emit("Honeypot persona", "divert", output=f"Thread from {sender or 'unknown'} diverted to decoy Linda (simulated)", mode="simulated")
        cancelled = []
        for p in self._linked(sender):
            self._evaluate(p)
            cancelled.append(self._pub_pay(p))
        msg = (f"{who} says they didn't send this." if is_business else f"The real {who} says this isn't him.")
        return {"label": "scam", "diverted": True, "tripwires": trips, "payments": cancelled, "skill": skill, "message": msg}

    def _learn(self, raw, category):
        """Verified label → skill forge → gate → every phone. Same gate as the consent path."""
        eng = self.engine
        story = next((s for s in eng.smap.stories.values() if s["category"] == category), None)
        if not story or not raw:
            self.emit("Skill forge", "propose", output="no matching story yet (load decoy history first)", mode="rules")
            return {"promoted": False, "version": None, "bytes": None, "reason": "No story to update yet. Load decoy history first."}
        proposal, fmeta = eng.agents.forge(raw, story)
        if fmeta.get("mode") == "nemotron":
            fmeta["mode"] = eng.llm.mode
        self.emit("Skill forge", "propose", output=", ".join(proposal["add_keywords"] + proposal["add_phrases"])[:200], **fmeta)
        with eng.lock:
            ok, results, cand = gate(story, proposal, raw, eng.gate_legit(), eng.smap.stories)
            if ok:
                story["skill"] = cand["skill"]
                story["skill"]["version"] += 1
                story["skill"]["history"].append(f"v{story['skill']['version']}: +{', '.join(proposal['add_keywords'] + proposal['add_phrases'])} (Echo ground truth)")
                eng.stats["skills_promoted"] += 1
                eng.smap.log("skill", f"{story['id']} skill v{story['skill']['version']} promoted to every phone (Echo label)")
            else:
                eng.stats["skills_rejected"] += 1
        self.emit("Gate (tests)", "gate", output=("promoted" if ok else "rejected") + " · " +
                  ", ".join(("PASS " if r["ok"] else "FAIL ") + r["test"] for r in results), mode="rules")
        size = len(json.dumps({"keywords": story["skill"]["keywords"], "phrases": story["skill"]["phrases"]}).encode())
        return {"promoted": ok, "version": story["skill"]["version"], "bytes": size, "story_id": story["id"],
                "gate": results, "mode": fmeta.get("mode")}

    # ------------------------------------------------------------ decoy (after "not me")
    def decoy_say(self, eid, text):
        rec = self.echoes.get(eid)
        if not rec or not rec.get("decoy"):
            return {"error": "No diverted thread for that Echo."}
        d = rec["decoy"]
        if sum(1 for c in d["convo"] if c["who"] == "scammer") >= 20:
            return {"error": "Turn limit reached."}
        text = (text or "").strip()[:500]
        d["convo"].append({"who": "scammer", "text": text, "sender": rec["sender"]})
        trips = [a for a in extract_rails(text) if self._tripwire(a, f"decoy thread {eid}")]
        from .data import PERSONAS
        canary = None
        if CARD_ASK.search(text) and not d["canary"]:
            canary = self._mint_canary(eid)
            d["canary"] = canary
            reply = (f"Ok sweetie, my hands are shaking. The card number is {canary['display']}, it expires {canary['exp']}. "
                     "Is that the right one?")
            meta = {"mode": "rules", "ms": 0}
            tactic = "hands over a canary card"
            self.emit("Canary (simulated)", "mint", output=f"canary card •••• {canary['last4']} handed to the scammer", mode="simulated")
        else:
            reply, meta = self.engine.agents.persona_reply(PERSONAS[d["persona"]], d["convo"])
            if meta.get("mode") == "nemotron":
                meta["mode"] = self.llm.mode
            tactic = STALL_TACTICS[len(d["convo"]) // 2 % len(STALL_TACTICS)]
        d["convo"].append({"who": "decoy", "text": reply})
        self.emit("Honeypot persona", "reply", input=text[:160], output=reply[:200], **meta)
        return {"reply": reply, "mode": meta.get("mode"), "canary": canary, "tactic": tactic,
                "time_burned_s": self._burned(rec), "tripwires": trips}

    def _burned(self, rec):
        d = rec.get("decoy")
        return int(_now() - d["diverted_at"]) if d else 0

    def _mint_canary(self, eid):
        token = "cny_" + uuid.uuid4().hex[:10]
        last4 = str(int(hashlib.sha256(token.encode()).hexdigest()[:6], 16) % 10000).zfill(4)
        c = {"token": token, "last4": last4, "display": f"4000 0566 1234 {last4}", "exp": "09/29", "echo_id": eid,
             "fired": False, "simulated": True}
        self.canaries[token] = c
        return {k: v for k, v in c.items()}

    # ------------------------------------------------------------ PNC rails (simulated)
    def _tripwire(self, account, source):
        account = (account or "").strip().lower()
        if not account or account in self.tripwires:
            return False
        self.tripwires[account] = {"account": account, "source": source, "at": int(_now())}
        self.emit("PNC tripwire (simulated)", "tripwire", output=f"tripwired {account} ({source})", mode="simulated")
        return True

    def tripwire_list(self):
        return {"items": sorted(self.tripwires.values(), key=lambda t: -t["at"]), "simulated": True}

    def card_auth(self, token, merchant, payout):
        c = self.canaries.get(token or "")
        if not c:
            return {"fired": False, "reason": "Not a canary card.", "simulated": True}
        c["fired"] = True
        rec = self.echoes.get(c["echo_id"], {})
        tripped = self._tripwire(payout, f"canary {token} fired at {merchant}")
        attribution = {"canary": f"•••• {c['last4']}", "handed_out_in": f"decoy thread {c['echo_id']}",
                       "scammer_number": rec.get("sender"), "merchant": (merchant or "")[:60], "payout_account": (payout or "")[:80]}
        self.emit("Canary (simulated)", "fired", output=f"canary •••• {c['last4']} used at {merchant}; payout {payout} tripwired", mode="simulated")
        return {"fired": True, "declined": True, "attribution": attribution, "tripwired": bool(tripped) or (payout or "").lower() in self.tripwires,
                "simulated": True}

    def kanon(self, account):
        """k-anonymity range lookup: PNC sends 5 hex chars of the account hash, gets every tripwire hash in that range,
        and compares locally. The network never learns which account PNC asked about."""
        h = acct_hash(account)
        prefix = h[:5]
        in_range = [acct_hash(a) for a in self.tripwires if acct_hash(a).startswith(prefix)]
        return {"prefix_sent": prefix, "chars_sent": 5, "matches_in_range": len(in_range), "hit": h in in_range, "simulated": True}

    def pay(self, to_handle, amount, memo, linked_sender):
        pid = "pay_" + uuid.uuid4().hex[:6]
        p = {"id": pid, "to_handle": (to_handle or "")[:80].strip().lower(), "amount": round(float(amount), 2), "memo": (memo or "")[:80],
             "linked_sender": (linked_sender or "")[:40], "status": "sent", "created": int(_now()), "hold_until": None,
             "signals": [], "decision_reasons": [], "notes": [], "whatif": None, "rail": "Zelle (simulated)", "simulated": True}
        self.payments[pid] = p
        self.engine._cap(self.payments, 100)
        p["whatif"] = self._whatif(p["amount"])
        self._evaluate(p)
        self.emit("PNC rails (simulated)", "pay", output=f"${p['amount']:,.0f} to {p['to_handle']} → {p['status'].upper()}", mode="rules")
        return self._pub_pay(p)

    def release(self, pid, by):
        p = self.payments.get(pid)
        if not p:
            return None
        if p["status"] == "held":
            sigs = self.gauntlet(p)
            if any(s["family"] == "echo" and s["name"] == "echo_denied" for s in sigs["signals"]):
                p["decision_reasons"].append("Can't release: the real person said 'not me'.")
            elif by == "trusted_contact":
                p["status"] = "released"
                p["decision_reasons"].append("Released after Linda's Trusted Contact (Mia) reviewed it (simulated).")
            else:
                p["status"] = "released"
                p["decision_reasons"].append("Released by Linda after the cooling-off explanation.")
        return self._pub_pay(p)

    def payments_list(self):
        for p in self.payments.values():
            if p["status"] == "held" and p["hold_until"] and _now() >= p["hold_until"]:
                p["notes"].append("Cooling-off ended; still waiting for a second check before it can go.")
                p["hold_until"] = None
        return {"items": [self._pub_pay(p) for p in sorted(self.payments.values(), key=lambda p: -p["created"])], "simulated": True}

    def _pub_pay(self, p):
        return {k: v for k, v in p.items()}

    def _linked(self, sender):
        if not sender:
            return []
        return [p for p in self.payments.values() if p["linked_sender"] == sender and p["status"] in ("held", "sent")]

    def _whatif(self, amount):
        try:
            from . import finance
            res = finance.whatif(finance.load_customer(), [{"type": "payment", "amount": amount, "from": "checking",
                                                            "date": time.strftime("%Y-%m-%d", time.localtime(_now() + 86400))}])
            facts = res.get("facts", [])[:3]
        except Exception:
            facts = []
        return {"title": "Low Cash Mode what-if", "facts": facts, "mode": "rules"}

    # ------------------------------------------------------------ gauntlet
    def gauntlet(self, p):
        """One signal can only warn. HOLD needs two independent signal families. Echo denial is the strongest."""
        sigs = []
        s = p["linked_sender"]
        if s and s in self.denied_senders:
            sigs.append({"family": "echo", "name": "echo_denied", "weight": 0.95,
                         "detail": "The real person said 'not me' on a trusted line (ground truth)."})
        elif s and s in self.confirmed_senders:
            sigs.append({"family": "echo", "name": "echo_confirmed", "weight": -0.9, "detail": "The real person confirmed on a trusted line."})
        if p["to_handle"] in self.tripwires or (s and s.lower() in self.tripwires):
            sigs.append({"family": "bank", "name": "tripwire", "weight": 0.85,
                         "detail": "The payee or sender is a tripwired cash-out account."})
        elif p["amount"] >= BIG_PAYMENT:
            sigs.append({"family": "bank", "name": "new_payee_large", "weight": 0.4,
                         "detail": f"First payment to this payee, and ${p['amount']:,.0f} is large for this account."})
        claim = self._claim_for(s)
        if claim:
            sigs.append({"family": "message", "name": "impersonation_claim", "weight": 0.5,
                         "detail": "The linked message claims to be someone Linda knows, from a number that isn't theirs, and asks for money."})
        if self.carrier.get("linda", {}).get("unknown_call"):
            sigs.append({"family": "carrier", "name": "on_call_unknown", "weight": 0.5,
                         "detail": "Linda is on a call with an unknown number right now (simulated carrier signal)."})
        echo = self._echo_for(s)
        if echo and echo["status"] == "answered" and not echo["trusted"]:
            sigs.append({"family": "carrier", "name": "echo_untrusted", "weight": 0.6,
                         "detail": "The Echo answer came from a line with a SIM swap or forwarding: " + "; ".join(echo["trust_reasons"])})
        if echo and echo["status"] == "no_answer":
            sigs.append({"family": "echo", "name": "echo_no_answer", "weight": 0.3, "detail": "The real person didn't answer. No answer is never treated as safe."})
        risky = [x for x in sigs if x["weight"] > 0]
        fams = {x["family"] for x in risky}
        if any(x["name"] == "echo_confirmed" for x in sigs) and not any(x["name"] in ("tripwire",) for x in sigs):
            action = "allow"
        elif "echo" in fams and any(x["name"] == "echo_denied" for x in sigs) and len(fams) >= 2:
            action = "cancel"
        elif len(fams) >= 2:
            action = "hold"
        elif len(fams) == 1:
            action = "warn"
        else:
            action = "allow"
        return {"signals": sigs, "independent": len(fams), "action": action,
                "rule": "One signal can only warn. Holding money needs 2 independent signals. Cancelling needs the Echo denial plus one more."}

    def _claim_for(self, sender):
        if not sender:
            return False
        return any(e["sender"] == sender and e["payload"].get("claim_kind") in ("family", "friend") for e in self.echoes.values())

    def _echo_for(self, sender):
        es = [e for e in self.echoes.values() if sender and e["sender"] == sender]
        return max(es, key=lambda e: e["created"]) if es else None

    def _evaluate(self, p):
        if p["status"] == "cancelled":
            return p
        g = self.gauntlet(p)
        p["signals"] = g["signals"]
        if g["action"] == "cancel" and p["status"] in ("held", "sent"):
            p["status"] = "cancelled"
            p["hold_until"] = None
            p["decision_reasons"].append("Cancelled automatically: the real person said 'not me' and the payee is a tripwired account. "
                                             "Linda's $%s stays in checking." % f"{p['amount']:,.0f}")
        elif g["action"] == "hold" and p["status"] == "sent":
            p["status"] = "held"
            p["hold_until"] = int(_now() + HOLD_SECONDS)
            p["decision_reasons"].append("Held for a 30-minute cooling-off: two independent signals fired. "
                                         "We're asking the real person before any money moves.")
        elif g["action"] == "warn" and p["status"] == "sent" and not p["decision_reasons"]:
            p["decision_reasons"].append("Only one signal fired, so we warned Linda but didn't hold the money.")
        elif g["action"] == "allow" and p["status"] == "held":
            p["status"] = "released"
            p["decision_reasons"].append("Released: confirmed by the real person on a trusted line.")
        return p
