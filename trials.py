"""End-to-end trials: run the WHOLE Detour pipeline N times with randomized inputs and measure every stage.

    python3 trials.py              # 10 trials, uses whatever mode .env gives (LIVE with a key, else MOCK)
    python3 trials.py --n 3 --quick   # fewer messages per trial (use this for LIVE: far fewer Nemotron calls)
    DETOUR_MOCK=1 python3 trials.py   # offline stand-ins (fast, deterministic agents; not Nemotron numbers)

Each trial uses a fresh engine and a different random seed. Stages measured:
  A. Decoy sessions: scammer script -> decoy persona -> intel extractor -> validator. Is the scam category right?
     Is the poisoning attack quarantined?
  B. Phone (on-device matcher, no model): held-out scams and legit texts, each PERTURBED per trial
     (new 555-01xx numbers, case changes, homoglyphs, spaced digits). warn / unsure / clear.
  C. Consent -> Nemotron rescue (tools) -> forge -> 4-check gate -> same message again: caught on-device?
  D. PNC: $3,000 bail what-if (deterministic), Script Mirror (decoy script shown, no numbers leak), money coach.
Results: printed table + results/trials.json
"""
import argparse
import json
import random
import re
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from detour.core import PHONE_RE  # noqa: E402
from detour.data import EVAL, PERSONAS, SCENARIOS  # noqa: E402
from detour.engine import Engine, load_jsonl, DATA_DIR  # noqa: E402

CAT = {"bank_alert": "bank", "toll": "toll", "parcel": "delivery", "carrier_bill": "carrier", "grandkid": "family_emergency",
       "job": "job"}
HOMO = {"a": "а", "e": "е", "o": "о", "c": "с", "p": "р"}  # Cyrillic look-alikes


def perturb(text, sender, rng, obfuscate=True):
    """New phone numbers every trial (the whole point: scammers rotate numbers), plus light obfuscation."""
    new = lambda: f"({rng.choice(['214', '469', '972', '682', '817'])}) 555-01{rng.randint(0, 99):02d}"  # noqa: E731
    text = PHONE_RE.sub(lambda m: new(), text)
    if sender and PHONE_RE.search(sender):
        sender = new()
    if not obfuscate:  # real businesses and friends don't disguise their texts; only scams get the tricks below
        return text, sender
    r = rng.random()
    if r < 0.2:
        text = text.upper()
    elif r < 0.4:
        text = text.lower()
    if rng.random() < 0.25:  # swap one letter for a look-alike
        idx = [i for i, ch in enumerate(text) if ch.lower() in HOMO]
        if idx:
            i = rng.choice(idx)
            text = text[:i] + HOMO[text[i].lower()] + text[i + 1:]
    if rng.random() < 0.1:  # spaced-out digits trick
        text = PHONE_RE.sub(lambda m: " ".join(re.sub(r"\D", "", m.group(0))), text, count=1)
    return text, sender


def trial(seed, quick):
    rng = random.Random(seed)
    e = Engine()
    calls0 = e.llm.calls
    out = {"seed": seed, "mode": e.llm.mode}

    # A. decoy sessions
    scen = rng.sample([k for k in SCENARIOS if k != "poison"], 2 if quick else 4)
    right = 0
    for sid in scen:
        decoy = rng.choice(list(PERSONAS))
        ext = None
        for ev in e.honeypot_session(sid, decoy):
            if ev["type"] == "stage" and ev["stage"] == "extract":
                ext = ev["data"]
        right += int(bool(ext) and ext.get("category") == CAT[sid])
    out["decoy_category_ok"] = f"{right}/{len(scen)}"
    q = None
    for ev in e.honeypot_session("poison", rng.choice(list(PERSONAS))):
        if ev["type"] == "stage" and ev["stage"] == "validate":
            q = ev["data"].get("quarantined")
    out["poison_quarantined"] = bool(q)
    e.seed()  # the rest of the decoy history (2 decoy lines each), so stories are corroborated

    # B + C. phone, consent, rescue, teach
    items = [m for m in EVAL if m["split"] == "test"]
    if not quick:
        items += [r for r in load_jsonl(DATA_DIR / "generated.jsonl") if r["split"] == "test"]
    rng.shuffle(items)
    tp_dev = fp_dev = tp_final = fp_final = unsure_scam = unsure_legit = taught = teach_tries = 0
    n_scam = sum(1 for m in items if m["story"])
    n_legit = len(items) - n_scam
    for m in items:
        e.threads.clear()  # each test message is its own conversation (a different scammer / sender)
        # Scams get new numbers + obfuscation every trial. Legit texts stay as written: a real bank keeps its real number.
        text, sender = perturb(m["text"], m.get("sender", ""), rng) if m["story"] else (m["text"], m.get("sender", ""))
        r = e.check_message(text, sender, m.get("known", False))
        lvl = r["card"]["level"]
        is_scam = bool(m["story"])
        final = lvl
        if lvl == "warn":
            tp_dev += is_scam
            fp_dev += not is_scam
        elif lvl == "unsure":
            unsure_scam += is_scam
            unsure_legit += not is_scam
            c = e.consent(r["check_id"])
            final = (c.get("card") or {}).get("level", "unsure")
            if is_scam and final == "warn":
                promoted = any(s.get("stage") == "forge" and s["data"].get("promoted") for s in c.get("steps", []))
                if promoted:
                    teach_tries += 1
                    again = e.check_message(text, perturb(m["text"], m.get("sender", ""), rng)[1])
                    taught += again["card"]["level"] == "warn"
        tp_final += is_scam and final == "warn"
        fp_final += (not is_scam) and final == "warn"
    out.update(scams=n_scam, legit=n_legit, caught_on_device=tp_dev, false_alarm_on_device=fp_dev,
               unsure_scam=unsure_scam, unsure_legit=unsure_legit, caught_after_rescue=tp_final,
               false_alarm_after_rescue=fp_final, teach_ok=f"{taught}/{teach_tries}")

    # D. PNC
    from detour import finance
    w = finance.whatif(finance.load_customer(), [{"type": "payment", "amount": 3000, "from": "checking",
                                                   "date": "2026-11-09", "label": "bail"}])
    out["whatif_overdraft_days"] = w["after"]["forecast_summary"]["overdraft_days"]
    mir = e.script_mirror("family_emergency")
    leaks = [ln["text"] for ln in mir.get("lines", []) if PHONE_RE.search(ln["text"]) or re.search(r"https?://", ln["text"])]
    out["mirror_ok"] = bool(mir.get("active")) and len(mir.get("lines", [])) >= 2 and not leaks \
        and all(ln["tactics"] for ln in mir["lines"])
    out["mirror_lines"] = len(mir.get("lines", []))
    if not quick or seed == 0:
        cr = finance.coach(e.llm, "Can I afford to pay $3,000 bail for my grandson tomorrow?")
        out["coach_warns"] = "scam" in cr["answer"].lower()
        out["coach_tools"] = len(cr.get("tool_trace", []))
        out["coach_mode"] = cr.get("mode")
    out["hosted_calls"] = e.llm.calls - calls0
    out["api_errors"] = e.llm.errors
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    rows = []
    for i in range(a.n):
        r = trial(i, a.quick)
        rows.append(r)
        print(f"trial {i + 1:>2}/{a.n} [{r['mode']}] decoy-cat {r['decoy_category_ok']}  poison-quarantined {r['poison_quarantined']}  "
              f"on-device {r['caught_on_device']}/{r['scams']} (FA {r['false_alarm_on_device']}/{r['legit']})  "
              f"after-rescue {r['caught_after_rescue']}/{r['scams']} (FA {r['false_alarm_after_rescue']}/{r['legit']})  "
              f"teach {r['teach_ok']}  whatif-OD {r['whatif_overdraft_days']}d  mirror {'OK' if r['mirror_ok'] else 'FAIL'}  "
              f"coach-warns {r.get('coach_warns', '-')}  calls {r['hosted_calls']}", flush=True)

    def pct(k, d):
        return [100 * r[k] / r[d] for r in rows if r[d]]

    summ = {}
    for name, k, d in [("Caught on device (%)", "caught_on_device", "scams"), ("False alarms on device (%)", "false_alarm_on_device", "legit"),
                       ("Caught after consent + rescue (%)", "caught_after_rescue", "scams"),
                       ("False alarms after rescue (%)", "false_alarm_after_rescue", "legit")]:
        v = pct(k, d)
        summ[name] = {"mean": round(statistics.mean(v), 1), "min": round(min(v), 1), "max": round(max(v), 1)}
    summ["Poison quarantined"] = f"{sum(r['poison_quarantined'] for r in rows)}/{len(rows)}"
    summ["Script Mirror OK"] = f"{sum(r['mirror_ok'] for r in rows)}/{len(rows)}"
    summ["What-if overdraft days (expect 50)"] = sorted({r['whatif_overdraft_days'] for r in rows})
    print("\nSUMMARY over", len(rows), "trials, mode", rows[0]["mode"])
    for k, v in summ.items():
        print(f"  {k}: {v}")
    print(f"Done in {time.time() - t0:.0f}s")
    Path("results").mkdir(exist_ok=True)
    Path("results/trials.json").write_text(json.dumps({"summary": summ, "trials": rows}, indent=2))
