# Detour: demo video script (target 1:55, hard cap 2:00)

Record at 1440×900. Start the app first (see "Before you record"). Read the lines in your own words; they're a guide, not a script to recite. No AI voice.

**Who reads what:** Mog = **M**, Ayush = **A** (Ayush also taps Jake's phone).

| Time | Click | Say |
|---|---|---|
| 0:00–0:12 | Show the T-Mobile lens. Point at the mode badge (top right). | **M:** "Every scam pretends to be someone. Detour asks that someone. This is Linda's phone, and this is her grandson Jake's phone." |
| 0:12–0:22 | Click **Reset**, then **Load decoy history**. | **M:** "Our decoys have already talked to scammers, so Linda's phone knows the common plays." |
| 0:22–0:40 | Deliver the sample **"grandma it's jake, i got arrested…"** from (682) 555-0177. Point at the chip "Claimed: Jake (grandson) → checking with the real Jake…". | **M:** "Nemotron reads who the message claims to be. Linda's phone matches that to her own contacts. Her contacts never leave the phone. T-Mobile then asks the real Jake, on his own line, whether this is him. No message content goes out." |
| 0:40–0:50 | Click **Linda sends $3,000 Zelle for Jake's bail**. Show **HELD** with the countdown. | **A:** "Linda's already trying to pay. PNC holds it, because two separate signals fired." |
| 0:50–1:02 | On Jake's phone, Ayush taps **Not me**. Linda's card turns red: "The real Jake says this isn't him." Show the payment flip to **CANCELLED**. | **A:** "Jake says it isn't him. That's a ground-truth scam label, not a guess. The payment is cancelled, and Linda keeps her $3,000." |
| 1:02–1:18 | In the scammer composer, send "ok send it now pls", then "whats ur card number grandma". Show the decoy stalling, the canary card chip, and "time burned". | **M:** "The scammer never knows he's caught. He's now talking to our decoy, which stalls him and hands him a canary card." |
| 1:18–1:30 | PNC lens → **Simulate scammer cashes out the decoy's card**. Show "canary fired", the tripwired payout account, and "PNC sent 5 chars". | **A:** "When he uses the card, the canary fires and his cash-out account is tripwired. PNC checks it by sending just 5 characters of a hash." |
| 1:30–1:42 | T-Mobile lens → toggle **Jake's line: SIM swapped**. Deliver the second Jake sample, tap **Yes, it's me**. Show "untrusted" and the hold staying. Toggle it back off. | **M:** "If the scammer swapped Jake's SIM, his 'yes' can't be trusted, so the money stays held." |
| 1:42–1:50 | Deliver the **Lakeview fraud dept** sample, then the **real Lakeview alert**. | **A:** "Businesses work the same way, but they only ever see a hash: Lakeview says it didn't send the fake one, and confirms the real one." |
| 1:50–1:58 | NVIDIA lens: show the agent graph lighting up (Claim extractor → Echo → Ground-truth label → Forge → Gate) and the badge. | **M:** "Every Nemotron call and tool call is visible, and every phone just learned a few-KB skill. That's Detour." |

**Honesty rules for the video:**
- Say "simulated" when the screen shows a SIMULATED tag: Jake's phone, carrier signals, PNC rails, canary cards, business endpoints.
- Only say "live" if the badge says LIVE. If it says REPLAY or MOCK, don't call it live.
- Don't say any accuracy or speed number unless it's on the LIVE scoreboard.

## Before you record

Live (Nemotron answering for real):

```bash
cd ~/Documents/Archives/AI\ Work/Claude/hackutd-research/Detour && ./run.sh
```

If venue Wi-Fi is bad, use the recorded backup (the badge will say REPLAY):

```bash
cd ~/Documents/Archives/AI\ Work/Claude/hackutd-research/Detour && DETOUR_REPLAY=1 ./run.sh
```

Do one dry run first, then click **Reset** before the real take.
