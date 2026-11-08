"""Checks that your NVIDIA key and model id work, in plain English.

    python3 check_nemotron.py

Run this on your own laptop (venue or home Wi-Fi). It tests three things Detour needs:
plain chat, JSON output, and tool calling.
"""
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from detour.llm import Nemotron, parse_json  # noqa: E402

ok = True


def result(name, passed, detail=""):
    global ok
    ok = ok and passed
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f"  -> {detail}" if detail else ""))


llm = Nemotron()
info = llm.describe()
print(f"Mode: {info['mode']}   Model: {info['model']}   Endpoint: {info['base_url']}")
if llm.mode != "live":
    print("\nNot live. Put NVIDIA_API_KEY=... in the .env file (and make sure DETOUR_MOCK=0), then run again.")
    sys.exit(1)

# 1. chat
try:
    t = llm.text([{"role": "user", "content": "Reply with exactly the word: ready"}], max_tokens=20)
    result("Chat", "ready" in t.lower(), repr(t[:60]))
except Exception as e:
    result("Chat", False, str(e)[:300])
    msg = str(e).lower()
    if "404" in msg or "not found" in msg or "model" in msg:
        print("\n  The model id is probably wrong. On build.nvidia.com open the model, click 'View Code',")
        print("  copy the text after model= and put it in .env as NEMOTRON_MODEL=...")
        try:
            ids = sorted(m.id for m in llm.client.models.list() if "nemotron" in m.id.lower())
            if ids:
                print("\n  Nemotron models your key can use:\n    " + "\n    ".join(ids))
        except Exception:
            pass
    elif "401" in msg or "403" in msg or "auth" in msg:
        print("\n  The key was rejected. Make a new key on build.nvidia.com and paste it into .env.")
    else:
        print("\n  Could not reach NVIDIA. Check the Wi-Fi, or use the recorded run: DETOUR_REPLAY=1 ./run.sh")
    sys.exit(1)

# 2. JSON
try:
    d = llm.json([{"role": "system", "content": "Return only a JSON object."},
                  {"role": "user", "content": 'Return {"scam": true, "category": "toll"}'}], max_tokens=80)
    result("JSON output", d.get("category") == "toll", json.dumps(d))
except Exception as e:
    result("JSON output", False, str(e)[:200])

# 3. tool calling
tools = [{"type": "function", "function": {
    "name": "check_allowlist", "description": "Check if a phone number belongs to a verified business.",
    "parameters": {"type": "object", "properties": {"number": {"type": "string"}}, "required": ["number"]}}}]
try:
    m = llm.chat([{"role": "user", "content": "Is (800) 555-0142 a verified business? Use the tool."}], tools=tools, max_tokens=200)
    calls = m.tool_calls or []
    passed = bool(calls) and calls[0].function.name == "check_allowlist"
    result("Tool calling", passed, (calls[0].function.name + " " + calls[0].function.arguments) if calls else f"no tool call; said {m.content!r:.80}")
except Exception as e:
    result("Tool calling", False, str(e)[:200])

print("\nAll good. Start the demo with ./run.sh" if ok else "\nSomething failed. Send this output to your teammate or Claude.")
print(f"Hosted calls used: {llm.calls}")
sys.exit(0 if ok else 1)
