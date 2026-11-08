"""Detour demo server.  Run:  uvicorn server:app --reload  then open http://localhost:8000"""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, StreamingResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from detour.data import PERSONAS, PHONE_SAMPLES, SCENARIOS  # noqa: E402
from detour.engine import Engine  # noqa: E402

ROOT = Path(__file__).parent
app = FastAPI(title="Detour")
engine = Engine()
BENCH_FILE = ROOT / "results" / "benchmark.json"
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class CheckIn(BaseModel):
    text: str
    sender: str = ""
    known: bool = False


class StoryIn(BaseModel):
    story_id: str
    number: str = ""


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/state")
def state():
    return engine.state()


@app.get("/api/samples")
def samples():
    return PHONE_SAMPLES


@app.get("/api/honeypot")
def honeypot(scenario: str, decoy: str):
    if scenario not in SCENARIOS or decoy not in PERSONAS:
        raise HTTPException(404, "unknown scenario or decoy")
    pause = 0.7 if engine.llm.mock else 0.0  # mock replies are instant; pace them so the demo reads well

    def stream():
        for ev in engine.honeypot_session(scenario, decoy):
            yield "data: " + json.dumps(ev) + "\n\n"
            if pause:
                time.sleep(pause)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/check")
def check(body: CheckIn):
    return engine.check_message(body.text, body.sender, body.known)


@app.post("/api/report")
def report(body: StoryIn):
    return engine.report(body.story_id)


@app.post("/api/approve")
def approve(body: StoryIn):
    return engine.approve_block(body.story_id, body.number)


@app.post("/api/seed")
def seed():
    return engine.seed()


@app.post("/api/reset")
def reset():
    engine.reset()
    return engine.state()


@app.post("/api/benchmark")
def benchmark():
    res = engine.benchmark()
    res["ran_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    BENCH_FILE.parent.mkdir(exist_ok=True)
    BENCH_FILE.write_text(json.dumps(res, indent=2))
    return res


@app.get("/api/benchmark/last")
def benchmark_last():
    if BENCH_FILE.exists():
        return json.loads(BENCH_FILE.read_text())
    return {}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
