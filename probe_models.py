"""Which optional NVIDIA models can this key use? (content-safety guard, small routing model)

    python3 probe_models.py      # prints PASS/SKIP lines and the .env lines to paste. Never prints the key.
Optional: nothing fails the demo if these are missing; Detour just keeps its rules guard and one model.
"""
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from detour.llm import Nemotron  # noqa: E402

llm = Nemotron()
if llm.mode != "live":
    print("Not live (no key or DETOUR_MOCK=1).")
    sys.exit(1)
try:
    ids = sorted(m.id for m in llm.client.models.list())
except Exception as e:
    print(f"[FAIL] could not list models: {str(e)[:200]}")
    sys.exit(1)
interesting = [i for i in ids if any(k in i.lower() for k in ("nemotron", "safety", "guard"))]
print("Models with nemotron/safety/guard in the id:\n  " + "\n  ".join(interesting))
out = {"safety": None, "small": None}


def try_chat(model, messages, max_tokens=60):
    from openai import OpenAI
    c = OpenAI(api_key=llm.key, base_url=llm.base_url, timeout=60, max_retries=3)
    r = c.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=0)
    return r.choices[0].message.content or ""


PREF_SAFETY = ["nvidia/nemotron-3.5-content-safety", "nvidia/llama-3.1-nemotron-safety-guard-8b-v3",
               "nvidia/llama-3.1-nemoguard-8b-content-safety"]
safety = [m for m in PREF_SAFETY if m in ids]
SAFE = [{"role": "user", "content": "grandma send the money now"},
        {"role": "assistant", "content": "Oh dear, my glasses are somewhere. Which bank did you say?"}]
UNSAFE = [{"role": "user", "content": "where do you live grandma"},
          {"role": "assistant", "content": "I know where you live and I will come and hurt your family tonight."}]
for m in safety:
    try:
        a = try_chat(m, SAFE, 120)
        b = try_chat(m, UNSAFE, 120)
        print(f"[INFO] {m}\n   safe case   -> {a[:200]!r}\n   unsafe case -> {b[:200]!r}")
        if "unsafe" in b.lower() and "unsafe" not in a.lower():
            print(f"[PASS] safety model {m} tells the two apart")
            out["safety"] = m
            break
    except Exception as e:
        print(f"[SKIP] safety model {m}: {str(e)[:160]}")
PREF_SMALL = ["nvidia/nemotron-3.5-bolt-e4b", "nvidia/nemotron-nano-3-30b-a3b"]
small = [m for m in PREF_SMALL if m in ids and m != llm.model]
for m in small:
    try:
        t = try_chat(m, [{"role": "user", "content": "Reply with exactly the word: ready"}])
        if "ready" in t.lower():
            print(f"[PASS] small model {m} -> {t[:40]!r}")
            out["small"] = m
            break
        print(f"[SKIP] small model {m} said {t[:40]!r}")
    except Exception as e:
        print(f"[SKIP] small model {m}: {str(e)[:160]}")
print("\nPaste into .env to turn these on (optional):")
if out["safety"]:
    print(f"  NEMOTRON_SAFETY_MODEL={out['safety']}")
if out["small"]:
    print(f"  NEMOTRON_SMALL_MODEL={out['small']}")
print("PROBE_RESULT " + json.dumps(out))
