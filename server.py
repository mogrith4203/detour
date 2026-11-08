"""Detour demo server.  Start with ./run.sh (or: uvicorn server:app --port 8000), then open http://localhost:8000"""
import json
import os
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
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

try:  # the PNC finance module is optional until it lands
    from detour import finance  # noqa: E402
except Exception:  # pragma: no cover
    finance = None


def admin_only(request: Request):
    """Admin actions only from this laptop (or with the demo token), so nobody on venue Wi-Fi can reset or approve."""
    host = request.client.host if request.client else ""
    if host in ("127.0.0.1", "::1", "localhost", "testclient"):
        return
    if DEMO_TOKEN and request.headers.get("x-demo-token") == DEMO_TOKEN:
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


@app.post("/api/report")
def report(body: StoryIn):
    return engine.report(body.story_id)


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
    try:
        res = engine.benchmark()
    finally:
        engine.quiet = False
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
    try:
        res = f.whatif(f.load_customer(), body.scenario)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(400, f"Bad scenario: {e}")
    # read-only addition for the UI chart overlay: the after-scenario daily checking series
    res["after_forecast"] = [{"date": d["date"], "checking": d["checking"]}
                             for d in f.forecast(f.load_customer(), 60, events=body.scenario)["days"]]
    engine.emit("Finance engine (rules)", "whatif", output=" · ".join(res.get("facts", [])[:2])[:240], mode="rules")
    return res


@app.post("/api/coach")
def coach(body: CoachIn):
    f = _fin()
    res = f.coach(engine.llm, body.question[:500])
    for t in res.get("tool_trace", []):
        engine.emit("Nemotron coach", "tool", tool=t.get("tool"), input=json.dumps(t.get("args"))[:160],
                    output=str(t.get("result_summary"))[:200], mode=res.get("mode"))
    return res


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
