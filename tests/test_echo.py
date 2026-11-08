"""Identity Echo, Time hold, Reality tripwires/canary, Space signals and the 2-signal gauntlet (MOCK mode, no network)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DETOUR_MOCK"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
from detour.resolver import msg_hash, number_hash, resolve_claim  # noqa: E402

A = {"x-detour-admin": "1"}
SCAM = "grandma it's jake, i got arrested, need $3000 for bail, dont tell mom"
SCAMMER = "(682) 555-0177"
LAKE_FAKE = "Lakeview fraud dept: your card is locked. Verify now at lakeview-secure.example or call (469) 555-0187"
LAKE_REAL = ("Lakeview Credit Union: a $980 charge was flagged. Open the Lakeview app to review it. "
             "We will never ask for your PIN.")


@pytest.fixture()
def c():
    cl = TestClient(server.app)
    assert cl.post("/api/reset", headers=A).status_code == 200
    assert cl.post("/api/seed", headers=A).status_code == 200
    return cl


def phone_echo(c, text, sender, consented=True):
    """What the browser does: claim (server) → resolve on phone → start echo with hashes only."""
    claim = c.post("/api/echo/claim", json={"text": text, "sender": sender}).json()
    assert claim["mode"] == "mock"
    r = resolve_claim(claim["claim"], None, sender)
    body = {"customer": "linda", "consented": consented, "target_kind": r["match"], "number_hash": r["number_hash"] or "",
            "business_id": r["business_id"] or "", "msg_hash": msg_hash(text), "claim_kind": claim["claim"]["kind"],
            "relation": r["relation"], "money_ask": claim["claim"]["money_ask"], "sender": sender}
    return claim, r, c.post("/api/echo/start", json=body).json()


def bail(c, sender=SCAMMER):
    return c.post("/api/pnc/pay", json={"to_handle": "bailhelp.jake@zelle.example", "amount": 3000,
                                         "memo": "Jake bail - family emergency", "linked_sender": sender}).json()


def test_scam_path_not_me_cancels_payment_and_learns(c):
    claim, r, st = phone_echo(c, SCAM, SCAMMER)
    assert claim["claim"]["name"] == "Jake" and r["match"] == "contact" and st["status"] == "pending"
    pay = bail(c)
    assert pay["status"] == "held" and pay["hold_until"]  # impersonation claim + large new payee = 2 families
    assert {s["family"] for s in pay["signals"]} >= {"bank", "message"}
    inbox = c.get("/api/echo/inbox", params={"who": "jake"}).json()["items"]
    assert len(inbox) == 1 and "jail" not in inbox[0]["prompt"] and "3000" not in inbox[0]["prompt"]
    rec = c.post("/api/echo/answer", json={"echo_id": st["echo_id"], "answer": "not_me", "who": "jake"}).json()
    assert rec["trusted"] and rec["outcome"]["label"] == "scam" and rec["outcome"]["diverted"]
    assert "isn't him" in rec["outcome"]["message"]
    assert SCAMMER.lower() in rec["outcome"]["tripwires"]
    pays = c.get("/api/pnc/payments").json()["items"]
    assert pays[0]["status"] == "cancelled"
    g = c.get("/api/gauntlet", params={"payment_id": pays[0]["id"]}).json()
    assert g["action"] == "cancel" and g["independent"] >= 2
    import time as _t
    for _ in range(50):
        sk = c.get("/api/echo/status", params={"echo_id": st["echo_id"]}).json()["outcome"]["skill"]
        if not sk.get("pending"):
            break
        _t.sleep(0.05)
    assert sk["version"] is not None and sk["promoted"] is not None
    ev = [e["agent"] for e in c.get("/api/events").json()["events"]]
    for agent in ("Claim extractor", "Identity Echo", "Ground-truth label", "Skill forge", "Gate (tests)"):
        assert agent in ev


def test_echo_payload_is_content_free(c):
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    blob = json.dumps(st["payload"]).lower()
    for word in ("arrested", "bail", "3000", "dont tell", "grandma", "jake"):
        assert word not in blob, word
    assert set(st["payload"]) <= {"type", "from_customer", "claim_kind", "relation", "ask", "asked_at", "target", "msg_hash"}
    assert set(st["payload"]["target"]) == {"number_hash"}


def test_business_sees_only_hash(c):
    _, r, st = phone_echo(c, LAKE_FAKE, "(469) 555-0187")
    assert r["match"] == "business" and st["status"] == "answered" and st["answer"] == "not_me"
    assert "didn't send" in st["outcome"]["message"]
    assert set(st["payload"]["target"]) == {"business_id"} and len(st["payload"]["msg_hash"]) == 16
    assert "verify" not in json.dumps(st["payload"]).lower()
    _, _, ok = phone_echo(c, LAKE_REAL, "(800) 555-0142")
    assert ok["answer"] == "yes" and ok["outcome"]["label"] == "confirmed"


def test_yes_from_trusted_line_releases(c):
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    pay = bail(c)
    assert pay["status"] == "held"
    rec = c.post("/api/echo/answer", json={"echo_id": st["echo_id"], "answer": "yes", "who": "jake"}).json()
    assert rec["outcome"]["message"].startswith("✓ Confirmed by Jake")
    assert c.get("/api/pnc/payments").json()["items"][0]["status"] == "released"


def test_sim_swap_makes_answer_untrusted_and_hold_stays(c):
    c.post("/api/carrier/signals", json={"who": "jake", "sim_swap": True})
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    bail(c)
    rec = c.post("/api/echo/answer", json={"echo_id": st["echo_id"], "answer": "yes", "who": "jake"}).json()
    assert rec["trusted"] is False and any("SIM" in r for r in rec["trust_reasons"])
    p = c.get("/api/pnc/payments").json()["items"][0]
    assert p["status"] == "held" and any(s["name"] == "echo_untrusted" for s in p["signals"])


def test_no_answer_is_never_safe(c):
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    bail(c)
    rec = c.post("/api/echo/timeout", json={"echo_id": st["echo_id"]}).json()
    assert rec["status"] == "no_answer" and any("safe word" in f for f in rec["fallback"])
    assert c.get("/api/pnc/payments").json()["items"][0]["status"] == "held"


def test_single_signal_only_warns(c):
    p = c.post("/api/pnc/pay", json={"to_handle": "newfriend@zelle.example", "amount": 2500, "memo": "rent share"}).json()
    assert p["status"] == "sent" and len({s["family"] for s in p["signals"]}) == 1


def test_consent_and_money_ask_required_and_rate_limit(c):
    _, _, st = phone_echo(c, SCAM, SCAMMER, consented=False)
    assert st["status"] == "skipped"
    _, _, st = phone_echo(c, "hi grandma it's jake, see you sunday!", SCAMMER)
    assert st["status"] == "skipped"
    statuses = [phone_echo(c, SCAM, f"(682) 555-01{i:02d}")[2]["status"] for i in range(8)]
    assert "rate_limited" in statuses


def test_real_number_is_detected_but_never_auto_confirms():
    r = resolve_claim({"claims_identity": True, "kind": "family", "name": "Jake"}, None, "(214) 555-0130")
    assert r["from_real_number"] and r["number_hash"] == number_hash("2145550130")


def test_decoy_canary_tripwire_kanon(c):
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    c.post("/api/echo/answer", json={"echo_id": st["echo_id"], "answer": "not_me", "who": "jake"})
    stall = c.post("/api/echo/decoy_say", json={"echo_id": st["echo_id"], "text": "hello? grandma are you there"}).json()
    assert stall["reply"] and stall["canary"] is None and stall["time_burned_s"] >= 0
    pay_ask = c.post("/api/echo/decoy_say", json={"echo_id": st["echo_id"],
                                                  "text": "whats ur card number grandma, or zelle to cashout.91@zelle.example"}).json()
    assert pay_ask["canary"] and len(pay_ask["canary"]["last4"]) == 4
    assert "cashout.91@zelle.example" in pay_ask["tripwires"]
    fired = c.post("/api/pnc/card_auth", json={"token": pay_ask["canary"]["token"], "merchant": "QuickCash ATM (simulated)",
                                               "payout_account": "payout.x91@cashapp.example"}).json()
    assert fired["fired"] and fired["tripwired"] and fired["attribution"]["scammer_number"] == SCAMMER
    import hashlib
    h = hashlib.sha256(b"payout.x91@cashapp.example").hexdigest()
    k = c.get("/api/pnc/kanon", params={"prefix": h[:5]}).json()
    assert k["chars_received"] == 5 and h in k["range"]  # PNC compares locally
    h2 = hashlib.sha256(b"grandma.linda@zelle.example").hexdigest()
    assert h2 not in c.get("/api/pnc/kanon", params={"prefix": h2[:5]}).json()["range"]
    assert c.get("/api/pnc/kanon", params={"prefix": "payout"}).status_code == 400
    again = c.post("/api/pnc/card_auth", json={"token": pay_ask["canary"]["token"], "payout_account": "linda@zelle.example"}).json()
    assert again["fired"] is False  # a canary fires once; a scammer can't tripwire arbitrary accounts with it
    assert c.post("/api/pnc/card_auth", json={"token": "cny_fake", "payout_account": "x"}).json()["fired"] is False


def test_payment_after_denial_is_cancelled_immediately(c):
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    c.post("/api/echo/answer", json={"echo_id": st["echo_id"], "answer": "not_me", "who": "jake"})
    assert bail(c)["status"] == "cancelled"


def test_carrier_token_content_free(c):
    c.post("/api/carrier/signals", json={"who": "linda", "unknown_call": True})
    t = c.get("/api/carrier/token", params={"who": "linda"}).json()
    assert t["signals"]["active_call_unknown_number"] and t["contains_message_content"] is False and t["simulated"]


def test_wrong_answerer_rejected(c):
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    assert c.post("/api/echo/answer", json={"echo_id": st["echo_id"], "answer": "yes"}).status_code == 404
    assert c.post("/api/echo/answer", json={"echo_id": st["echo_id"], "answer": "yes", "who": "mia"}).status_code == 404


def test_replayed_business_text_cannot_release_scam_payment(c):
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    assert bail(c)["status"] == "held"
    _, _, biz = phone_echo(c, LAKE_REAL, SCAMMER)  # scammer forwards the real Lakeview alert from his own number
    assert biz["answer"] == "yes" and biz["outcome"]["payments"] == []
    assert c.get("/api/pnc/payments").json()["items"][0]["status"] == "held"


def test_flooded_target_inbox_still_holds(c):
    for i in range(2):
        phone_echo(c, SCAM, f"(682) 555-01{50 + i}")
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    assert st["status"] == "rate_limited"
    assert bail(c)["status"] == "held"


def test_denial_never_tripwires_real_customer_lines(c):
    c.post("/api/echo/claim", json={"text": "grandma it's jake, need $3000 bail, call my mom at (214) 555-0131", "sender": SCAMMER})
    _, _, st = phone_echo(c, SCAM, SCAMMER)
    rec = c.post("/api/echo/answer", json={"echo_id": st["echo_id"], "answer": "not_me", "who": "jake"}).json()
    trips = [t["account"] for t in c.get("/api/pnc/tripwires").json()["items"]]
    assert "(214) 555-0131" not in trips and SCAMMER.lower() in trips and rec["outcome"]["label"] == "scam"


def test_customer_cannot_release_during_cooling_off(c):
    phone_echo(c, SCAM, SCAMMER)
    p = bail(c)
    assert c.post("/api/pnc/release", json={"payment_id": p["id"], "by": "customer"}).json()["status"] == "held"
    assert c.post("/api/pnc/release", json={"payment_id": p["id"], "by": "trusted_contact"}).json()["status"] == "released"


def test_safety_guard_replaces_unsafe_decoy_reply():
    from types import SimpleNamespace
    from detour.core import Agents
    from detour.data import PERSONAS

    class FakeLLM:
        mock, small_model, model, safety_model, mode = False, "small-m", "big-m", "guard-m", "live"

        def text(self, msgs, **kw):
            assert kw.get("model") == "small-m"  # routing: the persona uses the small model
            return "something the guard will flag"

        def safety(self, user_text, reply):
            return False, "Threat", "live"

    out, meta = Agents(FakeLLM()).persona_reply(PERSONAS["decoy-01"], [{"who": "scammer", "text": "hi", "sender": ""}])
    assert out != "something the guard will flag" and meta["filtered"] and meta["guard"]["verdict"] == "unsafe"
    assert meta["model"] == "small-m"


def test_safety_parser_reads_response_safety(monkeypatch):
    from types import SimpleNamespace
    from detour.llm import Nemotron
    n = Nemotron()
    n.mock, n.safety_model, n.replay = False, "guard-m", False
    monkeypatch.setattr(n, "chat", lambda *a, **k: SimpleNamespace(
        content='{"User Safety": "unsafe", "Response Safety": "safe", "Safety Categories": "PII/Privacy"}'))
    assert n.safety("u", "r")[0] is True  # judged on the decoy's reply, not the scammer's message
    monkeypatch.setattr(n, "chat", lambda *a, **k: SimpleNamespace(content='{"Response Safety": "unsafe", "Safety Categories": "Threat"}'))
    assert n.safety("u", "r")[:2] == (False, "Threat")


def test_claim_normalizes_model_synonyms_and_rules_backfill():
    from types import SimpleNamespace
    from detour.claims import extract_claim, normalize_claim
    assert normalize_claim({"kind": "bank", "business": "Lakeview Credit Union", "claims_identity": "true"})["kind"] == "business"

    class L:
        mode = "live"

        def json(self, *a, **k):
            return {"claims_identity": False, "kind": "unknown"}
    c, mode = extract_claim(L(), "Lakeview fraud dept: your card is locked. Verify now")
    assert c["business"] == "Lakeview" and mode == "rules"  # labeled as rules, never as the model


def test_safety_guard_privacy_only_flag_is_not_blocked():
    from detour.core import Agents
    from detour.data import PERSONAS

    class FakeLLM:
        mock, small_model, model, safety_model, mode = False, "s", "b", "g", "live"

        def text(self, msgs, **kw):
            return "Which bank, dear? Mine is Lakeview."

        def safety(self, user_text, reply):
            return False, "PII/Privacy", "live"

    out, meta = Agents(FakeLLM()).persona_reply(PERSONAS["decoy-01"], [{"who": "scammer", "text": "hi", "sender": ""}])
    assert out == "Which bank, dear? Mine is Lakeview." and not meta["filtered"] and meta["guard"]["verdict"].startswith("safe")
