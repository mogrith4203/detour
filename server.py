"""Detour demo server.  Start with ./run.sh (or: uvicorn server:app --port 8000), then open http://localhost:8000"""
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import FileResponse, StreamingResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from detour.data import PERSONAS, PHONE_SAMPLES, SCENARIOS  # noqa: E402
from detour.engine import Engine  # noqa: E402

ROOT = Path(__file__).parent
app = FastAPI(title="Detour")
engine = Engine()
BENCH_FILE = ROOT / "results" / "benchmark.json"
DEMO_TOKEN = os.getenv("DEMO_TOKEN", "")
BENCH_LOCK = __import__("threading").Lock()
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

try:  # the PNC finance module is optional until it lands
    from detour import finance  # noqa: E402
except Exception:  # pragma: no cover
    finance = None


def admin_only(request: Request):
    """Admin actions (reset/seed/approve/benchmark) need a custom header, which a browser can't send cross-site without a
    CORS preflight we never allow; that blocks CSRF. They also need this laptop, or DEMO_TOKEN when bound to the network."""
    origin = request.headers.get("origin", "")
    if origin and not re.match(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$", origin):
        raise HTTPException(403, "Admin actions are only allowed from the demo page.")
    hdr = request.headers.get("x-detour-admin", "")
    host = request.client.host if request.client else ""
    if DEMO_TOKEN:
        if hdr == DEMO_TOKEN:
            return
    elif hdr and host in ("127.0.0.1", "::1", "localhost", "testclient"):
        return
    raise HTTPException(403, "Admin actions are only allowed from the demo laptop.")


class CheckIn(BaseModel):
    text: str
    sender: str = ""
    known: bool = False


class IdIn(BaseModel):
    id: str = ""
    text: str = ""
    sender: str = ""
    local: dict = {}


class OnDeviceIn(BaseModel):
    decision: str
    story_id: str = ""
    score: float = 0.0


class StoryIn(BaseModel):
    story_id: str
    number: str = ""


class LiveIn(BaseModel):
    session: str = ""
    decoy: str = "decoy-01"
    text: str = ""


class CoachIn(BaseModel):
    question: str


class WhatIfIn(BaseModel):
    scenario: list


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/state")
def state():
    return engine.state()


@app.get("/api/events")
def events(since: int = 0):
    return {"events": engine.events_since(since), "last": engine.ev_seq, "llm": engine.llm.describe(), "stats": engine.stats}


@app.get("/api/samples")
def samples():
    return PHONE_SAMPLES


# ---- decoys
@app.get("/api/honeypot")
def honeypot(scenario: str, decoy: str):
    if scenario not in SCENARIOS or decoy not in PERSONAS:
        raise HTTPException(404, "unknown scenario or decoy")
    pause = 0.6 if engine.llm.mode in ("mock", "replay") else 0.0  # pace instant replies so the demo reads well

    def stream():
        for ev in engine.honeypot_session(scenario, decoy):
            yield "data: " + json.dumps(ev) + "\n\n"
            if pause:
                time.sleep(pause)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/live/start")
def live_start(body: LiveIn):
    if body.decoy not in PERSONAS:
        raise HTTPException(404, "unknown decoy")
    return engine.live_start(body.decoy)


@app.post("/api/live/say")
def live_say(body: LiveIn):
    return engine.live_say(body.session, body.text)


@app.post("/api/live/end")
def live_end(body: LiveIn):
    return engine.live_end(body.session)


# ---- phone
@app.post("/api/check")
def check(body: CheckIn):
    """Server-side reference copy of the phone matcher. Used by tests and the benchmark; the demo phone runs static/matcher.js."""
    return engine.check_message(body.text[:2000], body.sender[:40], body.known)


@app.get("/api/phone/rules")
def phone_rules():
    """Server -> phone: story skills and rules. The phone decides on its own with these."""
    return engine.phone_rules()


@app.post("/api/phone/verdict")
def phone_verdict(body: OnDeviceIn):
    """Phone -> server: only the decision (no text, no sender), for the live counters."""
    return engine.ondevice(body.decision[:10], body.story_id[:8], body.score)


@app.post("/api/consent")
def consent(body: IdIn):
    if body.text:  # real path: the phone sends the redacted copy the customer saw
        return engine.consent_text(body.text[:1500], body.sender[:40], body.local or {})
    return engine.consent(body.id)


REPORTS = {}


@app.post("/api/report")
def report(body: StoryIn, request: Request):
    """One report per story per device per 10 minutes, so one person can't vote a play into 'warn'."""
    key = ((request.client.host if request.client else ""), body.story_id[:8])
    if time.time() - REPORTS.get(key, 0) < 600:
        raise HTTPException(429, "You already reported this one. Thanks!")
    REPORTS[key] = time.time()
    return engine.report(body.story_id[:8])


# ---- admin
@app.post("/api/approve", dependencies=[Depends(admin_only)])
def approve(body: StoryIn):
    return engine.approve_block(body.story_id, body.number)


@app.post("/api/seed", dependencies=[Depends(admin_only)])
def seed():
    return engine.seed()


@app.post("/api/reset", dependencies=[Depends(admin_only)])
def reset():
    engine.reset()
    return engine.state()


@app.post("/api/benchmark", dependencies=[Depends(admin_only)])
def benchmark():
    if not BENCH_LOCK.acquire(blocking=False):
        raise HTTPException(409, "A benchmark is already running.")
    try:
        res = Engine().benchmark()  # separate engine: never touches the live demo's story map, stats or feed
    finally:
        BENCH_LOCK.release()
    engine.emit("Scoreboard", "benchmark", output=f"Benchmark done: {res.get('api_calls', 0)} hosted calls ({res.get('mode')})", mode=res.get("mode"))
    res["ran_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    BENCH_FILE.parent.mkdir(exist_ok=True)
    BENCH_FILE.write_text(json.dumps(res, indent=2))
    return res


@app.get("/api/benchmark/last")
def benchmark_last():
    return json.loads(BENCH_FILE.read_text()) if BENCH_FILE.exists() else {}


# ---- PNC navigator
def _fin():
    if finance is None:
        raise HTTPException(503, "Finance module not loaded")
    return finance


@app.get("/api/finance/overview")
def fin_overview():
    f = _fin()
    c = f.load_customer()
    return {"snapshot": f.snapshot(c), "indicators": f.indicators(c), "forecast": f.forecast(c, 60)}


@app.post("/api/finance/whatif")
def fin_whatif(body: WhatIfIn):
    f = _fin()
    import math
    ev = body.scenario[:10]
    for e in ev:
        if not isinstance(e, dict):
            raise HTTPException(400, "Each scenario event must be an object.")
        amt = e.get("amount", 0)
        try:
            amt = float(amt)
        except (TypeError, ValueError):
            raise HTTPException(400, "amount must be a number")
        if not math.isfinite(amt) or not 0 <= amt <= 1e7:
            raise HTTPException(400, "amount must be between 0 and 10,000,000")
        e["amount"] = amt
    try:
        res = f.whatif(f.load_customer(), ev)
    except Exception as e:  # never a bare 500 in front of judges
        raise HTTPException(400, f"Bad scenario: {str(e)[:120]}")
    # read-only addition for the UI chart overlay: the after-scenario daily checking series
    res["after_forecast"] = [{"date": d["date"], "checking": d["checking"]}
                             for d in f.forecast(f.load_customer(), 60, events=ev)["days"]]
    engine.emit("Finance engine (rules)", "whatif", output=" · ".join(res.get("facts", [])[:2])[:240], mode="rules")
    return res


@app.post("/api/coach")
def coach(body: CoachIn):
    f = _fin()
    res = f.coach(engine.llm, body.question[:500])
    if res.get("mode") in ("nemotron", "live"):
        res["mode"] = engine.llm.mode
    for t in res.get("tool_trace", []):
        engine.emit("Nemotron coach", "tool", tool=t.get("tool"), input=json.dumps(t.get("args"))[:160],
                    output=str(t.get("result_summary"))[:200], mode=res.get("mode"))
    return res


# ---- Identity Echo (Nemotron claim extraction; delivery, carrier, PNC rails and business endpoints are SIMULATED)
class EchoClaimIn(BaseModel):
    text: str
    sender: str = ""


class EchoStartIn(BaseModel):
    customer: str = "linda"
    consented: bool = False
    target_kind: str | None = "contact"
    number_hash: str | None = ""
    business_id: str | None = ""
    msg_hash: str | None = ""
    claim_kind: str | None = ""
    relation: str | None = None
    money_ask: bool = False
    sender: str | None = ""


class EchoAnswerIn(BaseModel):
    echo_id: str
    answer: str = ""
    who: str = ""


class DecoySayIn(BaseModel):
    echo_id: str
    text: str


class SignalsIn(BaseModel):
    who: str
    sim_swap: bool | None = None
    call_forwarding: bool | None = None
    unknown_call: bool | None = None


class PayIn(BaseModel):
    to_handle: str
    amount: float
    memo: str = ""
    linked_sender: str = ""


class ReleaseIn(BaseModel):
    payment_id: str
    by: str = "customer"


class CardAuthIn(BaseModel):
    token: str
    merchant: str = ""
    payout_account: str = ""


def _d():
    return engine.defense


def _rec(r):
    if r is None:
        raise HTTPException(404, "Unknown Echo.")
    return r


@app.post("/api/echo/claim")
def echo_claim(body: EchoClaimIn):
    return _d().claim(body.text[:1500], body.sender[:40])


@app.post("/api/echo/start")
def echo_start(body: EchoStartIn):
    return _d().start(body.model_dump())


@app.get("/api/echo/inbox")
def echo_inbox(who: str = "jake"):
    return _d().inbox(who[:20])


@app.post("/api/echo/answer")
def echo_answer(body: EchoAnswerIn):
    if body.answer not in ("not_me", "yes"):
        raise HTTPException(400, "answer must be not_me or yes")
    return _rec(_d().answer(body.echo_id[:12], body.answer, body.who[:20]))


@app.post("/api/echo/timeout")
def echo_timeout(body: EchoAnswerIn):
    return _rec(_d().timeout(body.echo_id[:12]))


@app.get("/api/echo/status")
def echo_status(echo_id: str):
    return _rec(_d().status(echo_id[:12]))


@app.get("/api/echo/list")
def echo_list():
    return _d().list()


@app.post("/api/echo/decoy_say")
def echo_decoy_say(body: DecoySayIn):
    return _d().decoy_say(body.echo_id[:12], body.text[:500])


@app.get("/api/carrier/signals")
def carrier_signals():
    return _d().signals()


@app.post("/api/carrier/signals")
def carrier_set(body: SignalsIn):
    if body.who not in ("jake", "linda", "mia", "ruth", "tom"):
        raise HTTPException(404, "unknown line")
    return _d().set_signals(body.who, sim_swap=body.sim_swap, call_forwarding=body.call_forwarding, unknown_call=body.unknown_call)


@app.get("/api/carrier/token")
def carrier_token(who: str = "linda"):
    return _d().risk_token(who[:20])


@app.post("/api/pnc/pay")
def pnc_pay(body: PayIn):
    import math
    if not math.isfinite(body.amount) or not 0 < body.amount <= 1e6:
        raise HTTPException(400, "amount must be between 0 and 1,000,000")
    return _d().pay(body.to_handle, body.amount, body.memo, body.linked_sender)


@app.get("/api/pnc/payments")
def pnc_payments():
    return _d().payments_list()


@app.post("/api/pnc/release")
def pnc_release(body: ReleaseIn):
    r = _d().release(body.payment_id[:16], body.by if body.by in ("customer", "trusted_contact") else "customer")
    if r is None:
        raise HTTPException(404, "Unknown payment.")
    return r


@app.get("/api/pnc/tripwires")
def pnc_tripwires():
    return _d().tripwire_list()


@app.post("/api/pnc/card_auth")
def pnc_card_auth(body: CardAuthIn):
    return _d().card_auth(body.token[:20], body.merchant[:60], body.payout_account[:80])


@app.get("/api/pnc/kanon")
def pnc_kanon(prefix: str):
    """The PNC side sends 5 hex chars of sha256(account) and compares the returned range itself."""
    r = _d().kanon_range(prefix)
    if "error" in r:
        raise HTTPException(400, r["error"])
    return r


@app.get("/api/gauntlet")
def gauntlet(payment_id: str):
    p = _d().payments.get(payment_id[:16])
    if not p:
        raise HTTPException(404, "Unknown payment.")
    return _d().gauntlet(p)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
