"""Identity Echo, step 1: extract WHO a message claims to be.

Nemotron returns a small JSON object. In MOCK mode (or if the model call fails)
a deterministic lexicon stand-in produces the same shape and the result is
labeled with its real mode. The claim never includes the message text itself,
so it is safe to hand to the Echo service.
"""
import re

CLAIM_SYSTEM = (
    "You read one text message and say who the SENDER claims to be. "
    "Return only a JSON object with these keys: "
    '"claims_identity" (true/false), '
    '"kind" ("family", "friend", "business", "government", "unknown"), '
    '"name" (the first name or business name the sender uses for themselves, or null), '
    '"relation" (e.g. "grandson", "daughter", "bank", or null), '
    '"business" (business or agency name if any, else null), '
    '"money_ask" (true if the message asks for money, gift cards, a payment, codes, account details, or to verify, log in, or call a new number), '
    '"confidence" (0 to 1). '
    "Do not repeat or quote the message."
)

RELATIONS = {
    "grandson": "family", "granddaughter": "family", "son": "family", "daughter": "family",
    "nephew": "family", "niece": "family", "brother": "family", "sister": "family",
    "mom": "family", "dad": "family", "cousin": "family", "grandchild": "family",
}
# words a sender uses about themselves when addressing a grandparent/parent
ADDRESS_TO_RELATION = {
    "grandma": "grandchild", "grandpa": "grandchild", "nana": "grandchild", "papa": "grandchild",
    "granny": "grandchild", "mom": "child", "mum": "child", "dad": "child", "auntie": "nephew/niece",
    "aunt": "nephew/niece", "uncle": "nephew/niece",
}
MONEY = re.compile(r"\$\s?\d|\b(money|bail|gift ?cards?|zelle|venmo|cash ?app|wire|western union|pay|payment|send|"
                   r"transfer|code|account|bitcoin|crypto|fee|lawyer|verify|log ?in|locked|suspended|card)\b", re.I)
SELF_NAME = re.compile(r"\b(?:it'?s|its|this is|im|i'm|i am)\s+([A-Z][a-z]{1,15}|[a-z]{2,15})\b", re.I)
NOT_NAMES = {"me", "your", "you", "the", "a", "an", "not", "so", "really", "just", "going", "in", "at", "on",
             "stuck", "here", "okay", "ok", "fine", "safe", "sorry", "urgent", "calling", "texting", "from", "with"}
BUSINESS = re.compile(r"\b([A-Z][A-Za-z&]+(?:\s[A-Z][A-Za-z&]+){0,2})\s+(?:bank|credit union|fraud|security|support|"
                      r"tolls?|delivery|post|IRS|dept|department)\b")
KNOWN_BUSINESS = re.compile(r"\b(lakeview|pnc|t-mobile|usps|ups|fedex|irs|ezpass|ntta|chase|wells fargo|amazon)\b", re.I)


def mock_claim(text):
    """Deterministic lexicon stand-in. Same output shape as the model."""
    t = text or ""
    low = t.lower()
    name = None
    for m in SELF_NAME.finditer(t):
        cand = m.group(1)
        if cand.lower() not in NOT_NAMES:
            name = cand.capitalize()
            break
    relation = None
    for word, rel in RELATIONS.items():
        if re.search(rf"\byour {word}\b|\bur {word}\b", low):
            relation = word
            break
    if not relation:
        for word, rel in ADDRESS_TO_RELATION.items():
            if re.search(rf"^\W*{word}\b|\b(hi|hey|dear)\s+{word}\b", low):
                relation = rel
                break
    business = None
    bm = KNOWN_BUSINESS.search(t)
    if bm:
        business = bm.group(1).title() if bm.group(1).lower() not in ("irs", "usps", "ups", "pnc", "ntta") else bm.group(1).upper()
    else:
        bm = BUSINESS.search(t)
        if bm:
            business = bm.group(1)
    if business and not name and not relation:
        kind = "government" if business.upper() in ("IRS",) else "business"
    elif name or relation:
        kind = "family" if relation else "friend"
    else:
        kind = "unknown"
    claims = kind != "unknown"
    return {
        "claims_identity": claims,
        "kind": kind,
        "name": name,
        "relation": relation,
        "business": business if kind in ("business", "government") else None,
        "money_ask": bool(MONEY.search(t)),
        "confidence": 0.7 if claims else 0.2,
    }


def normalize_claim(d):
    """Coerce model output into the fixed shape; never trust free-form keys."""
    kind = str(d.get("kind") or "unknown").lower()
    if kind not in ("family", "friend", "business", "government", "unknown"):
        kind = "unknown"

    def s(v, n=40):
        if v in (None, "", "null", "None"):
            return None
        return str(v).strip()[:n]

    try:
        conf = max(0.0, min(1.0, float(d.get("confidence", 0.5))))
    except (TypeError, ValueError):
        conf = 0.5
    return {
        "claims_identity": bool(d.get("claims_identity")) and kind != "unknown",
        "kind": kind,
        "name": s(d.get("name"), 30),
        "relation": s(d.get("relation"), 30),
        "business": s(d.get("business"), 60),
        "money_ask": bool(d.get("money_ask")),
        "confidence": round(conf, 2),
    }


def extract_claim(llm, text):
    """Returns (claim, mode). mode is the honest source: live / replay / mock."""
    if llm.mode != "mock":
        try:
            d = llm.json([{"role": "system", "content": CLAIM_SYSTEM},
                          {"role": "user", "content": text}], max_tokens=200, temperature=0)
            return normalize_claim(d), llm.mode
        except Exception:
            pass
    return normalize_claim(mock_claim(text)), "mock"
