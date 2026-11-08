"""Orchestration: decoy sessions, live 'you be the scammer' sessions, phone checks with
consent and the teaching loop, an event stream for the NVIDIA view, and the benchmark."""
import copy
import hashlib
import json
import re
import threading
import time
import uuid
from collections import deque
from pathlib import Path

from .core import (CATEGORY_STEPS, INJECTION_RE, Agents, StoryMap, domains, gate, match, phones, redact,
                   sender_status)
from .data import EVAL, PERSONAS, SCENARIOS
from .llm import Nemotron

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TURNS = 3            # scripted scammer turns per decoy session
LIVE_TURN_CAP = 6    # max judge messages in a live session
THREAD_WINDOW = 3    # messages from the same unknown sender scored together


def fingerprint(text):
    """One-way hash of a normalized message. The phone sends this, never the message, to ask 'already verified?'"""
    norm = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def short(obj, n=240):
    s = obj if isinstance(obj, str) else json.dumps(obj)
    return s if len(s) <= n else s[: n - 1] + "…"


def load_jsonl(path):
    """Load a labeled message file: one JSON object per line with text, label (scam|legit), optional sender/category/split."""
    items = []
    if not path.exists():
        return items
    for i, line in enumerate(path.read_text().splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not d.get("text") or d.get("label") not in ("scam", "legit"):
            continue
        items.append({"id": d.get("id", f"{path.stem}-{i}"), "text": d["text"], "sender": d.get("sender", ""),
                      "story": (d.get("category") or "scam") if d["label"] == "scam" else None,
                      "split": d.get("split", "test")})
    return items


class Engine:
    def __init__(self):
        self.lock = threading.RLock()
        self.llm = Nemotron()
        self.agents = Agents(self.llm)
        self.events = deque(maxlen=500)
        self.ev_seq = 0
        self.reset()

    def reset(self):
        self.smap = StoryMap()
        self.good = set()
        self.threads = {}
        self.pending = {}
        self.live = {}
        self.stats = {"phone_checks": 0, "handled_on_device": 0, "asked_consent": 0, "rescues": 0,
                      "bytes_to_cloud": 0, "skills_promoted": 0, "skills_rejected": 0, "policy_overrides": 0}
        self.emit("system", "reset", note="Demo state reset")

    # ------------------------------------------------------------ event stream (NVIDIA view)
    def emit(self, agent, stage, **data):
        with self.lock:
            self.ev_seq += 1
            self.events.append({"id": self.ev_seq, "t": time.strftime("%H:%M:%S"), "agent": agent, "stage": stage, **data})

    def events_since(self, since):
        return [e for e in list(self.events) if e["id"] > since]

    def state(self):
        return {"llm": self.llm.describe(), "stats": self.stats, "stories": self.smap.snapshot(),
                "log": self.smap.events[-40:][::-1], "personas": PERSONAS, "last_event": self.ev_seq,
                "scenarios": {k: v["label"] for k, v in SCENARIOS.items()}}

    def gate_legit(self):
        return [m for m in EVAL if m["story"] is None and m["split"] == "train"]

    # ------------------------------------------------------------ scripted decoy session
    def honeypot_session(self, scenario_id, decoy_id):
        """Generator of UI events for one scripted decoy conversation."""
        persona = PERSONAS[decoy_id]
        sc = SCENARIOS[scenario_id]
        convo = []
        yield {"type": "start", "persona": persona, "scenario": sc["label"], "sender": sc["sender"]}
        for i in range(TURNS):
            line = self.agents.scammer_turn(scenario_id, i)
            if line is None:
                break
            convo.append({"who": "scammer", "text": line, "sender": sc["sender"]})
            self.emit("Scammer simulator", "message", output=short(line), mode="scripted")
            yield {"type": "msg", "who": "scammer", "text": line, "agent": "Scammer simulator (scripted)"}
            reply, meta = self.agents.persona_reply(persona, convo)
            convo.append({"who": "decoy", "text": reply})
            self.emit("Honeypot persona", "reply", input=short(line), output=short(reply), **meta)
            yield {"type": "msg", "who": "decoy", "text": reply, "agent": "Honeypot persona", "meta": meta}
        yield from self._finish_session(convo, decoy_id)

    def _finish_session(self, convo, decoy_id):
        ext, meta = self.agents.extract(convo)
        self.emit("Intel extractor", "extract", output=short(ext, 400), **meta)
        yield {"type": "stage", "stage": "extract", "agent": "Intel extractor", "meta": meta, "data": ext}
        with self.lock:
            res = self.agents.validate(ext, convo, decoy_id, self.smap)
        self.emit("Validator (rules)", "validate", output=short([f"{'OK' if c['ok'] else 'X'} {c['check']}" for c in res["checks"]], 400),
                  mode="rules", story=res.get("story"), quarantined=res.get("quarantined"))
        yield {"type": "stage", "stage": "validate", "agent": "Validator (rules)", "data": res}
        yield {"type": "done", "story": res.get("story"), "state": self.state()}

    # ------------------------------------------------------------ live: the judge plays the scammer
    def live_start(self, decoy_id):
        sid = uuid.uuid4().hex[:8]
        self.live[sid] = {"decoy": decoy_id, "convo": [], "sender": "(214) 555-0177"}
        self.emit("Honeypot persona", "live-start", note=f"Live session with {PERSONAS[decoy_id]['name']}")
        return {"session": sid, "persona": PERSONAS[decoy_id]}

    def live_say(self, sid, text):
        s = self.live.get(sid)
        if not s:
            return {"error": "Session ended. Start a new one."}
        if sum(1 for c in s["convo"] if c["who"] == "scammer") >= LIVE_TURN_CAP:
            return {"error": f"Turn limit reached ({LIVE_TURN_CAP}). End the session to see what the decoy learned."}
        text = (text or "").strip()[:500]
        s["convo"].append({"who": "scammer", "text": text, "sender": s["sender"]})
        injected = bool(INJECTION_RE.search(text))
        reply, meta = self.agents.persona_reply(PERSONAS[s["decoy"]], s["convo"])
        s["convo"].append({"who": "decoy", "text": reply})
        self.emit("Honeypot persona", "reply", input=short(text), output=short(reply), injection=injected, **meta)
        return {"reply": reply, "meta": meta, "injection": injected}

    def live_end(self, sid):
        s = self.live.pop(sid, None)
        if not s or not s["convo"]:
            return {"error": "Nothing to analyze yet."}
        out = {}
        for ev in self._finish_session(s["convo"], s["decoy"]):
            if ev["type"] == "stage":
                out[ev["stage"]] = ev["data"]
            elif ev["type"] == "done":
                out["state"] = ev["state"]
        return out

    # ------------------------------------------------------------ phone
    def _card_unsure(self, local, check_id):
        why = ["This doesn't match a play we know yet."] + [a[0].upper() + a[1:] for a in local["asks"][:2]]
        return {"level": "unsure", "title": "We're not sure about this one", "why": why,
                "next_step": CATEGORY_STEPS["other"], "consent": True, "check_id": check_id}

    def check_message(self, text, sender="", known=False, auto_consent=False):
        """Phone side. Decides on-device; only an unsure message can leave the phone, and only after consent."""
        check_id = uuid.uuid4().hex[:8]
        steps = []
        self.stats["phone_checks"] += 1
        if known:
            steps.append({"stage": "contact", "note": "Sender is a saved contact. Not screened."})
            return {"check_id": check_id, "steps": steps, "cloud_bytes": 0,
                    "card": {"level": "clear", "title": "From a saved contact", "why": [], "next_step": ""}, "state": self.state()}
        key = sender or "unknown"
        thread = self.threads.setdefault(key, [])
        thread.append(text)
        del thread[:-THREAD_WINDOW]
        ctx = " ".join(thread)
        if fingerprint(text) in self.good:
            self.stats["handled_on_device"] += 1
            local = {"decision": "clear", "score": 0, "best": None, "ranked": [], "asks": [],
                     "note": "Same message was already verified as legitimate (the phone sent only a hash)."}
            steps.append({"stage": "local", "agent": "On-device matcher", "data": local})
            self.emit("On-device matcher", "local", output="clear (known-good hash)", mode="on-device")
            return {"check_id": check_id, "steps": steps, "cloud_bytes": 0, "state": self.state(),
                    "card": {"level": "clear", "title": "Looks legitimate", "why": [local["note"]], "next_step": ""}}
        with self.lock:
            local = match(ctx, self.smap.stories)
        local["sender"] = sender_status(sender)
        local["thread_len"] = len(thread)
        steps.append({"stage": "local", "agent": "On-device matcher", "data": local})
        self.emit("On-device matcher", "local", input="(stays on phone)", output=f"{local['decision']} · score {local['score']}", mode="on-device")
        if local["decision"] == "warn":
            self.stats["handled_on_device"] += 1
            story = self.smap.stories[local["best"]["story_id"]]
            if story["status"] != "warn":
                card = {"level": "unsure", "title": "Possible scam (still being confirmed)", "story": story["title"],
                        "why": ["Matches a play only one decoy has seen so far."] + local["asks"][:1],
                        "next_step": CATEGORY_STEPS.get(story["category"], CATEGORY_STEPS["other"])}
            else:
                card = {"level": "warn", "title": "This matches an active scam", "story": story["title"],
                        "why": [f"Same play our decoys caught: {story['claim'][:110]}"] + [a[0].upper() + a[1:] for a in local["asks"][:2]],
                        "next_step": CATEGORY_STEPS.get(story["category"], CATEGORY_STEPS["other"]), "story_id": story["id"]}
            return {"check_id": check_id, "steps": steps, "card": card, "cloud_bytes": 0, "state": self.state()}
        if local["decision"] == "unsure" and not local["asks"] and local["sender"]["registered"]:
            # A registered A2P sender (vetted short code / business number) with no risky ask: clear on the phone.
            self.stats["handled_on_device"] += 1
            self.emit("On-device matcher", "local", output=f"clear · {local['sender']['status']}, no risky ask", mode="on-device")
            return {"check_id": check_id, "steps": steps, "cloud_bytes": 0, "state": self.state(),
                    "card": {"level": "clear", "title": "Looks legitimate",
                             "why": [f"Sent from a {local['sender']['status']}.", "It doesn't ask you to pay, click, or call a new number."],
                             "next_step": ""}}
        if local["decision"] == "clear":
            self.stats["handled_on_device"] += 1
            return {"check_id": check_id, "steps": steps, "cloud_bytes": 0, "state": self.state(),
                    "card": {"level": "clear", "title": "No known scam pattern", "why": ["No risky request and no match to an active play."], "next_step": ""}}
        self.pending[check_id] = {"text": ctx, "raw": text, "sender": sender, "local": local, "steps": steps}
        if auto_consent:
            return self.consent(check_id)
        self.stats["asked_consent"] += 1
        return {"check_id": check_id, "steps": steps, "card": self._card_unsure(local, check_id), "cloud_bytes": 0, "state": self.state()}

    def decide(self, verdict, trace, asks):
        """Policy layer on top of the model. Rules win over the model."""
        v = dict(verdict)
        evidence = [t for t in trace if t.get("tool") != "submit_verdict"]
        if v.get("verdict") in ("scam", "legit") and not evidence:
            v.update(verdict="unsure", policy="No tool evidence behind the verdict, so it was downgraded to unsure.")
        elif v.get("verdict") == "legit" and asks:
            v.update(verdict="unsure", policy="It asks for a payment, link or callback, so it can never be marked safe automatically.")
        if v.get("policy"):
            self.stats["policy_overrides"] += 1
        return v

    def consent(self, check_id):
        p = self.pending.pop(check_id, None)
        if not p:
            return {"error": "That check has expired. Receive the message again."}
        steps = p["steps"]
        red = redact(p["text"])
        sent = len(red.encode())
        self.stats["rescues"] += 1
        self.stats["bytes_to_cloud"] += sent
        self.emit("Consent", "consent", output=f"Customer tapped 'Ask Detour'. Sent {sent} bytes, redacted.", mode="customer")
        raw_verdict, trace, meta = self.agents.rescue(p["text"], p["sender"], p["local"], self.smap)
        for t in trace:
            self.emit("Nemotron rescue", "tool", tool=t["tool"], input=short(t["args"], 160), output=short(t["result"], 200), mode=meta["mode"])
        verdict = self.decide(raw_verdict, trace, p["local"]["asks"])
        self.emit("Policy (rules)", "verdict", output=f"{raw_verdict.get('verdict')} → {verdict['verdict']}", mode="rules", policy=verdict.get("policy"))
        steps.append({"stage": "rescue", "agent": "Nemotron rescue (tool calls)", "meta": meta, "trace": trace, "data": verdict})
        story = self.smap.stories.get(verdict.get("story_id") or "")
        if verdict["verdict"] == "scam":
            card = {"level": "warn", "title": "This looks like a scam", "story": story["title"] if story else "New pattern",
                    "why": [verdict.get("customer_message") or verdict.get("reason", "")] + [a[0].upper() + a[1:] for a in p["local"]["asks"][:2]],
                    "next_step": CATEGORY_STEPS.get(story["category"] if story else "other"), "story_id": story["id"] if story else ""}
        elif verdict["verdict"] == "legit":
            if float(verdict.get("confidence") or 0) >= 0.7:
                self.good.add(fingerprint(p["raw"]))
            card = {"level": "clear", "title": "Looks legitimate", "why": [verdict.get("customer_message") or verdict.get("reason", "")], "next_step": ""}
        else:
            card = {"level": "unsure", "title": "Still not sure. Play it safe", "why": [verdict.get("policy") or verdict.get("reason", "")],
                    "next_step": CATEGORY_STEPS["other"]}
        if verdict["verdict"] == "scam" and story:
            proposal, fmeta = self.agents.forge(p["raw"], story)
            self.emit("Skill forge", "propose", output=short(proposal["add_keywords"] + proposal["add_phrases"]), **fmeta)
            with self.lock:
                ok, results, cand = gate(story, proposal, p["raw"], self.gate_legit(), self.smap.stories)
                if ok:
                    story["skill"] = cand["skill"]
                    story["skill"]["version"] += 1
                    story["skill"]["history"].append(f"v{story['skill']['version']}: +{', '.join(proposal['add_keywords'] + proposal['add_phrases'])}")
                    self.stats["skills_promoted"] += 1
                    self.smap.log("skill", f"{story['id']} skill v{story['skill']['version']} promoted to every phone")
                else:
                    self.stats["skills_rejected"] += 1
                    self.smap.log("skill", f"{story['id']} skill proposal rejected by the gate")
            self.emit("Gate (tests)", "gate", output=("promoted" if ok else "rejected") + " · " + ", ".join(("PASS " if r["ok"] else "FAIL ") + r["test"] for r in results), mode="rules")
            steps.append({"stage": "forge", "agent": "Skill forge + gate", "meta": fmeta, "data": {"proposal": proposal, "promoted": ok, "gate": results}})
        return {"check_id": check_id, "steps": steps, "card": card, "cloud_bytes": sent, "sent_text": red, "state": self.state()}

    def report(self, story_id):
        s = self.smap.stories.get(story_id)
        if s:
            s["reports"] += 1
            self.smap.refresh_status(s)
            self.smap.log("report", f"Customer report on {story_id} ({s['reports']} total)")
        return self.state()

    def approve_block(self, story_id, number):
        s = self.smap.stories.get(story_id)
        if s and number in s["numbers"] and s["numbers"][number]["status"] == "needs human review":
            s["numbers"][number]["status"] = "blocked"
            self.smap.log("block", f"Analyst approved block of {number} ({story_id})")
        return self.state()

    # ------------------------------------------------------------ seeding
    def seed(self, decoys=("decoy-01", "decoy-02")):
        """Replay scripted decoy sessions (extractor + validator, no persona chat) so the story map has active plays."""
        for sid in [k for k in SCENARIOS if k != "poison"]:
            convo = [{"who": "scammer", "text": t, "sender": SCENARIOS[sid]["sender"]} for t in SCENARIOS[sid]["turns"]]
            ext, meta = self.agents.extract(convo)
            self.emit("Intel extractor", "extract", output=short(ext.get("story_title", "")), **meta)
            for d in decoys:
                with self.lock:
                    self.agents.validate(copy.deepcopy(ext), convo, d, self.smap)
        return self.state()

    # ------------------------------------------------------------ benchmark
    def _run_set(self, items, base, label):
        """Blocklist vs on-device vs on-device + rescue on one labeled set."""
        n_scam = sum(1 for m in items if m["story"])
        n_legit = len(items) - n_scam

        def score(flags, mode, calls=0):
            tp = sum(1 for m, f in zip(items, flags) if m["story"] and f == "scam")
            fp = sum(1 for m, f in zip(items, flags) if not m["story"] and f == "scam")
            return {"set": label, "mode": mode, "caught": tp, "scams": n_scam, "false_alarms": fp, "legit": n_legit,
                    "unsure": sum(1 for f in flags if f == "unsure"), "hosted_calls": calls,
                    "precision": round(tp / (tp + fp), 3) if tp + fp else None}

        known = set()
        for s in base.stories.values():
            known |= {n for n, i in s["numbers"].items() if i["status"] != "rejected"} | set(s["domains"])
        f0 = ["scam" if (m["sender"] in known or set(phones(m["text"]) + domains(m["text"])) & known) else "clear" for m in items]
        f1 = [{"warn": "scam", "clear": "clear", "unsure": "unsure"}[match(m["text"], base.stories)["decision"]] for m in items]
        self.smap = copy.deepcopy(base)
        f2, calls = [], 0
        for m in items:
            loc = match(m["text"], self.smap.stories)
            if loc["decision"] != "unsure":
                f2.append("scam" if loc["decision"] == "warn" else "clear")
                continue
            calls += 1
            v, trace, _ = self.agents.rescue(m["text"], m["sender"], loc, self.smap)
            v = self.decide(v, trace, loc["asks"])
            f2.append({"scam": "scam", "legit": "clear"}.get(v["verdict"], "unsure"))
        return [score(f0, "Number/link blocklist (today's approach)"), score(f1, "On-device matcher only"),
                score(f2, "On-device + Nemotron rescue", calls)], f2

    def benchmark(self):
        saved = (self.smap, self.stats, self.good, self.threads, self.pending)
        calls0 = self.llm.calls
        self.smap = StoryMap()
        self.seed()
        base = copy.deepcopy(self.smap)
        builtin = [m for m in EVAL if m["split"] == "test"]
        sets = [("Built-in held-out set", builtin)]
        gen = [m for m in load_jsonl(DATA_DIR / "generated.jsonl") if m["split"] == "test"]
        if gen:
            sets.append(("Nemotron-generated held-out set", gen))
        hand = load_jsonl(DATA_DIR / "handwritten.jsonl")
        if hand:
            sets.append(("Hand-written by a teammate (never seen during tuning)", hand))
        rows = []
        f2_builtin = None
        for label, items in sets:
            r, f2 = self._run_set(items, base, label)
            rows += r
            if f2_builtin is None:
                f2_builtin = f2

        # Campaign replay on the built-in set: each message reaches COPIES customers in a row.
        COPIES = 5
        stream = [m for m in builtin for _ in range(COPIES)]
        n_s = sum(1 for m in stream if m["story"])

        def tally(flags, calls, mode, note=""):
            return {"set": f"Campaign replay x{COPIES}", "mode": mode, "caught": sum(1 for m, f in zip(stream, flags) if m["story"] and f == "scam"),
                    "scams": n_s, "false_alarms": sum(1 for m, f in zip(stream, flags) if not m["story"] and f == "scam"),
                    "legit": len(stream) - n_s, "unsure": sum(1 for f in flags if f == "unsure"), "hosted_calls": calls, "note": note}

        unsure_unique = sum(1 for m in builtin if match(m["text"], base.stories)["decision"] == "unsure")
        campaign = [tally([f for f in f2_builtin for _ in range(COPIES)], unsure_unique * COPIES,
                          "Nemotron checks every copy (projected)")]
        self.smap, self.good = copy.deepcopy(base), set()
        c0 = self.llm.calls
        fb, calls, promoted, rejected = [], 0, 0, 0
        for m in stream:
            if fingerprint(m["text"]) in self.good:
                fb.append("clear")
                continue
            loc = match(m["text"], self.smap.stories)
            if loc["decision"] != "unsure":
                fb.append("scam" if loc["decision"] == "warn" else "clear")
                continue
            calls += 1
            v, trace, _ = self.agents.rescue(m["text"], m["sender"], loc, self.smap)
            v = self.decide(v, trace, loc["asks"])
            fb.append({"scam": "scam", "legit": "clear"}.get(v["verdict"], "unsure"))
            if v["verdict"] == "legit" and not loc["asks"] and float(v.get("confidence") or 0) >= 0.7:
                self.good.add(fingerprint(m["text"]))
            s = self.smap.stories.get(v.get("story_id") or "")
            if v["verdict"] == "scam" and s:
                prop, _ = self.agents.forge(m["text"], s)
                ok, _, cand = gate(s, prop, m["text"], self.gate_legit(), self.smap.stories)
                if ok:
                    s["skill"] = cand["skill"]
                    promoted += 1
                else:
                    rejected += 1
        campaign.append(tally(fb, calls, "Nemotron checks once, then teaches the phone",
                              f"{promoted} skills promoted, {rejected} rejected by the gate"))
        total_calls = self.llm.calls - calls0
        self.smap, self.stats, self.good, self.threads, self.pending = saved
        return {"mode": self.llm.mode, "model": self.llm.describe()["model"], "rows": rows, "campaign": campaign,
                "api_calls": total_calls, "thresholds": {"warn": 0.60, "clear": 0.30, "frozen": True}}
