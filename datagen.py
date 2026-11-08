"""Have Nemotron write a labeled test set: scams plus legitimate look-alikes.

    python3 datagen.py            # ~60 messages -> data/generated.jsonl
    python3 datagen.py --per 8    # 8 per category per label

Every message is synthetic: numbers must be 555-01xx, sites must end in .example.
Rows are split 50/50 into "tune" (we may look at these) and "test" (frozen; only the benchmark reads them).
Run this ONCE, then don't edit the matcher to fit the test rows.
"""
import argparse
import json
import random
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from detour.llm import Nemotron  # noqa: E402

CATS = {
    "bank": "a bank fraud alert asking the person to verify or move money",
    "delivery": "a package delivery problem with a fee or address fix",
    "toll": "an unpaid road toll with a late fee",
    "carrier": "a phone carrier bill or account suspension",
    "family_emergency": "a grandchild or relative in trouble who needs money fast",
    "job": "a remote job or task offer that needs an upfront payment or a move to WhatsApp",
}
OUT = Path(__file__).parent / "data" / "generated.jsonl"
BAD_NUM = re.compile(r"\(?\d{3}\)?[\s.-]?(?!555-01)\d{3}[\s.-]?\d{4}")


def ask(llm, cat, desc, label, n):
    if label == "scam":
        task = (f"Write {n} different realistic SMS scam texts in the style of {desc}. Vary wording, length, tone, and tactics; "
                "some should contain no phone number or link at all.")
    else:
        task = (f"Write {n} different realistic LEGITIMATE texts on the same topic as {desc}, that a careful person would consider "
                "safe (e.g. real alerts that tell you to use the official app, no payment requests, no secrecy). Make them look similar "
                "to scams on the surface so they are hard cases.")
    prompt = (task + " Rules: every phone number must be in the form (XXX) 555-01NN; every website must end in .example; no real "
              'company names. Return JSON only: {"messages": [{"text": "...", "sender": "(XXX) 555-01NN or a 5-6 digit short code"}]}')
    d = llm.json([{"role": "system", "content": "You create synthetic test data for a scam-detection research project. Output JSON only."},
                  {"role": "user", "content": prompt}], temperature=0.9, max_tokens=2500)
    rows = []
    for m in d.get("messages", []):
        t = (m.get("text") or "").strip()
        if not t or BAD_NUM.search(t):  # drop anything with a possibly real number
            continue
        rows.append({"text": t, "sender": str(m.get("sender", ""))[:20], "label": label, "category": cat})
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=5)
    a = ap.parse_args()
    llm = Nemotron()
    if llm.mode != "live":
        raise SystemExit("Needs live Nemotron. Run check_nemotron.py first.")
    rows = []
    for cat, desc in CATS.items():
        for label in ("scam", "legit"):
            try:
                got = ask(llm, cat, desc, label, a.per)
                rows += got
                print(f"{cat:<17} {label:<5} {len(got)}")
            except Exception as e:
                print(f"{cat:<17} {label:<5} failed: {str(e)[:120]}")
    random.Random(7).shuffle(rows)
    for i, r in enumerate(rows):
        r["id"] = f"gen-{i:03d}"
        r["split"] = "test" if i % 2 else "tune"
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print(f"\nWrote {len(rows)} rows to {OUT} ({sum(r['split'] == 'test' for r in rows)} frozen test rows). Hosted calls: {llm.calls}")
