"""Orchestration: honeypot sessions, phone checks with the teaching loop, benchmark."""
import copy
import hashlib
import re
import threading

from .core import (CATEGORY_LABEL, CATEGORY_STEPS, MATCH, Agents, StoryMap, gate, match, phones, domains,
                   skill_score)
from .data import EVAL, PERSONAS, SCENARIOS
from .llm import Nemotron

TURNS = 3


def fingerprint(text):
    """One-way hash of a normalized message. Shared instead of the message itself."""
    norm = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


class Engine:
    def __init__(self):
        self.lock = threading.Lock()
        self.llm = Nemotron()
        self.agents = Agents(self.llm)
        self.reset()

    def reset(self):
        self.smap = StoryMap()
        self.good = set()
        self.stats = {"phone_checks": 0, "handled_on_device": 0, "rescues": 0, "skills_promoted": 0, "skills_rejected": 0}

    def state(self):
        return {"llm": self.llm.describe(), "stats": self.stats, "stories": self.smap.snapshot(),
                "events": self.smap.events[-40:][::-1], "personas": PERSONAS,
                "scenarios": {k: v["label"] for k, v in SCENARIOS.items()}}

    def gate_legit(self):
        return [m for m in EVAL if m["story"] is None and m["split"] == "train"]

    # ------------------------------------------------------------ honeypot
    def honeypot_session(self, scenario_id, decoy_id):
        """Generator of UI events for one decoy conversation."""
        persona = PERSONAS[decoy_id]
        sc = SCENARIOS[scenario_id]
        convo = []
        yield {"type": "start", "persona": persona, "scenario": sc["label"], "sender": sc["sender"]}
        for i in range(TURNS):
            line = self.agents.scammer_turn(scenario_id, i)
            if line is None:
                break
            convo.append({"who": "scammer", "text": line})
            yield {"type": "msg", "who": "scammer", "text": line, "agent": "Scammer simulator (scripted)"}
            reply, meta = self.agents.persona_reply(persona, convo)
            convo.append({"who": "decoy", "text": reply})
            yield {"type": "msg", "who": "decoy", "text": reply, "agent": "Honeypot persona", "meta": meta}
        ext, meta = self.agents.extract(convo)
        yield {"type": "stage", "stage": "extract", "agent": "Intel extractor", "meta": meta, "data": ext}
        with self.lock:
            res = self.agents.validate(ext, convo, decoy_id, self.smap)
        yield {"type": "stage", "stage": "validate", "agent": "Validator (rules)", "data": res}
        yield {"type": "done", "story": res.get("story"), "state": self.state()}

    # ------------------------------------------------------------ phone
    def card_for_story(self, story, asks):
        return {
            "level": "warn",
            "title": "This matches an active scam",
            "story": story["title"],
            "why": [f"Same play as a scam our decoys caught: {story['claim'][:120]}"] + [a[0].upper() + a[1:] for a in asks[:2]],
            "next_step": CATEGORY_STEPS.get(story["category"], CATEGORY_STEPS["other"]),
        }

    def check_message(self, text, sender="", known=False):
        steps = []
        self.stats["phone_checks"] += 1
        if known:
            steps.append({"stage": "contact", "note": "Sender is in your contacts. Not screened."})
            return {"steps": steps, "card": {"level": "clear", "title": "From a saved contact", "why": [], "next_step": ""}, "state": self.state()}
        if fingerprint(text) in self.good:
            self.stats["handled_on_device"] += 1
            steps.append({"stage": "local", "agent": "On-device matcher", "data": {"decision": "clear", "score": 0, "best": None, "ranked": [], "asks": [], "note": "Matches a message Nemotron already verified as legitimate (hash only)."}})
            return {"steps": steps, "card": {"level": "clear", "title": "Looks legitimate", "why": ["Same message was already verified as legitimate."], "next_step": ""}, "state": self.state()}
        with self.lock:
            local = match(text, self.smap.stories)
        steps.append({"stage": "local", "agent": "On-device matcher", "data": local})
        if local["decision"] == "warn":
            self.stats["handled_on_device"] += 1
            story = self.smap.stories[local["best"]["story_id"]]
            if story["status"] != "warn":
                card = {"level": "unsure", "title": "Possible scam (still being confirmed)", "story": story["title"],
                        "why": ["Matches a story only one decoy has seen so far."] + local["asks"][:1],
                        "next_step": CATEGORY_STEPS.get(story["category"], CATEGORY_STEPS["other"])}
            else:
                card = self.card_for_story(story, local["asks"])
            return {"steps": steps, "card": card, "state": self.state()}
        if local["decision"] == "clear":
            self.stats["handled_on_device"] += 1
            return {"steps": steps, "card": {"level": "clear", "title": "No known scam pattern", "why": ["No risky request and no match to an active story."], "next_step": ""}, "state": self.state()}
        # unsure: escalate (redacted) to Nemotron
        self.stats["rescues"] += 1
        verdict, trace, meta = self.agents.rescue(text, sender, local, self.smap)
        steps.append({"stage": "rescue", "agent": "Nemotron rescue (tool calls)", "meta": meta, "trace": trace, "data": verdict})
        story = self.smap.stories.get(verdict.get("story_id") or "")
        if verdict.get("verdict") == "scam":
            card = {"level": "warn", "title": "This looks like a scam", "story": story["title"] if story else "New pattern",
                    "why": [verdict.get("customer_message") or verdict.get("reason", "")] + local["asks"][:2],
                    "next_step": CATEGORY_STEPS.get(story["category"] if story else "other")}
        elif verdict.get("verdict") == "legit":
            if float(verdict.get("confidence") or 0) >= 0.7:
                self.good.add(fingerprint(text))
            card = {"level": "clear", "title": "Looks legitimate", "why": [verdict.get("customer_message") or verdict.get("reason", "")], "next_step": ""}
        else:
            card = {"level": "unsure", "title": "We're not sure", "why": [verdict.get("reason", "")], "next_step": CATEGORY_STEPS["other"]}
        if verdict.get("verdict") == "scam" and story:
            proposal, fmeta = self.agents.forge(text, story)
            with self.lock:
                ok, results, cand = gate(story, proposal, text, self.gate_legit(), self.smap.stories)
                if ok:
                    story["skill"] = cand["skill"]
                    story["skill"]["version"] += 1
                    story["skill"]["history"].append(f"v{story['skill']['version']}: +{', '.join(proposal['add_keywords'] + proposal['add_phrases'])}")
                    self.stats["skills_promoted"] += 1
                    self.smap.log("skill", f"{story['id']} skill v{story['skill']['version']} promoted")
                else:
                    self.stats["skills_rejected"] += 1
                    self.smap.log("skill", f"{story['id']} skill proposal rejected by gate")
            steps.append({"stage": "forge", "agent": "Skill forge + gate", "meta": fmeta, "data": {"proposal": proposal, "promoted": ok, "gate": results}})
        return {"steps": steps, "card": card, "state": self.state()}

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
        """Replay scripted decoy sessions (extractor + validator only, no persona chat)."""
        for sid in [k for k in SCENARIOS if k != "poison"]:
            convo = [{"who": "scammer", "text": t} for t in SCENARIOS[sid]["turns"]]
            ext, _ = self.agents.extract(convo)
            for d in decoys:
                with self.lock:
                    self.agents.validate(copy.deepcopy(ext), convo, d, self.smap)
        return self.state()

    # ------------------------------------------------------------ benchmark
    def benchmark(self):
        saved_smap, saved_stats = self.smap, dict(self.stats)
        calls0 = self.llm.calls
        saved_good = self.good
        self.smap = StoryMap()
        self.seed()
        seed_calls = self.llm.calls - calls0
        base = copy.deepcopy(self.smap)
        test = [m for m in EVAL if m["split"] == "test"]
        train = [m for m in EVAL if m["split"] == "train"]
        n_scam = sum(1 for m in test if m["story"])
        n_legit = len(test) - n_scam

        def score(flags):
            caught = sum(1 for m, f in zip(test, flags) if m["story"] and f == "scam")
            fa = sum(1 for m, f in zip(test, flags) if not m["story"] and f == "scam")
            unsure = sum(1 for f in flags if f == "unsure")
            return {"caught": caught, "scams": n_scam, "false_alarms": fa, "legit": n_legit, "unsure": unsure}

        rows = []
        # 0. today's approach: block known numbers / links only
        known_ind = set()
        for s in base.stories.values():
            known_ind |= {n for n, i in s["numbers"].items() if i["status"] != "rejected"} | set(s["domains"])
        f0 = ["scam" if (m["sender"] in known_ind or set(phones(m["text"]) + domains(m["text"])) & known_ind) else "clear" for m in test]
        rows.append({"mode": "Number/link blocklist (today's approach)", **score(f0), "hosted_calls": 0})
        # 1. local only
        f1 = [{"warn": "scam", "clear": "clear", "unsure": "unsure"}[match(m["text"], base.stories)["decision"]] for m in test]
        rows.append({"mode": "On-device matcher only", **score(f1), "hosted_calls": 0})
        # 2. local + Nemotron rescue
        self.smap = copy.deepcopy(base)
        c0 = self.llm.calls
        f2, rescues2 = [], 0
        for m in test:
            loc = match(m["text"], self.smap.stories)
            if loc["decision"] == "unsure":
                rescues2 += 1
                v, _, _ = self.agents.rescue(m["text"], m["sender"], loc, self.smap)
                f2.append(v.get("verdict", "unsure") if v.get("verdict") in ("scam", "legit") else "unsure")
            else:
                f2.append("scam" if loc["decision"] == "warn" else "clear")
        f2 = ["clear" if f == "legit" else f for f in f2]
        rows.append({"mode": "On-device + Nemotron rescue", **score(f2), "hosted_calls": rescues2, "api_calls": self.llm.calls - c0})

        # Campaign replay: scammers blast the same text to many people.
        # Each test message reaches COPIES customers in a row.
        COPIES = 5
        stream = [m for m in test for _ in range(COPIES)]
        n_s = sum(1 for m in stream if m["story"])
        n_l = len(stream) - n_s

        def tally(flags, calls, note):
            caught = sum(1 for m, f in zip(stream, flags) if m["story"] and f == "scam")
            fa = sum(1 for m, f in zip(stream, flags) if not m["story"] and f == "scam")
            return {"mode": note, "caught": caught, "scams": n_s, "false_alarms": fa, "legit": n_l,
                    "unsure": sum(1 for f in flags if f == "unsure"), "hosted_calls": calls}

        # A. Nemotron rescues every unsure copy (no learning). Verdicts for identical
        #    messages are reused from row 2, so the call count is projected, not re-run.
        fa_flags = [f for m, f in zip(test, f2) for _ in range(COPIES)]
        unsure_unique = sum(1 for m in test if match(m["text"], base.stories)["decision"] == "unsure")
        campaign = [tally(fa_flags, unsure_unique * COPIES, f"Campaign x{COPIES}: rescue every copy (projected)")]
        # B. Rescue once, forge a skill, gate it, then later copies are caught on-device.
        self.smap = copy.deepcopy(base)
        c0 = self.llm.calls
        fb, rescues_b, promoted, rejected = [], 0, 0, 0
        good = set()
        for m in stream:
            if fingerprint(m["text"]) in good:
                fb.append("clear")
                continue
            loc = match(m["text"], self.smap.stories)
            if loc["decision"] != "unsure":
                fb.append("scam" if loc["decision"] == "warn" else "clear")
                continue
            rescues_b += 1
            v, _, _ = self.agents.rescue(m["text"], m["sender"], loc, self.smap)
            verdict = v.get("verdict")
            fb.append("scam" if verdict == "scam" else ("clear" if verdict == "legit" else "unsure"))
            if verdict == "legit" and float(v.get("confidence") or 0) >= 0.7:
                good.add(fingerprint(m["text"]))
            s = self.smap.stories.get(v.get("story_id") or "")
            if verdict == "scam" and s:
                prop, _ = self.agents.forge(m["text"], s)
                ok, _, cand = gate(s, prop, m["text"], self.gate_legit(), self.smap.stories)
                if ok:
                    s["skill"] = cand["skill"]
                    promoted += 1
                else:
                    rejected += 1
        row_b = tally(fb, rescues_b, f"Campaign x{COPIES}: rescue once, then teach the phone")
        row_b["note"] = f"{promoted} skills promoted, {rejected} rejected by the gate, {self.llm.calls - c0} API calls in live mode"
        campaign.append(row_b)
        self.smap, self.stats, self.good = saved_smap, saved_stats, saved_good
        return {"mode": self.llm.mode, "model": self.llm.describe()["model"], "rows": rows, "campaign": campaign,
                "test_size": len(test), "train_size": len(train), "seed_calls": seed_calls}
