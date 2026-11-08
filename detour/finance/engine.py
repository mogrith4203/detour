"""Deterministic 360-degree financial picture for one synthetic customer.

Everything here is plain arithmetic over customer.json: a snapshot of all
accounts, a daily cash forecast, four health indicators (including Scam
Exposure) and a what-if simulator. No randomness, no model calls.
"""
import calendar
import copy
import json
from datetime import date, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).with_name("customer.json")
FORECAST_DAYS = 60
COVERAGE_DAYS = 30
CHECKING_WATCH = 500.0
SCAM_WATCH = 3000.0
SCAM_RISK = 10000.0
LOANS = ("auto", "personal")
LOAN_WORDS = {"auto": "auto loan", "personal": "personal loan"}


# ---------- small helpers ----------

def _r(x):
    """Round money to cents (and never return -0.0)."""
    return round(x, 2) + 0.0


def money(x):
    """'$1,180' / '$213.33' / '-$213.33'."""
    x = _r(x)
    s = f"${abs(x):,.2f}"
    if s.endswith(".00"):
        s = s[:-3]
    return ("-" if x < 0 else "") + s


def _day(d):
    """'Nov 9' style date for sentences."""
    return f"{d:%b} {d.day}"


def _acct(c, acct_id):
    return next(a for a in c["accounts"] if a["id"] == acct_id)


def _as_of(c):
    return date.fromisoformat(c["as_of"])


def load_customer():
    """Load the synthetic customer record."""
    return json.loads(DATA_FILE.read_text())


# ---------- scenario application ----------

def _cd_penalty(cd):
    return _r(cd["balance"] * cd["apy"] / 100 * cd["early_withdrawal_penalty_days"] / 365)


def _remaining_interest(balance, apr, payment):
    """Interest still to be paid on an amortizing loan, and months left."""
    rate, total, months = apr / 1200, 0.0, 0
    while balance > 0.005 and months < 600:
        interest = balance * rate
        total += interest
        balance += interest - payment
        months += 1
    return _r(total), months


def _apply(c, events):
    """Return (state, normalized events): a copy of the customer with every
    scenario event's lasting effect applied, plus the events with dates and
    actual amounts resolved."""
    state = copy.deepcopy(c)
    default_date = c["as_of"]
    resolved = []
    for raw in sorted(events or [], key=lambda e: e.get("date") or default_date):
        ev = dict(raw, date=raw.get("date") or default_date)
        kind = ev["type"]
        if kind == "payment":
            ev["amount"] = _r(float(ev["amount"]))
            _acct(state, ev.get("from", "checking"))["balance"] -= ev["amount"]
        elif kind == "break_cd":
            cd = _acct(state, "cd")
            ev["penalty"] = _cd_penalty(cd)
            ev["amount"] = _r(cd["balance"] - ev["penalty"])
            ev["from"] = "cd"
            _acct(state, "savings")["balance"] += ev["amount"]
            cd["balance"] = 0.0
        elif kind == "extra_loan_payment":
            loan = _acct(state, ev["loan"])
            ev["amount"] = _r(min(float(ev["amount"]), loan["balance"]))
            ev["balance_before"] = _r(loan["balance"])
            _acct(state, ev.get("from", "checking"))["balance"] -= ev["amount"]
            loan["balance"] = _r(loan["balance"] - ev["amount"])
            ev["paid_off"] = loan["balance"] <= 0.005
            if ev["paid_off"]:
                loan["paid_off"] = ev["date"]
        elif kind == "lock_savings":
            sav = _acct(state, "savings")
            ev["amount"] = _r(min(float(ev["amount"]), max(sav["balance"], 0.0)))
            sav["locked_amount"] = _r(sav.get("locked_amount", 0.0) + ev["amount"])
        else:
            raise ValueError(f"unknown scenario event type: {kind}")
        for a in state["accounts"]:
            a["balance"] = _r(a["balance"])
        resolved.append(ev)
    return state, resolved


def _active_payments(state, on=None):
    """Loan/card payments still owed (on a given date, if one is passed)."""
    out = []
    for a in state["accounts"]:
        if "payment" not in a:
            continue
        paid_off = a.get("paid_off")
        if paid_off and (on is None or date.fromisoformat(paid_off) <= on):
            continue
        out.append(a)
    return out


def _monthly_income(c):
    return _r(sum(i["amount"] for i in c["income"]))


def _monthly_debt_payments(state):
    return _r(sum(a["payment"] for a in _active_payments(state)))


def _monthly_spending(state):
    """Essentials + household bills + required loan/card/mortgage payments."""
    bills = sum(b["amount"] for b in state["bills"])
    return _r(state["essentials_monthly"] + bills + _monthly_debt_payments(state))


# ---------- public engine ----------

def snapshot(c):
    """All accounts on one page with totals."""
    accounts = []
    for a in c["accounts"]:
        locked_amount = _r(a.get("locked_amount", 0.0))
        acct = dict(a, balance=_r(a["balance"]), locked=locked_amount > 0)
        if a["id"] == "card":
            acct["available_credit"] = _r(a["limit"] - a["balance"])
        if a["id"] == "cd":
            acct["early_withdrawal_penalty"] = _cd_penalty(a)
        accounts.append(acct)
    assets = sum(a["balance"] for a in accounts if a["kind"] == "asset")
    liabilities = sum(a["balance"] for a in accounts if a["kind"] == "liability")
    liquid = sum(a["balance"] for a in accounts if a["liquid"])
    return {
        "as_of": c["as_of"],
        "synthetic": True,
        "customer": c["customer"],
        "accounts": accounts,
        "totals": {
            "assets": _r(assets),
            "liabilities": _r(liabilities),
            "net_worth": _r(assets - liabilities),
            "liquid_cash": _r(liquid),
        },
    }


def forecast(c, days=FORECAST_DAYS, events=None):
    """Daily end-of-day checking/savings ledger starting at the as-of date."""
    state, resolved = _apply(c, events)
    bal = {"checking": _acct(c, "checking")["balance"], "savings": _acct(c, "savings")["balance"]}
    start = _as_of(c)
    ledger, upcoming = [], []
    for i in range(int(days)):
        d = start + timedelta(days=i)
        notes = []

        def move(acct, amount, label, scheduled=False):
            bal[acct] += amount
            notes.append(f"{label} {'+' if amount >= 0 else '-'}{money(abs(amount))} ({acct})")
            if scheduled and amount < 0:
                upcoming.append({"date": d.isoformat(), "label": label, "amount": _r(-amount)})

        for inc in c["income"]:
            if inc["day"] == d.day:
                move(inc["to"], inc["amount"], inc["label"])
        for bill in c["bills"]:
            if bill["day"] == d.day:
                move(bill["from"], -bill["amount"], bill["label"], scheduled=True)
        for loan in _active_payments(state, on=d):
            if loan["due_day"] == d.day:
                label = f"{loan['name']} payment" + (" (autopay)" if loan.get("autopay") else "")
                move(loan["pay_from"], -loan["payment"], label, scheduled=True)
        for ev in resolved:
            if ev["date"] != d.isoformat() or ev["type"] == "lock_savings":
                continue
            if ev["type"] == "payment":
                move(ev.get("from", "checking"), -ev["amount"], ev.get("label") or "Payment")
            elif ev["type"] == "break_cd":
                move("savings", ev["amount"], f"CD broken early (after {money(ev['penalty'])} penalty)")
            else:
                move(ev.get("from", "checking"), -ev["amount"], f"Extra {LOAN_WORDS[ev['loan']]} payment")
        bal["checking"] -= c["essentials_monthly"] / calendar.monthrange(d.year, d.month)[1]
        ledger.append({"date": d.isoformat(), "checking": _r(bal["checking"]),
                       "savings": _r(bal["savings"]), "events": notes})

    low = min(ledger, key=lambda row: row["checking"])
    return {
        "synthetic": True,
        "days": ledger,
        "min_checking": low["checking"],
        "min_date": low["date"],
        "overdraft_dates": [row["date"] for row in ledger if row["checking"] < 0],
        "next_bills": upcoming[:8],
        "bills_total": _r(sum(b["amount"] for b in upcoming)),
        "monthly_income": _monthly_income(c),
        "monthly_outflow": _monthly_spending(state),
        "monthly_net": _r(_monthly_income(c) - _monthly_spending(state)),
    }


def _status(good, risk):
    return "risk" if risk else ("good" if good else "watch")


def _scam_exposure(state):
    """Money that could leave within one hour, by rail."""
    chk, sav = _acct(state, "checking"), _acct(state, "savings")
    card = _acct(state, "card")
    locked = _r(sav.get("locked_amount", 0.0))
    pool = max(chk["balance"] + sav["balance"] - locked, 0.0)
    rails = chk["zelle_daily_limit"] + chk["wire_daily_limit"]
    deposits = _r(min(pool, rails))
    cash_advance = _r(max(card["limit"] - card["balance"], 0.0))
    return {"deposits": deposits, "cash_advance": cash_advance,
            "locked": locked, "total": _r(deposits + cash_advance)}


def indicators(c, events=None):
    """The four health indicators, after any scenario events."""
    state, _ = _apply(c, events)
    chk, sav = _acct(state, "checking")["balance"], _acct(state, "savings")["balance"]
    spend = _monthly_spending(state)

    runway = round((chk + sav) / spend, 2)
    ind_runway = {
        "id": "liquidity_runway", "name": "Cash Runway", "value": runway, "unit": "months",
        "display": f"{runway:.1f} months",
        "status": "good" if runway >= 6 else ("watch" if runway >= 3 else "risk"),
        "explanation": (f"Your checking and savings ({money(chk + sav)}) would cover "
                        f"{runway:.1f} months of your {money(spend)} monthly costs if income stopped."),
        "formula": "(checking + savings) divided by monthly living costs, bills and required payments",
        "monthly_spending": spend,
    }

    fc = forecast(c, COVERAGE_DAYS, events)
    low, low_date = fc["min_checking"], date.fromisoformat(fc["min_date"])
    over = fc["overdraft_dates"]
    if over:
        expl = (f"Checking would go below $0 on {len(over)} of the next {COVERAGE_DAYS} days, "
                f"starting {_day(date.fromisoformat(over[0]))}, and bottom out at {money(low)} on {_day(low_date)}.")
    else:
        expl = (f"Checking stays above $0 for the next {COVERAGE_DAYS} days while {money(fc['bills_total'])} "
                f"of bills and payments come out; the low point is {money(low)} on {_day(low_date)}.")
    ind_cover = {
        "id": "obligation_coverage", "name": "Bill Coverage", "value": low, "unit": "$",
        "display": f"{money(low)} low point",
        "status": _status(low >= CHECKING_WATCH, bool(over)),
        "explanation": expl,
        "formula": f"lowest projected checking balance over the next {COVERAGE_DAYS} days, after every scheduled bill",
        "min_date": fc["min_date"], "overdraft_days": len(over), "bills_due": fc["bills_total"],
    }

    income = _monthly_income(state)
    debt_pay = _monthly_debt_payments(state)
    card = _acct(state, "card")
    dti = round(debt_pay / income * 100, 1)
    util = round(card["balance"] / card["limit"] * 100, 1)
    fails = (dti >= 36) + (util >= 30)
    ind_debt = {
        "id": "debt_credit_health", "name": "Debt & Credit", "value": dti, "unit": "%",
        "display": f"DTI {dti:.1f}% · card use {util:.1f}%",
        "status": ["good", "watch", "risk"][fails],
        "explanation": (f"{money(debt_pay)} of your {money(income)} monthly income goes to loan, card and "
                        f"mortgage payments ({dti:.1f}%), and you are using {util:.1f}% of your card limit."),
        "formula": "monthly debt payments divided by monthly income; card balance divided by card limit",
        "dti_pct": dti, "utilization_pct": util,
    }

    exp = _scam_exposure(state)
    unlocked_savings = _r(max(sav - exp["locked"], 0.0))
    if unlocked_savings > 0:
        locked_state = copy.deepcopy(state)
        _acct(locked_state, "savings")["locked_amount"] = _r(max(sav, 0.0))
        if_locked = _scam_exposure(locked_state)["total"]
        lock_note = (f"Locking your {money(unlocked_savings)} of unlocked savings would cut this to "
                     f"{money(if_locked)}.")
    else:
        lock_note = "Your savings is locked, so only checking and the card's cash advance remain exposed."
    ind_scam = {
        "id": "scam_exposure", "name": "Scam Exposure", "value": exp["total"], "unit": "$",
        "display": f"{money(exp['total'])} could leave in 1 hour",
        "status": _status(exp["total"] < SCAM_WATCH, exp["total"] >= SCAM_RISK),
        "explanation": (f"If someone talked you into it, {money(exp['deposits'])} could leave by Zelle or wire "
                        f"and {money(exp['cash_advance'])} by card cash advance within an hour. {lock_note}"),
        "formula": ("unlocked checking + savings (capped by Zelle and wire daily limits) "
                    "+ card cash advance available (limit minus balance)"),
        **{f"{k}_part": v for k, v in exp.items() if k != "total"},
    }
    return [ind_runway, ind_cover, ind_debt, ind_scam]


# ---------- what-if ----------

HIGHER_IS_BETTER = {"liquidity_runway": True, "obligation_coverage": True,
                    "debt_credit_health": False, "scam_exposure": False}


def _summary(fc):
    over = fc["overdraft_dates"]
    last = fc["days"][-1]
    return {"days": len(fc["days"]), "min_checking": fc["min_checking"], "min_date": fc["min_date"],
            "first_overdraft": over[0] if over else None, "overdraft_days": len(over),
            "end_checking": last["checking"], "end_savings": last["savings"],
            "monthly_net": fc["monthly_net"]}


def _fmt_value(ind, v):
    if ind["unit"] == "months":
        return f"{v:.1f} months"
    if ind["unit"] == "%":
        return f"{v:.1f}%"
    return money(v)


def _event_facts(c, resolved):
    facts = []
    for ev in resolved:
        d = _day(date.fromisoformat(ev["date"]))
        src = ev.get("from", "checking")
        if ev["type"] == "payment":
            facts.append(f"Scenario: {ev.get('label') or 'a payment'} of {money(ev['amount'])} from {src} on {d}.")
        elif ev["type"] == "break_cd":
            facts.append(f"Breaking the CD on {d} moves {money(ev['amount'])} to savings after a "
                         f"{money(ev['penalty'])} early-withdrawal penalty (90 days of interest).")
        elif ev["type"] == "lock_savings":
            facts.append(f"Locking {money(ev['amount'])} of savings stops it from moving digitally "
                         f"until you unlock it in person or by verified call.")
        else:
            loan = _acct(c, ev["loan"])
            name = LOAN_WORDS[ev["loan"]]
            before_int, months = _remaining_interest(ev["balance_before"], loan["apr"], loan["payment"])
            if ev["paid_off"]:
                facts.append(f"Paying off the {name} ({money(ev['amount'])}) from {src} on {d} saves about "
                             f"{money(before_int)} of interest over the remaining {months} payments.")
                facts.append(f"It frees up {money(loan['payment'])} a month that would no longer leave checking.")
            else:
                after_int, _ = _remaining_interest(ev["balance_before"] - ev["amount"], loan["apr"], loan["payment"])
                facts.append(f"Paying {money(ev['amount'])} extra on the {name} from {src} on {d} lowers the balance "
                             f"to {money(ev['balance_before'] - ev['amount'])} and saves about "
                             f"{money(before_int - after_int)} of interest; the {money(loan['payment'])} "
                             f"monthly payment stays the same.")
    return facts


def _cashflow_facts(c, fc_before, fc_after):
    facts = []
    over_after, over_before = fc_after["overdraft_dates"], fc_before["overdraft_dates"]
    if over_after and (not over_before or over_after[0] < over_before[0]):
        rows = {row["date"]: row for row in fc_after["days"]}
        first = rows[over_after[0]]
        facts.append(f"Checking would first drop below $0 on {_day(date.fromisoformat(first['date']))}, "
                     f"to {money(first['checking'])}.")
        mortgage = _acct(c, "mortgage")
        for row in fc_after["days"]:
            d = date.fromisoformat(row["date"])
            prev = rows.get((d - timedelta(days=1)).isoformat())
            if d.day == mortgage["due_day"] and prev and prev["checking"] < 0 and d.isoformat() > first["date"]:
                facts.append(f"On {_day(d)} the {money(mortgage['payment'])} mortgage autopay would hit an account "
                             f"already at {money(prev['checking'])}, leaving checking at {money(row['checking'])} that day.")
                break
        facts.append(f"Checking would be below $0 on {len(over_after)} of the next {len(fc_after['days'])} days "
                     f"(versus {len(over_before)} without this).")
    elif fc_after["min_checking"] != fc_before["min_checking"]:
        facts.append(f"The lowest checking balance over the next {len(fc_after['days'])} days moves from "
                     f"{money(fc_before['min_checking'])} to {money(fc_after['min_checking'])}.")
    sav_b, sav_a = fc_before["days"][-1]["savings"], fc_after["days"][-1]["savings"]
    if sav_a != sav_b:
        facts.append(f"Savings would end up at {money(sav_a)} instead of {money(sav_b)}.")
    return facts


def whatif(c, scenario):
    """Simulate a list of events against the whole picture and explain the change."""
    _, resolved = _apply(c, scenario)
    ind_b, ind_a = indicators(c), indicators(c, scenario)
    fc_b, fc_a = forecast(c), forecast(c, events=scenario)
    deltas, delta_facts = [], []
    for b, a in zip(ind_b, ind_a):
        if a["value"] == b["value"]:
            direction = "same"
        else:
            better = (a["value"] > b["value"]) == HIGHER_IS_BETTER[b["id"]]
            direction = "better" if better else "worse"
        deltas.append({"id": b["id"], "name": b["name"], "before": b["value"], "after": a["value"],
                       "before_display": b["display"], "after_display": a["display"],
                       "before_status": b["status"], "after_status": a["status"], "direction": direction})
        if direction != "same":
            delta_facts.append(f"{b['name']} goes from {_fmt_value(b, b['value'])} ({b['status']}) to "
                               f"{_fmt_value(a, a['value'])} ({a['status']}).")
    return {
        "synthetic": True,
        "scenario": resolved,
        "before": {"indicators": ind_b, "forecast_summary": _summary(fc_b)},
        "after": {"indicators": ind_a, "forecast_summary": _summary(fc_a)},
        "deltas": deltas,
        "facts": _event_facts(c, resolved) + _cashflow_facts(c, fc_b, fc_a) + delta_facts,
    }
