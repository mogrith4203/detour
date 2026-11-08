"""Parity: the browser matcher (static/matcher.js, run in Node) must decide exactly like the Python reference."""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DETOUR_MOCK"] = "1"

from detour.core import domains, match, normalize, phones, redact, sender_status, tokens  # noqa: E402
from detour.data import BENIGN_SMS, EVAL, PHONE_SAMPLES  # noqa: E402
from detour.engine import Engine, fingerprint, strip_indicators  # noqa: E402

NODE = shutil.which("node") or ("/opt/node22/bin/node" if os.path.exists("/opt/node22/bin/node") else None)
pytestmark = pytest.mark.skipif(not NODE, reason="node is not installed")

ADVERSARIAL = [
    ("homoglyph", "(469) 555-0100", "Lаkeview Credit Union: your card is locked. Call (972) 555-0161 now."),
    ("spaced", "(469) 555-0100", "Your account is suspended. Call 9 7 2 5 5 5 0 1 7 7 today."),
    ("spaced-dots", "", "Call 9.7.2.5.5.5.0.1.7.7 to unlock your card"),
    ("bitly", "(214) 555-0111", "Your package is waiting. Pay the fee at https://bit.ly/3xYz today."),
    ("puny", "(214) 555-0112", "Verify your Lakeview account at http://xn--lkeview-hwa.com immediately."),
    ("puny-bad", "", "Login now at xn--zz9.top"),
    ("puny-upper", "", "Go to https://XN--LKEVIEW-HWA.COM/login now"),
    ("grandson-mx", "(682) 555-0140", "Hi it's your grandson, I'm in jail in Mexico. Please send cash via Western Union to my lawyer. Keep it quiet."),
    ("irs", "(817) 555-0141", "IRS: you owe back taxes. Pay with Venmo or Cash App today or face arrest."),
    ("es", "(972) 555-0142", "Abuela, soy yo. Estoy en la cárcel y necesito dinero para la fianza. No le digas a mamá."),
    ("zelle", "33622", "Your Zelle payment of $40 to Sam was sent."),
    ("empty", "", ""),
    ("long", "(214) 555-0150", ("Lakeview fraud alert, call (469) 555-0187 now. " * 60)[:2000]),
    ("emoji", "(214) 555-0151", "\U0001F6A8\U0001F6A8 Grandma \U0001F62D it's me, bail is $3,000 \U0001F4B8 please send money tonight \U0001F64F\U0001F3FD"),
    ("pii", "(214) 555-0152", "Hi Linda Park, your code is 123456. Email linda@example.com, SSN 123-45-6789, card 4111 1111 1111 1111 "
            "ending in 4417, 12 Main Street. Ref 98765432. LINDA PARK"),
    ("fullwidth", "", "Ｌａｋｅｖｉｅｗ card locked, call （９７２） 555-0161"),
    ("turkish-i", "", "İRS warnıng: pay the fıne today"),
    ("registered", "(800) 555-0142", "Lakeview Credit Union: call (469) 555-0187 to verify the $980 charge now."),
    ("registered-noask", "(800) 555-0142", "Lakeview Credit Union fraud alert: a charge was flagged. Open the Lakeview app to review it."),
    ("known", "(214) 555-0153", "Grandma it's me, bail is $3,000, send money now", True),
    ("thread", "(214) 555-0154", "Please send it via Zelle tonight.", False,
     ["Grandma it's me, I'm in trouble.", "They arrested me and I need bail."]),
]


def cases():
    out = []
    for m in EVAL:
        out.append({"id": m["id"], "text": m["text"], "sender": m["sender"]})
    for i, s in enumerate(PHONE_SAMPLES):
        out.append({"id": f"sample-{i}", "text": s["text"], "sender": s["sender"]})
    for i, t in enumerate(BENIGN_SMS):
        out.append({"id": f"benign-{i}", "text": t, "sender": ""})
    for a in ADVERSARIAL:
        out.append({"id": a[0], "sender": a[1], "text": a[2], "known": a[3] if len(a) > 3 else False,
                    "thread": a[4] if len(a) > 4 else []})
    return out


def engines():
    full = Engine()
    full.seed()
    full.good.add(fingerprint(BENIGN_SMS[0]))  # exercise the known-good hash path
    half = Engine()
    half.seed(decoys=("decoy-01",))  # every story at 'watch': "still being confirmed" cards
    empty = Engine()  # no stories: the money/authority floor and plain asks
    return {"seeded": full, "one-decoy": half, "empty": empty}


def python_side(engine, cs):
    m = match(cs["text"], engine.smap.stories)
    engine.threads.clear()
    for t in cs.get("thread", []):
        engine.check_message(t, cs["sender"], cs.get("known", False))
    res = engine.check_message(cs["text"], cs["sender"], cs.get("known", False))
    card = {k: v for k, v in res["card"].items() if k != "check_id"}
    local = next((s["data"] for s in res["steps"] if s["stage"] == "local"), None)
    return {
        "decision": m["decision"], "score": m["score"], "asks": m["asks"], "best": m["best"]["story_id"] if m["best"] else None,
        "ranked": [[r["story_id"], r["score"], r["detail"]["kw"], r["detail"]["indicator"]] for r in m["ranked"]],
        "redact": redact(cs["text"], ("Linda Park",)), "redact_plain": redact(cs["text"]), "normalize": normalize(cs["text"]),
        "phones": phones(cs["text"]), "domains": domains(cs["text"]), "tokens": tokens(cs["text"]),
        "sender": sender_status(cs["sender"]), "fingerprint": fingerprint(cs["text"]), "fingerprint_async": fingerprint(cs["text"]),
        "card": card, "local_decision": local["decision"] if local else None, "strip": strip_indicators(cs["text"]),
    }


@pytest.mark.parametrize("name", ["seeded", "one-decoy", "empty"])
def test_js_matcher_matches_python(name, tmp_path):
    eng = engines()[name]
    rules = eng.phone_rules()
    cs = cases()
    (tmp_path / "rules.json").write_text(json.dumps(rules))
    (tmp_path / "cases.json").write_text(json.dumps(cs))
    out = subprocess.run([NODE, os.path.join(ROOT, "tests", "parity.js"), str(tmp_path / "rules.json"), str(tmp_path / "cases.json")],
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    js = json.loads(out.stdout)
    assert len(js) == len(cs)
    diffs = []
    decisions = {}
    for c, j in zip(cs, js):
        py = python_side(eng, c)
        decisions[py["decision"]] = decisions.get(py["decision"], 0) + 1
        for k, v in py.items():
            if j.get(k) != v:
                diffs.append(f"{c['id']}.{k}: py={v!r} js={j.get(k)!r}")
    print(f"\n[{name}] {len(cs)} cases, decisions {decisions}, diffs {len(diffs)}")
    assert not diffs, "\n".join(diffs[:40])


def test_patterns_compile_in_js(tmp_path):
    rules = Engine().phone_rules()
    (tmp_path / "rules.json").write_text(json.dumps(rules))
    (tmp_path / "cases.json").write_text("[]")
    out = subprocess.run([NODE, os.path.join(ROOT, "tests", "parity.js"), str(tmp_path / "rules.json"), str(tmp_path / "cases.json")],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
