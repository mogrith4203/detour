"""Thin client for NVIDIA Nemotron through any OpenAI-compatible endpoint.

Works with build.nvidia.com (integrate.api.nvidia.com) or OpenRouter.
If no API key is set (or DETOUR_MOCK=1), every agent falls back to its
deterministic mock so the demo still runs; the UI labels that mode.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path
from types import SimpleNamespace

REPLAY_DIR = Path(__file__).resolve().parent.parent / "replays"


def _env(name, default=None):
    v = os.getenv(name)
    return v if v not in (None, "") else default


class Nemotron:
    def __init__(self):
        nv_key = _env("NVIDIA_API_KEY")
        or_key = _env("OPENROUTER_API_KEY")
        self.key = nv_key or or_key
        if nv_key:
            default_base = "https://integrate.api.nvidia.com/v1"
        else:
            default_base = "https://openrouter.ai/api/v1"
        self.base_url = _env("NEMOTRON_BASE_URL", default_base)
        self.model = _env("NEMOTRON_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
        self.record = _env("DETOUR_RECORD", "0") == "1"
        self.replay = _env("DETOUR_REPLAY", "0") == "1"
        self.mock = (_env("DETOUR_MOCK", "0") == "1" or not self.key) and not self.replay
        self.thinking = _env("NEMOTRON_THINKING", "off")
        # Model routing: the decoy persona uses a small fast model; everything measured by the benchmark stays on self.model.
        # Both ids were verified with this key by probe_models.py. Set either to "off" to disable.
        self.small_model = _env("NEMOTRON_SMALL_MODEL", "nvidia/nemotron-3.5-bolt-e4b")
        self.safety_model = _env("NEMOTRON_SAFETY_MODEL", "nvidia/llama-3.1-nemotron-safety-guard-8b-v3")
        if self.small_model == "off":
            self.small_model = None
        if self.safety_model == "off":
            self.safety_model = None
        self._send_thinking_flag = True
        self.calls = 0
        self.errors = 0
        self.last_error = None
        self.client = None
        if not self.mock and not self.replay:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.key, base_url=self.base_url, timeout=90, max_retries=6)  # backs off on 429s

    @property
    def mode(self):
        return "replay" if self.replay else ("mock" if self.mock else "live")

    def describe(self):
        return {
            "mode": self.mode,
            "model": "recorded run" if self.replay else (self.model if not self.mock else "mock (no API key)"),
            "base_url": self.base_url if not self.mock else None,
            "routing": {"default": self.model, "decoy_persona": self.small_model or self.model, "safety_guard": self.safety_model}
            if not self.mock else None,
            "hosted_calls": self.calls,
            "errors": self.errors,
            "last_error": self.last_error,
        }

    def chat(self, messages, tools=None, temperature=0.3, max_tokens=900, model=None):
        """Returns the assistant message object. Raises on failure."""
        if self.mock:
            raise RuntimeError("mock mode")
        model = model or self.model
        key = hashlib.sha256(json.dumps([model, messages, tools], sort_keys=True, default=str).encode()).hexdigest()[:24]
        if self.replay:  # venue backup: serve a response recorded during an earlier live run
            f = REPLAY_DIR / f"{key}.json"
            if not f.exists():
                raise RuntimeError("no recording for this exact call")
            self.calls += 1
            d = json.loads(f.read_text())
            calls = [SimpleNamespace(id=c["id"], type="function", function=SimpleNamespace(**c["function"])) for c in d.get("tool_calls") or []]
            return SimpleNamespace(content=d.get("content"), tool_calls=calls or None)
        kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if self._send_thinking_flag and self.thinking == "off" and model != self.safety_model:
            kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        self.calls += 1
        try:
            resp = self.client.chat.completions.create(**kwargs)
        except Exception as e:  # retry once without the optional thinking flag
            if "extra_body" in kwargs:
                self._send_thinking_flag = False
                kwargs.pop("extra_body")
                try:
                    resp = self.client.chat.completions.create(**kwargs)
                except Exception as e2:
                    self.errors += 1
                    self.last_error = str(e2)[:300]
                    raise
            else:
                self.errors += 1
                self.last_error = str(e)[:300]
                raise
        msg = resp.choices[0].message
        if self.record:
            REPLAY_DIR.mkdir(exist_ok=True)
            calls = [{"id": c.id, "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in (msg.tool_calls or [])]
            (REPLAY_DIR / f"{key}.json").write_text(json.dumps({"content": msg.content, "tool_calls": calls}))
        return msg

    def safety(self, user_text, reply):
        """Nemotron Safety Guard verdict on a reply before it leaves. Returns (safe: bool|None, categories, mode).
        None means the guard model wasn't available; callers then rely on the rules guard alone."""
        if self.mock or not self.safety_model:
            return None, "", "rules"
        try:
            msg = self.chat([{"role": "user", "content": user_text or "(no message)"}, {"role": "assistant", "content": reply}],
                            temperature=0, max_tokens=80, model=self.safety_model)
            d = parse_json(msg.content or "")
            verdict = str(d.get("Response Safety", "")).lower()
            if verdict not in ("safe", "unsafe"):
                return None, "", "fallback"
            return verdict == "safe", str(d.get("Safety Categories", ""))[:80], self.mode
        except Exception:
            return None, "", "fallback"

    def text(self, messages, **kw):
        msg = self.chat(messages, **kw)
        return strip_think(msg.content or "")

    def json(self, messages, **kw):
        return parse_json(self.text(messages, **kw))


def strip_think(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    return text.strip()


def parse_json(text):
    text = strip_think(text)
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start : end + 1])


class Timer:
    def __enter__(self):
        self.t = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.ms = int((time.perf_counter() - self.t) * 1000)
