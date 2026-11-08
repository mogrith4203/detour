"""Tests for the PNC 360 finance engine and coach (synthetic data)."""
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detour.finance import coach, forecast, indicators, load_customer, snapshot, whatif  # noqa: E402
from detour.finance.coach import unsupported_figures  # noqa: E402

BAIL = [{"type": "payment", "amount": 3000, "from": "checking", "date": "2026-11-09", "label": "Bail payment"}]
CAR_PAYOFF = [{"type": "extra_loan_payment", "loan": "auto", "amount": 8200, "from": "savings", "date": "2026-11-09"}]


def _ind(inds, ind_id):
    return next(i for i in inds if i["id"] == ind_id)


def test_balances_load():
    c = load_customer()
    snap = snapshot(c)
    bal = {a["id"]: a["balance"] for a in snap["accounts"]}
    assert snap["synthetic"] is True and c["synthetic"] is True
    assert bal == {"checking": 2840, "savings": 9600, "cd": 15000, "ira": 142000,
                   "auto": 8200, "personal": 3100, "card": 1650, "mortgage": 96000}
    assert snap["totals"]["liquid_cash"] == 12440
    assert snap["totals"]["net_worth"] == 60490
    json.dumps(snap)


def test_four_indicators_with_valid_status():
    inds = indicators(load_customer())
    assert [i["id"] for i in inds] == ["liquidity_runway", "obligation_coverage",
                                       "debt_credit_health", "scam_exposure"]
    for i in inds:
        assert i["status"] in {"good", "watch", "risk"}
        assert i["explanation"] and i["formula"] and i["display"]
    json.dumps(inds)


def test_bail_overdrafts_and_cuts_runway():
    c = load_customer()
    assert forecast(c, 30)["overdraft_dates"] == []
    assert forecast(c, 30, BAIL)["overdraft_dates"][0] == "2026-11-09"
    w = whatif(c, BAIL)
    runway = _ind(w["deltas"], "liquidity_runway")
    assert runway["after"] < runway["before"]
    assert w["after"]["forecast_summary"]["overdraft_days"] > 0
    assert any("mortgage" in f and "Dec 1" in f for f in w["facts"])
    assert _ind(w["after"]["indicators"], "obligation_coverage")["status"] == "risk"


def test_lock_savings_lowers_scam_exposure():
    c = load_customer()
    w = whatif(c, [{"type": "lock_savings", "amount": 9600}])
    scam = _ind(w["deltas"], "scam_exposure")
    assert scam["after"] < scam["before"]
    assert "Locking" in _ind(indicators(c), "scam_exposure")["explanation"]


def test_car_payoff_removes_payment_and_is_mixed():
    c = load_customer()
    later = [d for d in forecast(c, 60, CAR_PAYOFF)["days"] if d["date"] > "2026-11-09"]
    assert not any("Auto Loan payment" in e for d in later for e in d["events"])
    base = [d for d in forecast(c, 60)["days"] if d["date"] > "2026-11-09"]
    assert sum("Auto Loan payment" in e for d in base for e in d["events"]) == 2
    deltas = {d["id"]: d["direction"] for d in whatif(c, CAR_PAYOFF)["deltas"]}
    assert deltas["liquidity_runway"] == "worse"
    assert deltas["debt_credit_health"] == "better"


def test_coach_mock_bail_numbers_are_grounded():
    out = coach(SimpleNamespace(mock=True), "Can I afford to pay $3,000 bail?")
    assert out["mode"] == "mock"
    assert "run_whatif" in [t["tool"] for t in out["tool_trace"]]
    assert out["numbers_cited"] and out["next_steps"]
    c = load_customer()
    results = [whatif(c, [dict(BAIL[0], **{"from": src})]) for src in ("checking", "savings")]
    assert unsupported_figures(out["answer"], results) == []


def _msg(content=None, calls=None):
    tool_calls = [SimpleNamespace(id=f"t{i}", function=SimpleNamespace(name=n, arguments=json.dumps(a)))
                  for i, (n, a) in enumerate(calls or [])]
    return SimpleNamespace(content=content, tool_calls=tool_calls or None)


class ScriptedLLM:
    """Stands in for Nemotron: replays a fixed list of assistant messages."""
    mock = False

    def __init__(self, replies):
        self.replies = list(replies)

    def chat(self, messages, tools=None, **kw):
        return self.replies.pop(0)


def test_coach_live_accepts_grounded_and_rejects_invented_numbers():
    call = _msg(calls=[("get_indicators", {})])
    good = _msg(json.dumps({"answer": "You could cover 3.1 months; card use is 20.6% and $1,977 goes to debt.",
                            "next_steps": ["Lock savings"]}))
    out = coach(ScriptedLLM([call, good]), "How am I doing?")
    assert out["mode"] == "nemotron", out

    bad = _msg(json.dumps({"answer": "You have $55,555 spare.", "next_steps": []}))
    out = coach(ScriptedLLM([call, bad, bad]), "How am I doing?")
    assert out["mode"] == "fallback"
    assert "$55,555" not in out["answer"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
