# 06 · Pitch, demo click path, Q&A

## 3:00 script (as built). Open on the lens of whichever sponsor is judging, then show the other two briefly

| Time | Who | Say | Screen |
|---|---|---|---|
| 0:00 | Mog | "Most AI security waits for the attack. Detour sends Nemotron out to talk to the attackers first. It learns their playbook, then teaches the phone a few-KB skill that runs right on the device. Every lesson passes 4 regression checks before it ships." | NVIDIA lens, empty agent graph |
| 0:20 | Mog | "Attackers swap phone numbers in hours, but they keep the same story. So we match the story, not the number." | Decoy console |
| 0:35 | Judge | "You be the scammer. Type anything." Decoy Linda replies in character. End the session: the extractor pulls the story, and the validator runs rules the model can't overrule. It lands as WATCH (amber) on purpose. Say: "One person typing can't put a play on every phone. Rules, not the model, decide that, and it takes two independent decoy lines." Point to the scripted plays already red in the story map. | Live decoy, graph lighting up |
| 1:15 | Ayush | Bank sample (new number, old play): warned on the phone, privacy meter unchanged. Then the grandparent sample: unsure → consent sheet shows the exact redacted text and bytes → "Send redacted copy" → rescue tool calls → forged skill → 4 checks pass → deliver it again: caught on-device, and the hosted-call counter doesn't move. | T-Mobile lens, then NVIDIA lens |
| 2:10 | Ayush | Click "See what this would do to Linda's finances →". "That bail would overdraw Linda's checking on 50 of the next 60 days." Ask the coach the bail question: the tool chips show, and every number is checked. | PNC lens |
| 2:35 | Mog | Scoreboard (LIVE numbers only): blocklist vs on-device vs on-device + Nemotron on held-out sets, including Ayush's blind set; hosted calls with and without teaching. | NVIDIA lens scoreboard |
| 2:50 | Mog | "Nemotron is the teacher, not the bottleneck. It checks a new attack once, and every phone handles it after that." | Graph, full loop |

Variant for the **general jury**: run the T-Mobile flow, then spend 20 seconds on keys 2 and 3: "Same engine, seen by NVIDIA and PNC."

## Pre-demo checklist (each judging slot)

1. Server running in LIVE mode (green badge), or REPLAY (amber) if Wi-Fi is bad. Never MOCK in front of judges unless you say so.
2. Click Reset, then Load decoy history, so the story map has red plays.
3. The phone is clear, and the privacy meter is at 0.
4. The scoreboard shows the last LIVE benchmark (with a timestamp), not mock.
5. Keys 1/2/3 work. Nothing is focused in an input.
6. Browser zoom fits the projector. The UI targets 1440×900 and works at 1280×800.

## Words: use these / avoid these

| Use | Avoid |
|---|---|
| few-KB on-device skill (weighted keywords + rule checks) | "a model on the phone", "on-device AI model" |
| 4 regression checks | unit tests, "fully tested" |
| plays from a scam taxonomy, scripted plus you live | "Nemotron talks to real scammers" |
| simulated decoy lines / sender registration | implying real carrier integration |
| recorded run (in REPLAY) | calling a replay live |
| "rules the model can't overrule" | "injection-proof", "unhackable" |

## Q&A bank (answer in one sentence first; add more only if they lean in)

| Q | A |
|---|---|
| Isn't this just another scam-text detector? | The detector is the smallest part. The product is the loop: adversary-in-the-loop agents that turn attacker conversations into tested on-device skills. |
| Where exactly is Nemotron? | Five agents: decoy persona, intel extractor, rescue investigator with tools, skill forge, and the money coach. Rules do the enforcement on purpose. |
| Why is this agentic and not a pipeline? | The rescue agent chooses its own tool calls in a ReAct loop, and forge + gate lets the system improve itself under verification. |
| Why Nemotron? | We need role-play, strict JSON extraction and tool calling in one loop behind one OpenAI-compatible endpoint, and Nemotron does all three. |
| What runs on the phone? Does my text leave? | A few-KB skill runs in the browser, standing in for the phone. Only the verdict leaves. The text leaves only if the phone is unsure and you tap consent, and then redacted. The network tab proves it. |
| What stops poisoning? | The allowlist, the injection scan, corroboration from 2 independent decoy lines (typed sessions and reports can't do it alone), and the gate's 4 checks. Skills are versioned and promotions rate-limited. |
| How do you know the score isn't overfit? | Thresholds are frozen; test rows are held out; Ayush wrote his set blind. The blocklist row is low by construction because the tests use new numbers. |
| What if Nemotron is wrong? | A verdict with no tool evidence becomes unsure, "legit" never overrides a payment ask, and a bad skill fails the gate. |
| What does it cost? | We measured hosted calls: the teaching loop cut them from [N] to [M] in the campaign replay. Use LIVE numbers only. |
| Won't scammers detect decoys? | Some will, but they still have to tell the same story to real people, and customer reports feed the same map. |
| Isn't running decoys legal-risky? | That needs counsel. Our design is reply-only, on carrier-owned dormant numbers, with synthetic personas, and no data is sold. |
| Apate.ai / O2 Daisy already do this? | They waste scammers' time. We turn the conversation into a shared, tested skill that protects every phone. |
| iMessage / WhatsApp? | Matching happens on the phone, so encryption doesn't stop it. Screenshot checks are the next step. |
| PNC: where's the data from? | A synthetic customer. In production it would come through open banking, with consent. |
| PNC: why is scam exposure a health indicator? | Money that can leave in the next hour is risk. Singapore banks already let customers lock savings against digital transfers. |
| PNC: isn't the coach a chatbot? | It calls the forecast and what-if tools, and every dollar figure is checked against their results, sign included. Safety warnings come from code. |
| Did you use AI to build this? | Yes. We directed Claude to write code fast, and made the product, design, safety and pitch decisions ourselves. [Say this honestly if asked.] |
| What's real vs simulated? | Real: agents, Nemotron calls, tools, rules, matcher, gate, finance math, benchmark. Simulated: scammer traffic, decoy lines, sender registration, the customers. |
