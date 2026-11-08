"""Parity: the phone-side claim resolver (static/resolver.js in Node) must resolve exactly like detour/resolver.py."""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DETOUR_MOCK"] = "1"

from detour.claims import mock_claim, normalize_claim  # noqa: E402
from detour.data import BENIGN_SMS, EVAL, PHONE_SAMPLES  # noqa: E402
from detour.resolver import BUSINESSES, CONTACTS, msg_hash, number_hash, resolve_claim  # noqa: E402

NODE = shutil.which("node") or ("/opt/node22/bin/node" if os.path.exists("/opt/node22/bin/node") else None)
pytestmark = pytest.mark.skipif(not NODE, reason="node is not installed")

HAND = [
    ({"claims_identity": True, "kind": "family", "name": "Jake", "relation": "grandson"}, "(682) 555-0177"),
    ({"claims_identity": True, "kind": "family", "name": "jake", "relation": None}, "(214) 555-0130"),
    ({"claims_identity": True, "kind": "family", "name": None, "relation": "grandchild"}, ""),
    ({"claims_identity": True, "kind": "family", "name": None, "relation": "granddaughter"}, ""),
    ({"claims_identity": True, "kind": "family", "name": None, "relation": "son"}, ""),  # Tom vs Mia: child group ambiguous
    ({"claims_identity": True, "kind": "family", "name": "Bob", "relation": None}, ""),
    ({"claims_identity": True, "kind": "business", "business": "Lakeview Credit Union fraud dept"}, "(469) 555-0187"),
    ({"claims_identity": True, "kind": "business", "business": "Lakeview"}, "+1 (800) 555-0142"),
    ({"claims_identity": True, "kind": "government", "business": "IRS"}, ""),
    ({"claims_identity": True, "kind": "business", "business": None}, ""),
    ({"claims_identity": False, "kind": "unknown"}, ""),
    (None, ""),
    ({"claims_identity": True, "kind": "friend", "name": "RUTH ", "relation": None}, "4695550132"),
]


def cases():
    out = [{"claim": c, "sender": s, "text": ""} for c, s in HAND]
    texts = [(m["text"], m["sender"]) for m in EVAL] + [(s["text"], s["sender"]) for s in PHONE_SAMPLES] + [(t, "") for t in BENIGN_SMS]
    texts += [("grandma it's jake, i got arrested, need $3000 for bail, dont tell mom", "(682) 555-0177"),
              ("Lakeview fraud dept: your card is locked, verify now", "(469) 555-0187")]
    for t, s in texts:
        out.append({"claim": normalize_claim(mock_claim(t)), "sender": s, "text": t})
    return out


def test_resolver_parity(tmp_path):
    cs = cases()
    (tmp_path / "c.json").write_text(json.dumps(cs))
    p = subprocess.run([NODE, os.path.join(ROOT, "tests", "resolver_parity.js"), str(tmp_path / "c.json")],
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    js = json.loads(p.stdout)
    assert js["data"]["contacts"] == CONTACTS and js["data"]["businesses"] == BUSINESSES
    diffs = []
    for c, j in zip(cs, js["out"]):
        py = {"r": resolve_claim(c["claim"], None, c["sender"]), "nh": number_hash(c["sender"]), "mh": msg_hash(c["text"])}
        if py != j:
            diffs.append(f"{c}: py={py} js={j}")
    assert not diffs, "\n".join(diffs[:20])
    assert len(cs) > 40


def test_resolver_behaviour():
    jake = resolve_claim(normalize_claim(mock_claim("grandma it's jake, i got arrested, need $3000 for bail, dont tell mom")), None, "(682) 555-0177")
    assert jake["match"] == "contact" and jake["contact_id"] == "c-jake" and not jake["from_real_number"]
    assert resolve_claim({"claims_identity": True, "kind": "family", "relation": "son"})["match"] == "none"  # ambiguous: never guess
    lv = resolve_claim(normalize_claim(mock_claim("Lakeview fraud dept: your card is locked, verify now")))
    assert lv["match"] == "business" and lv["business_id"] == "lakeview"
