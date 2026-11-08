"""Run the Detour benchmark from the command line and save results/benchmark.json.

    python bench.py            # uses NVIDIA_API_KEY / OPENROUTER_API_KEY from .env
    DETOUR_MOCK=1 python bench.py   # offline stand-in (numbers are NOT Nemotron results)
"""
import json
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from detour.engine import Engine  # noqa: E402

if __name__ == "__main__":
    e = Engine()
    print(f"Mode: {e.llm.mode}  Model: {e.llm.describe()['model']}")
    t = time.time()
    res = e.benchmark()
    res["ran_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    out = Path(__file__).parent / "results" / "benchmark.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=2))
    last_set = None
    for r in res["rows"] + res["campaign"]:
        if r.get("set") != last_set:
            last_set = r.get("set")
            print(f"\n{last_set}")
        print(f"  {r['mode'][:52]:<53} caught {r['caught']:>2}/{r['scams']:<3} false alarms {r['false_alarms']}/{r['legit']:<3} "
              f"unsure {r['unsure']:<3} hosted checks {r['hosted_calls']}")
    print(f"\nAPI errors: {e.llm.errors}  ({e.llm.last_error})" if e.llm.errors else "")
    print(f"Done in {time.time() - t:.0f}s. Saved {out}")
