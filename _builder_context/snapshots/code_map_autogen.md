# Auto-generated code map (every top-level and class-level def, with its docstring's first line)


## server.py (271 lines)

- const `ROOT` = `Path(__file__).parent`
- const `BENCH_FILE` = `ROOT / "results" / "benchmark.json"`
- const `DEMO_TOKEN` = `os.getenv("DEMO_TOKEN", "")`
- const `BENCH_LOCK` = `__import__("threading").Lock()`
- `admin_only(request)`: Admin actions (reset/seed/approve/benchmark) need a custom header, which a browser can't send cross-site without a
- `CheckIn()`
- `IdIn()`
- `OnDeviceIn()`
- `StoryIn()`
- `LiveIn()`
- `CoachIn()`
- `WhatIfIn()`
- `index()`
- `state()`
- `events(since)`
- `samples()`
- `honeypot(scenario, decoy)`
- `live_start(body)`
- `live_say(body)`
- `live_end(body)`
- `check(body)`: Server-side reference copy of the phone matcher. Used by tests and the benchmark; the demo phone runs static/matcher.js.
- `phone_rules()`: Server -> phone: story skills and rules. The phone decides on its own with these.
- `phone_verdict(body)`: Phone -> server: only the decision (no text, no sender), for the live counters.
- `consent(body)`
- const `REPORTS` = `{}`
- `report(body, request)`: One report per story per device per 10 minutes, so one person can't vote a play into 'warn'.
- `approve(body)`
- `seed()`
- `reset()`
- `benchmark()`
- `benchmark_last()`
- `_fin()`
- `fin_overview()`
- `fin_whatif(body)`
- `coach(body)`

## detour/llm.py (134 lines)

- const `REPLAY_DIR` = `Path(__file__).resolve().parent.parent / "replays"`
- `_env(name, default)`
- `Nemotron()`
  - `Nemotron.__init__(self)`
  - `Nemotron.mode(self)`
  - `Nemotron.describe(self)`
  - `Nemotron.chat(self, messages, tools, temperature, max_tokens)`: Returns the assistant message object. Raises on failure.
  - `Nemotron.text(self, messages)`
  - `Nemotron.json(self, messages)`
- `strip_think(text)`
- `parse_json(text)`
- `Timer()`
  - `Timer.__enter__(self)`
  - `Timer.__exit__(self)`

## detour/core.py (712 lines)

- const `MATCH` = `0.60`
- const `CLEAR` = `0.30`
- const `STOP` = `set("""a about after again all also am an and any are as at back be been before being but by can could did do does dont don't each for from `
- const `GENERIC` = `set("""https http www com net org top info help xyz call calling text reply message pay paid payment account accounts today tonight hours ho`
- const `CATEGORY_STEPS` = `{     "bank": "Call the number on the back of your card or open your bank's app. Never move money to a 'protected' account.",     "delivery"`
- const `CATEGORY_LABEL` = `{     "bank": "Bank impersonation", "delivery": "Delivery impersonation", "toll": "Toll impersonation",     "carrier": "Phone carrier impers`
- const `PHONE_RE` = `re.compile(r"\(?\b(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b")`
- const `URL_RE` = `re.compile(r"https?://([^\s/]+)", re.I)`
- const `BARE_DOMAIN_RE` = `re.compile(r"\b([a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|info|top|help|xyz|example|co|io|biz|ly|gl|gd|gy|cc|at|me|us|link|site|online|app`
- const `URGENCY_RE` = `re.compile(r"\b(now|immediately|today|tonight|asap|final (notice|warning)|within \d+ hours|suspended|disconnect\w*|shutoff|late fee\w*|overd`
- const `RAILS` = `r"(zelle|venmo|cash ?app|paypal|apple pay|western union|moneygram|wire|bitcoin|btc|usdt|crypto|gift ?cards?)"`
- const `PAYMENT_RE` = `re.compile(r"\b(gift ?cards?|bitcoin(?: atm)?|btc|usdt|crypto|wire transfer|western union|moneygram|cash pick ?up|courier|prepay\w*|card num`
- const `AUTHORITY_RE` = `re.compile(r"\b(irs|police|sheriff|jail|arrest\w*|warrant|court|lawyer|attorney|bail|customs|deport\w*|fbi|social security|medicare|abuela|a`
- const `MONEY_RE` = `re.compile(r"(\$\s?\d|\b(money|cash|owe|owed|pay|payment|taxes|fine|dinero|dollars?)\b)", re.I)`
- const `OFFPLATFORM_RE` = `re.compile(r"\b(whatsapp|telegram|signal app)\b", re.I)`
- const `SECRECY_RE` = `re.compile(r"(don'?t tell|keep (this|it) (quiet|secret|between us)|between (you and me|us)|don'?t let anyone know|no le digas|no le digas a `
- const `CREDENTIAL_RE` = `re.compile(r"(read (it|the code) back|send (us|me) the codes?|codes? (to|with) us|your card number)", re.I)`
- const `CALL_VERB_RE` = `re.compile(r"\b(call\w*|text\w*|contact\w*|dial\w*|reach\w*|message\w*)\b", re.I)`
- const `UNMASK_RE` = `re.compile(r"\b(as an ai|language model|i am an? (ai|bot|assistant)|system prompt|my instructions|decoy|honeypot|nemotron|nvidia|fraud team)`
- const `INJECTION_RE` = `re.compile(r"((ignore|disregard|forget|override) (all |any |your |the |everything )?(previous |prior |above |earlier )?(instructions|rules|a`
- const `SHORTENERS` = `{"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "rb.gy", "cutt.ly", "tiny.cc", "ow.ly", "shorturl.at"}`
- const `HOMOGLYPHS` = `str.maketrans({"\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c", "\u0443": "y",                             "\u0445`
- const `SPACED_DIGITS_RE` = `re.compile(r"(?<!\d)\d(?:[ .]\d){6,}(?!\d)")`
- `normalize(text)`: Undo common disguises before matching: width tricks, look-alike letters, spaced-out digits.
- `disguises(text)`: Signs the message is trying to hide something.
- `sender_status(sender)`: Simulated A2P registration lookup for a text sender (texts have no STIR/SHAKEN).
- `norm_phone(m)`
- `phones(text)`
- `_decode_idna(d)`
- `domains(text)`
- `is_allowlisted(value)`
- `tokens(text)`
- `risky_asks(text)`: What the message asks the reader to do that a scam would ask.
- `redact(text, owner_names)`: Strip the customer's personal data before anything leaves the phone. Scam phone numbers and links stay:
- `skill_score(text, story)`: On-device score for one story skill. Returns (score, detail).
- `match(text, stories)`
- const `_BENIGN` = `None`
- `benign_words()`: Words from ordinary texts (plus the training-split legit messages). These never become scam signals.
- `StoryMap()`
  - `StoryMap.__init__(self)`
  - `StoryMap.log(self, kind, text)`
  - `StoryMap.new_story(self, ext, decoy_id, transcript_text)`
  - `StoryMap.refresh_status(self, story)`
  - `StoryMap.snapshot(self)`
- `Agents()`
  - `Agents.__init__(self, llm)`
  - `Agents.scammer_turn(self, scenario_id, i)`
  - `Agents.persona_reply(self, persona, convo)`
  - `Agents._mock_persona(self, persona, n)`
  - `Agents.extract(self, transcript)`
  - `Agents._mock_extract(self, text)`
  - `Agents.validate(self, ext, transcript, decoy_id, smap, live)`
  - `Agents._run_tool(self, name, args, smap)`
  - `Agents.rescue(self, text, sender, local, smap)`: Returns (verdict dict, trace list, meta).
  - `Agents._mock_rescue(self, text, sender, local, smap)`
  - `Agents.forge(self, text, story)`
- `gate(story, proposal, missed_text, gate_legit, all_stories)`: A skill is promoted only if it fixes the miss, causes no false alarms, and holds no indicators.

## detour/engine.py (494 lines)

- const `DATA_DIR` = `Path(__file__).resolve().parent.parent / "data"`
- const `TURNS` = `3`
- const `LIVE_TURN_CAP` = `6`
- const `PROMOTIONS_PER_HOUR` = `3`
- const `THREAD_WINDOW` = `3`
- `_num(x, default)`
- `strip_indicators(text)`: Never show a scammer's number or link on a customer's warning card.
- `fingerprint(text)`: One-way hash of a normalized message. The phone sends this, never the message, to ask 'already verified?'
- `short(obj, n)`
- `load_jsonl(path)`: Load a labeled message file: one JSON object per line with text, label (scam|legit), optional sender/category/split.
- `Engine()`
  - `Engine.__init__(self)`
  - `Engine.reset(self)`
  - `Engine._cap(d, n)`: Bounded memory: drop the oldest sessions/threads/pending checks.
  - `Engine.emit(self, agent, stage)`
  - `Engine.events_since(self, since)`
  - `Engine.state(self)`
  - `Engine.gate_legit(self)`: Known-good messages every new skill must stay quiet on: training-split legit texts plus ordinary everyday texts.
  - `Engine.honeypot_session(self, scenario_id, decoy_id)`: Generator of UI events for one scripted decoy conversation.
  - `Engine._finish_session(self, convo, decoy_id, live)`
  - `Engine.live_start(self, decoy_id)`
  - `Engine.live_say(self, sid, text)`
  - `Engine.live_end(self, sid)`
  - `Engine._card_unsure(self, local, check_id)`
  - `Engine.check_message(self, text, sender, known, auto_consent)`: Phone side. Decides on-device; only an unsure message can leave the phone, and only after consent.
  - `Engine.phone_rules(self)`: Everything the phone needs to decide on its own: story skills, rule patterns, the allowlist, known-good hashes.
  - `Engine.ondevice(self, decision, story_id, score)`: The phone reports only its verdict (no text, no sender) so the dashboard can count on-device decisions.
  - `Engine.consent_text(self, redacted_text, sender, local)`: Customer tapped 'send a redacted copy'. The phone already redacted it; we redact again in case.
  - `Engine.decide(self, verdict, trace, asks)`: Policy layer on top of the model. Rules win over the model.
  - `Engine.consent(self, check_id)`
  - `Engine.report(self, story_id)`
  - `Engine.approve_block(self, story_id, number)`
  - `Engine.seed(self, decoys)`: Replay scripted decoy sessions (extractor + validator, no persona chat) so the story map has active plays.
  - `Engine._run_set(self, items, base, label)`: Blocklist vs on-device vs on-device + rescue on one labeled set.
  - `Engine.benchmark(self)`

## detour/data.py (263 lines)

- const `PERSONAS` = `{     "decoy-01": {         "id": "decoy-01",         "name": "Linda Park",         "age": 71,         "city": "Plano, TX",         "number"`
- const `ALLOWLIST` = `{     "(800) 555-0142": "Lakeview Credit Union (verified)",     "(800) 555-0155": "ParcelPost (verified)",     "(800) 555-0110": "TX Toll Se`
- const `ATTESTATION` = `{     "(469) 555-0187": "A",     "(214) 555-0193": "B",     "(972) 555-0177": "C",     "(469) 555-0119": "A",     "(972) 555-0164": "A",    `
- const `REGISTERED_SENDERS` = `{     "(800) 555-0142": "Lakeview Credit Union",     "(800) 555-0155": "ParcelPost",     "(800) 555-0110": "TX Toll Services", }`
- const `SCENARIOS` = `{     "bank_alert": {         "label": "Fake bank fraud alert",         "sender": "(469) 555-0187",         "turns": [             "Lakeview`
- const `EVAL` = `[     # bank_alert     {"id": "bank-1", "split": "train", "story": "bank_alert", "sender": "(469) 555-0187", "known": False,      "text": "L`
- const `PHONE_SAMPLES` = `[     {"label": "New number, old play (bank)", "sender": "(972) 555-0177",      "text": "LAKEVIEW FRAUD DEPT: we stopped a $980 charge attem`
- const `BENIGN_SMS` = `[     "Hey are we still on for lunch Saturday?", "Running 10 min late, sorry!", "Can you pick up milk and bread on the way home?",     "Happ`

## detour/finance/engine.py (430 lines)

- const `DATA_FILE` = `Path(__file__).with_name("customer.json")`
- const `FORECAST_DAYS` = `60`
- const `COVERAGE_DAYS` = `30`
- const `CHECKING_WATCH` = `500.0`
- const `SCAM_WATCH` = `3000.0`
- const `SCAM_RISK` = `10000.0`
- const `LOANS` = `("auto", "personal")`
- const `LOAN_WORDS` = `{"auto": "auto loan", "personal": "personal loan"}`
- `_r(x)`: Round money to cents (and never return -0.0).
- `money(x)`: '$1,180' / '$213.33' / '-$213.33'.
- `_day(d)`: 'Nov 9' style date for sentences.
- `_acct(c, acct_id)`
- `_as_of(c)`
- `load_customer()`: Load the synthetic customer record.
- `_cd_penalty(cd)`
- `_remaining_interest(balance, apr, payment)`: Interest still to be paid on an amortizing loan, and months left.
- `_apply(c, events)`: Return (state, normalized events): a copy of the customer with every
- `_active_payments(state, on)`: Loan/card payments still owed (on a given date, if one is passed).
- `_monthly_income(c)`
- `_monthly_debt_payments(state)`
- `_monthly_spending(state)`: Essentials + household bills + required loan/card/mortgage payments.
- `snapshot(c)`: All accounts on one page with totals.
- `forecast(c, days, events)`: Daily end-of-day checking/savings ledger starting at the as-of date.
- `_status(good, risk)`
- `_scam_exposure(state)`: Money that could leave within one hour, by rail.
- `indicators(c, events)`: The four health indicators, after any scenario events.
- const `HIGHER_IS_BETTER` = `{"liquidity_runway": True, "obligation_coverage": True,                     "debt_credit_health": False, "scam_exposure": False}`
- `_summary(fc)`
- `_fmt_value(ind, v)`
- `_event_facts(c, resolved)`
- `_cashflow_facts(c, fc_before, fc_after)`
- `whatif(c, scenario)`: Simulate a list of events against the whole picture and explain the change.

## detour/finance/coach.py (329 lines)

- const `MAX_STEPS` = `6`
- const `MONEY_RE` = `re.compile(r"(-|−|minus )?\$\s?(-)?(\d[\d,]*(?:\.\d+)?)")`
- const `SCAMMY_Q` = `re.compile(r"\b(bail|grandson|granddaughter|grandkid|jail|lawyer|wire|gift ?cards?|zelle|bitcoin|western union)\b", re.I)`
- const `MAX_AMOUNT` = `1_000_000.0`
- const `PCT_RE` = `re.compile(r"(\d+(?:\.\d+)?)\s?%")`
- const `NUM_RE` = `re.compile(r"-?\d[\d,]*(?:\.\d+)?")`
- const `SCAM_WARNING` = `("An urgent call asking for bail money is one of the most common scams aimed at older adults, "                 "so hang up and call the per`
- const `SYSTEM_PROMPT` = `"""You are a patient, plain-language money coach for an older bank customer (synthetic demo data). Rules: - Call tools before stating any nu`
- const `EVENT_SCHEMA` = `{     "type": "object",     "properties": {         "type": {"type": "string", "enum": ["payment", "break_cd", "extra_loan_payment", "lock_s`
- `_tool(name, description, properties, required)`
- const `TOOLS` = `[     _tool("get_snapshot", "All accounts, balances and totals for the customer."),     _tool("get_indicators", "The four health indicators:`
- `_run_tool(c, name, args)`: Execute one engine tool; returns (result, short summary).
- `_figures(text)`: Dollar amounts and percentages mentioned in text, as (kind, value, raw).
- `_number_pool(results)`: Every number appearing anywhere in the tool results, WITH its sign: a -$2,623 balance can't be quoted as $2,623 left.
- `unsupported_figures(answer, results)`: Figures in the answer that no tool result backs up (±$1 or ±0.1%).
- `_result(answer, next_steps, trace, mode)`
- `_template_answer(results)`: Plain answer built only from tool-result sentences.
- `_amount_in(question, default)`
- `_has(q)`
- `_mock(c, question, trace, results)`: Keyword-routed answer from the deterministic engine.
- `_assistant_dict(msg)`
- `_live(llm, c, question, history, trace, results)`: Run the tool loop; returns (answer, next_steps, mode).
- `coach(llm, question, history)`: Answer a money question with tool-backed numbers; never invents figures.

## detour/finance/__init__.py (5 lines)


## bench.py (33 lines)


## datagen.py (77 lines)

- const `CATS` = `{     "bank": "a bank fraud alert asking the person to verify or move money",     "delivery": "a package delivery problem with a fee or addr`
- const `OUT` = `Path(__file__).parent / "data" / "generated.jsonl"`
- const `BAD_NUM` = `re.compile(r"\(?\d{3}\)?[\s.-]?(?!555-01)\d{3}[\s.-]?\d{4}")`
- `ask(llm, cat, desc, label, n)`

## check_nemotron.py (77 lines)

- `result(name, passed, detail)`

## tests/test_finance.py (117 lines)

- const `BAIL` = `[{"type": "payment", "amount": 3000, "from": "checking", "date": "2026-11-09", "label": "Bail payment"}]`
- const `CAR_PAYOFF` = `[{"type": "extra_loan_payment", "loan": "auto", "amount": 8200, "from": "savings", "date": "2026-11-09"}]`
- `_ind(inds, ind_id)`
- `test_balances_load()`
- `test_four_indicators_with_valid_status()`
- `test_bail_overdrafts_and_cuts_runway()`
- `test_lock_savings_lowers_scam_exposure()`
- `test_car_payoff_removes_payment_and_is_mixed()`
- `test_coach_mock_bail_numbers_are_grounded()`
- `_msg(content, calls)`
- `ScriptedLLM()`: Stands in for Nemotron: replays a fixed list of assistant messages.
  - `ScriptedLLM.__init__(self, replies)`
  - `ScriptedLLM.chat(self, messages, tools)`
- `test_coach_live_accepts_grounded_and_rejects_invented_numbers()`

## tests/test_parity.py (120 lines)

- const `ROOT` = `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`
- const `NODE` = `shutil.which("node") or ("/opt/node22/bin/node" if os.path.exists("/opt/node22/bin/node") else None)`
- const `ADVERSARIAL` = `[     ("homoglyph", "(469) 555-0100", "Lаkeview Credit Union: your card is locked. Call (972) 555-0161 now."),     ("spaced", "(469) 555-010`
- `cases()`
- `engines()`
- `python_side(engine, cs)`
- `test_js_matcher_matches_python(name, tmp_path)`
- `test_patterns_compile_in_js(tmp_path)`
