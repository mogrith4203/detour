"""Conversational money coach over the deterministic engine.

Live path: Nemotron calls engine tools, and every dollar figure or percentage
in its answer is checked against the tool results it saw. Mock path: keyword
routing to the same tools with a template answer built from their facts.
"""
import json
import re
from datetime import date, timedelta

from ..llm import parse_json, strip_think
from .engine import forecast, indicators, load_customer, money, snapshot, whatif

MAX_STEPS = 6
MONEY_RE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")
PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s?%")
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
SCAM_WARNING = ("An urgent call asking for bail money is one of the most common scams aimed at older adults, "
                "so hang up and call the person or a family member on a number you already know before sending anything.")

SYSTEM_PROMPT = """You are a patient, plain-language money coach for an older bank customer (synthetic demo data).
Rules:
- Call tools before stating any number. Use only numbers that appear in tool results; never invent, estimate or do new arithmetic.
- For "can I afford / should I pay / what if" questions, call run_whatif with the scenario. Today is the as-of date in the data; use the next day for new payments unless the customer gives a date.
- If a request sounds urgent or secretive (bail, a grandchild in trouble, gift cards, "don't tell anyone"), say it matches a common scam and suggest calling family or the bank on a known number first.
- Short sentences, no jargon. Mention once, in a few words, that this is not financial advice.
- Final reply: ONLY a JSON object {"answer": "...", "next_steps": ["...", "..."]}."""

EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["payment", "break_cd", "extra_loan_payment", "lock_savings"]},
        "amount": {"type": "number"},
        "from": {"type": "string", "enum": ["checking", "savings"]},
        "date": {"type": "string", "description": "YYYY-MM-DD"},
        "label": {"type": "string"},
        "loan": {"type": "string", "enum": ["auto", "personal"]},
    },
    "required": ["type"],
}


def _tool(name, description, properties=None, required=None):
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {
        "type": "object", "properties": properties or {}, "required": required or []}}}


TOOLS = [
    _tool("get_snapshot", "All accounts, balances and totals for the customer."),
    _tool("get_indicators", "The four health indicators: cash runway, bill coverage, debt & credit, scam exposure."),
    _tool("run_forecast", "Daily checking/savings forecast with overdraft dates and upcoming bills.",
          {"days": {"type": "integer", "minimum": 7, "maximum": 90}}),
    _tool("run_whatif", "Simulate events against the whole picture; returns before/after indicators and facts.",
          {"scenario": {"type": "array", "items": EVENT_SCHEMA}}, ["scenario"]),
]


# ---------- tool execution ----------

def _run_tool(c, name, args):
    """Execute one engine tool; returns (result, short summary)."""
    if name == "get_snapshot":
        res = snapshot(c)
        t = res["totals"]
        return res, f"{len(res['accounts'])} accounts; liquid cash {money(t['liquid_cash'])}, net worth {money(t['net_worth'])}"
    if name == "get_indicators":
        res = {"indicators": indicators(c)}
        return res, "; ".join(f"{i['name']} {i['display']} ({i['status']})" for i in res["indicators"])
    if name == "run_forecast":
        res = forecast(c, days=int(args.get("days") or 30))
        res["days"] = [d for d in res["days"] if d["events"]]  # keep only days with activity
        over = res["overdraft_dates"]
        return res, (f"low {money(res['min_checking'])} on {res['min_date']}; "
                     + (f"{len(over)} overdraft days from {over[0]}" if over else "no overdrafts"))
    if name == "run_whatif":
        res = whatif(c, args.get("scenario") or [])
        changed = [d for d in res["deltas"] if d["direction"] != "same"]
        return res, "; ".join(f"{d['name']} {d['before_display']} -> {d['after_display']}" for d in changed) or "no change"
    raise ValueError(f"unknown tool {name}")


# ---------- number validation ----------

def _figures(text):
    """Dollar amounts and percentages mentioned in text, as (kind, value, raw)."""
    out = [("$", float(m.group(1).replace(",", "")), m.group(0)) for m in MONEY_RE.finditer(text)]
    out += [("%", float(m.group(1)), m.group(0)) for m in PCT_RE.finditer(text)]
    return out


def _number_pool(results):
    """Every number (absolute value) appearing anywhere in the tool results."""
    pool = set()

    def walk(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            pool.add(abs(float(x)))
        elif isinstance(x, str):
            pool.update(float(n.replace(",", "")) for n in NUM_RE.findall(x))
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(results)
    return pool


def unsupported_figures(answer, results):
    """Figures in the answer that no tool result backs up (±$1 or ±0.1%)."""
    pool = _number_pool(results)
    bad = []
    for kind, value, raw in _figures(answer):
        tol = 1.0 if kind == "$" else 0.1
        candidates = pool if kind == "$" else pool | {p * 100 for p in pool}
        if not any(abs(value - p) <= tol + 1e-9 for p in candidates):
            bad.append(raw)
    return bad


def _result(answer, next_steps, trace, mode):
    return {"answer": answer, "numbers_cited": [raw for _, _, raw in _figures(answer)],
            "next_steps": next_steps, "tool_trace": trace, "mode": mode}


# ---------- deterministic answers ----------

def _template_answer(results):
    """Plain answer built only from tool-result sentences."""
    whatifs = [r for r in results if "facts" in r]
    if whatifs:
        return " ".join(whatifs[-1]["facts"])
    inds = next((r["indicators"] for r in results if "indicators" in r), None)
    if inds:
        return " ".join(i["explanation"] for i in inds)
    snap = next((r for r in results if "totals" in r), None)
    if snap:
        t = snap["totals"]
        return f"You have {money(t['liquid_cash'])} in checking and savings and a net worth of {money(t['net_worth'])}."
    return "I couldn't pull up your accounts just now, so I won't guess at any numbers."


def _amount_in(question, default):
    m = MONEY_RE.search(question) or re.search(r"\b(\d[\d,]{2,}(?:\.\d+)?)\b", question)
    return float(m.group(1).replace(",", "")) if m else default


def _mock(c, question, trace, results):
    """Keyword-routed answer from the deterministic engine."""
    q = question.lower()
    next_day = (date.fromisoformat(c["as_of"]) + timedelta(days=1)).isoformat()

    def call(name, args=None):
        res, summary = _run_tool(c, name, args or {})
        trace.append({"tool": name, "args": args or {}, "result_summary": summary})
        results.append(res)
        return res

    if any(k in q for k in ("bail", "afford", "send", "wire")):
        amount = _amount_in(question, 3000.0)
        label = "Bail payment" if "bail" in q else "Payment"
        w = call("run_whatif", {"scenario": [{"type": "payment", "amount": amount, "from": "checking",
                                              "date": next_day, "label": label}]})
        hurts = w["after"]["forecast_summary"]["overdraft_days"] > w["before"]["forecast_summary"]["overdraft_days"]
        alt = call("run_whatif", {"scenario": [{"type": "payment", "amount": amount, "from": "savings",
                                                "date": next_day, "label": label}]})
        alt_runway, alt_cover = alt["deltas"][0], alt["deltas"][1]
        facts = [f for f in w["facts"] if not f.startswith(("Scenario:", "Scam Exposure"))]
        if hurts:
            opening = f"Paying {money(amount)} from checking right now would cause real trouble."
        else:
            opening = f"Paying {money(amount)} from checking would not overdraw your account."
        answer = " ".join([opening, *facts,
                           f"If the payment is truly needed, paying from savings instead keeps your 30-day checking "
                           f"low point at {money(alt_cover['after'])}, though your cash runway still drops to "
                           f"{alt_runway['after_display']}.",
                           SCAM_WARNING if "bail" in q else "",
                           "This is general guidance, not financial advice."]).replace("  ", " ").strip()
        steps = ["Verify the request by calling family or the court directly on a number you look up yourself.",
                 "Do not pay by Zelle, wire, gift card or cash advance to someone who called you.",
                 "Ask us to lock your savings while you check."]
        return answer, steps

    if any(k in q for k in ("pay off", "payoff", "car", "loan")):
        loan = "personal" if "personal" in q else "auto"
        bal = next(a for a in c["accounts"] if a["id"] == loan)["balance"]
        w = call("run_whatif", {"scenario": [{"type": "extra_loan_payment", "loan": loan, "amount": bal,
                                              "from": "savings", "date": next_day}]})
        answer = ("It's a trade-off. " + " ".join(w["facts"]) +
                  " Less cash on hand means less cushion for surprises. Not financial advice.")
        steps = ["Consider paying part of the loan and keeping a few months of costs in savings.",
                 "Run the numbers again with a smaller extra payment before deciding."]
        return answer, steps

    if any(k in q for k in ("scam", "lock", "protect", "fraud")):
        sav = next(a for a in c["accounts"] if a["id"] == "savings")["balance"]
        ind = call("get_indicators")["indicators"][3]
        w = call("run_whatif", {"scenario": [{"type": "lock_savings", "amount": sav}]})
        answer = f"{ind['explanation']} " + " ".join(w["facts"]) + " Not financial advice."
        steps = ["Turn on the savings lock so large moves need a verified call.",
                 "Lower your Zelle limit or turn off card cash advances if you never use them."]
        return answer, steps

    if any(k in q for k in ("overdraft", "bill", "forecast", "next month")):
        ind = call("get_indicators")["indicators"]
        fc = call("run_forecast", {"days": 60})
        cover = ind[1]["explanation"]
        tail = (f" Looking further out, money coming in falls short of money going out by "
                f"{money(-fc['monthly_net'])} a month." if fc["monthly_net"] < 0 else "")
        answer = cover + tail + " Not financial advice."
        steps = ["Move a set amount from savings to checking each month to cover the gap.",
                 "Set a low-balance alert on checking."]
        return answer, steps

    ind = call("get_indicators")["indicators"]
    call("get_snapshot")
    answer = " ".join(i["explanation"] for i in ind) + " Not financial advice."
    steps = ["Ask me a what-if, like paying off a loan or a payment someone asked you for.",
             "Consider locking savings to lower your scam exposure."]
    return answer, steps


# ---------- live tool-calling loop ----------

def _assistant_dict(msg):
    out = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        out["tool_calls"] = [{"id": tc.id, "type": "function",
                              "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                             for tc in msg.tool_calls]
    return out


def _live(llm, c, question, history, trace, results):
    """Run the tool loop; returns (answer, next_steps, mode)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *(history or []),
                {"role": "user", "content": question}]
    retried = False
    for _ in range(MAX_STEPS):
        msg = llm.chat(messages, tools=TOOLS)
        messages.append(_assistant_dict(msg))
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                try:
                    res, summary = _run_tool(c, tc.function.name, args)
                except (ValueError, KeyError, TypeError) as e:
                    res, summary = {"error": str(e)}, f"error: {e}"
                trace.append({"tool": tc.function.name, "args": args, "result_summary": summary})
                results.append(res)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res)})
            continue
        try:
            out = parse_json(msg.content or "")
            answer, steps = str(out["answer"]), [str(s) for s in out.get("next_steps", [])]
        except (ValueError, KeyError, TypeError):
            answer, steps = strip_think(msg.content or ""), []
        bad = unsupported_figures(answer, results)
        if answer and not bad and results:
            return answer, steps, "nemotron"
        if retried:
            break
        retried = True
        messages.append({"role": "user", "content": (
            f"These figures are not in any tool result: {', '.join(bad) or 'none (no tools called)'}. "
            "Call tools if needed, use only numbers from tool results, and reply with the JSON object.")})
    if not results:
        return None
    return _template_answer(results), ["Ask me a what-if to see how a choice changes these numbers."], "fallback"


def coach(llm, question, history=None):
    """Answer a money question with tool-backed numbers; never invents figures."""
    c = load_customer()
    trace, results = [], []
    if not getattr(llm, "mock", True):
        try:
            live = _live(llm, c, question, history, trace, results)
            if live:
                return _result(live[0], live[1], trace, live[2])
        except Exception as e:  # network/model failure: fall through to the deterministic path
            trace.append({"tool": "nemotron", "args": {}, "result_summary": f"live call failed: {str(e)[:120]}"})
        answer, steps = _mock(c, question, trace, results)
        return _result(answer, steps, trace, "fallback")
    answer, steps = _mock(c, question, trace, results)
    return _result(answer, steps, trace, "mock")
