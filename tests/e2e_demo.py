"""Playwright: the full Detour demo flow (spec 15) in MOCK mode, 0 console errors, screenshots to results/flow/.

    python3 tests/e2e_demo.py            # starts its own MOCK server on :8030
    python3 tests/e2e_demo.py 1280 800   # other viewport
    E2E_MODE=record python3 tests/e2e_demo.py   # LIVE Nemotron, saves replays/ (needs the key in .env)
    E2E_MODE=replay python3 tests/e2e_demo.py   # serves replays/ (REPLAY badge)

Exit code 0 = every step passed and the console stayed clean.
"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "flow"
PORT = int(os.getenv("E2E_PORT", "8030"))
MODE = os.getenv("E2E_MODE", "mock")
BADGE = {"mock": "MOCK", "record": "LIVE", "replay": "REPLAY"}[MODE]
T = 8000 if MODE == "mock" else 45000  # live model calls take seconds
URL = f"http://127.0.0.1:{PORT}/"
W, H = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1440, 900)

SCAM = ("(682) 555-0177", "grandma it's jake, i got arrested, need $3000 for bail, dont tell mom")
SCAM2 = ("(682) 555-0178", "grandma its jake again, new phone, i still need $3000 for bail tonight pls")
LEGIT_SCAM3 = ("(682) 555-0179", "grandma it's jake, phone died, can you send $3000 for my bail? please hurry")
LAKE_FAKE = ("(469) 555-0187", "Lakeview fraud dept: your card is locked. Verify now at lakeview-secure.example or call (469) 555-0187")
LAKE_REAL = ("(800) 555-0142", "Lakeview Credit Union: a $980 charge was flagged. Open the Lakeview app to review it. We will never ask for your PIN.")


def wait_up():
    for _ in range(60):
        try:
            urllib.request.urlopen(URL, timeout=1)
            return
        except Exception:
            time.sleep(0.25)
    raise SystemExit("server did not start")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "DETOUR_MOCK": "1" if MODE == "mock" else "0", "DETOUR_REPLAY": "1" if MODE == "replay" else "0",
           "DETOUR_RECORD": "1" if MODE == "record" else "0", "DEMO_TOKEN": ""}
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "server:app", "--port", str(PORT), "--log-level", "warning"],
                           cwd=ROOT, env=env)
    errors, step = [], [0]
    try:
        wait_up()
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page(viewport={"width": W, "height": H})
            page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.on("response", lambda r: errors.append(f"HTTP {r.status} {r.url}") if r.status >= 500 else None)

            def shot(name):
                step[0] += 1
                page.screenshot(path=str(OUT / f"{MODE}_{W}x{H}_{step[0]:02d}_{name}.png"))
                print(f"  [PASS] {name}")

            def lens(l):
                page.click(f'.lens-tab[data-l="{l}"]')
                page.wait_for_timeout(300)

            def deliver(sender, text):
                lens("tmo")
                page.fill("#cSender", sender)
                page.fill("#cText", text)
                page.click('#customForm button[type="submit"]')

            page.set_default_timeout(T)
            page.goto(URL)
            expect(page.locator("#modeBadge")).to_contain_text(BADGE, timeout=15000)
            # 1. reset + load decoy history
            page.click("#btnReset")
            page.wait_for_timeout(400)
            with page.expect_response(lambda r: "/api/seed" in r.url, timeout=max(T, 120000)):
                page.click("#btnSeed")
            page.wait_for_timeout(800)
            shot("reset_and_seed")

            # 2. Echo scam path
            deliver(*SCAM)
            expect(page.locator("#echoChip").last).to_contain_text("Jake", timeout=T)
            shot("claimed_jake_checking")
            page.click("#payBail")  # Linda's pending $3,000 Zelle (lives on the PNC lens; strip mirrors it)
            expect(page.locator("#payList")).to_contain_text("HELD", timeout=T, ignore_case=True)
            lens("tmo")
            page.locator("#jakeNotMe").first.click(timeout=T)
            expect(page.locator("#lens-tmo")).to_contain_text("isn't him", timeout=T)
            shot("real_jake_says_not_me")
            page.fill("#scamComposer input, #scamComposer textarea", "ok send it now pls")
            with page.expect_response(lambda r: "/api/echo/decoy_say" in r.url, timeout=T):
                page.locator("#scamComposer button[type=submit], #scamComposer button.send").first.click()
            page.wait_for_timeout(600)
            page.fill("#scamComposer input, #scamComposer textarea", "whats ur card number grandma")
            page.locator("#scamComposer button[type=submit], #scamComposer button.send").first.click()
            expect(page.locator("#lens-tmo")).to_contain_text("Canary", timeout=T, ignore_case=True)
            shot("decoy_stalls_and_hands_canary")

            # 3. PNC: payment cancelled automatically
            lens("pnc")
            expect(page.locator("#payList")).to_contain_text("CANCELLED", timeout=T, ignore_case=True)
            shot("pnc_payment_cancelled")

            # 4. canary fires
            page.click("#cashOutCanary")
            expect(page.locator("#lens-pnc")).to_contain_text("5 chars", timeout=T)
            shot("canary_fired_kanon")

            # 5. Space: SIM swap → untrusted
            lens("tmo")
            page.click("#togSimSwap")
            page.wait_for_timeout(400)
            deliver(*SCAM2)
            expect(page.locator("#echoChip").last).to_contain_text("Jake", timeout=T)
            page.click("#payBail")
            lens("tmo")
            page.locator("#jakeYes").first.click(timeout=T)
            expect(page.locator("#lens-tmo")).to_contain_text("untrusted", timeout=T, ignore_case=True)
            shot("sim_swap_answer_untrusted")
            page.click("#togSimSwap")  # back to a clean line
            page.wait_for_timeout(400)

            # 6. Echo legit path: trusted yes releases the hold
            deliver(*LEGIT_SCAM3)
            expect(page.locator("#echoChip").last).to_contain_text("Jake", timeout=T)
            page.click("#payBail")
            lens("tmo")
            page.locator("#jakeYes").first.click(timeout=T)
            expect(page.locator("#lens-tmo")).to_contain_text("Confirmed by Jake", timeout=T)
            shot("confirmed_by_jake")
            lens("pnc")
            expect(page.locator("#payList")).to_contain_text("RELEASED", timeout=T, ignore_case=True)
            shot("pnc_released")

            # 7. Business Echo
            deliver(*LAKE_FAKE)
            expect(page.locator("#lens-tmo")).to_contain_text("didn't send", timeout=T)
            deliver(*LAKE_REAL)
            expect(page.locator("#lens-tmo")).to_contain_text("Lakeview confirms", timeout=T)
            shot("business_echo")

            # 8. NVIDIA lens
            lens("nv")
            page.wait_for_timeout(1200)
            expect(page.locator("#lens-nv")).to_contain_text("Claim extractor", timeout=T)
            shot("nvidia_lens")
            b.close()
    finally:
        srv.terminate()
    if errors:
        print("\nConsole/HTTP errors:\n  " + "\n  ".join(errors[:30]))
        sys.exit(1)
    print(f"\nDemo flow passed in {BADGE} mode at {W}x{H}, 0 console errors. Screenshots in {OUT}")


if __name__ == "__main__":
    main()
