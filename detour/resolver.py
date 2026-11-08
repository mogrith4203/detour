"""Python twin of static/resolver.js (the phone-side claim resolver). Used by tests and the server-side
reference flow; the demo phone runs the JS copy so contacts never leave the browser. Parity-tested."""
import hashlib
import re

CONTACTS = [
    {"id": "c-jake", "name": "Jake", "relation": "grandson", "number": "(214) 555-0130"},
    {"id": "c-mia", "name": "Mia", "relation": "daughter", "number": "(214) 555-0131"},
    {"id": "c-ruth", "name": "Ruth", "relation": "friend", "number": "(469) 555-0132"},
    {"id": "c-tom", "name": "Tom", "relation": "son", "number": "(972) 555-0133"},
]
BUSINESSES = [
    {"id": "lakeview", "name": "Lakeview Credit Union", "aliases": ["lakeview"], "number": "(800) 555-0142"},
    {"id": "parcelpost", "name": "ParcelPost", "aliases": ["parcelpost", "parcel post"], "number": "(800) 555-0155"},
    {"id": "txtoll", "name": "TX Toll Services", "aliases": ["tx toll", "txtoll", "toll services"], "number": "(800) 555-0110"},
]
REL_GROUP = {
    "grandson": "grandchild", "granddaughter": "grandchild", "grandchild": "grandchild",
    "son": "child", "daughter": "child", "child": "child",
    "nephew": "nephew/niece", "niece": "nephew/niece", "nephew/niece": "nephew/niece",
    "friend": "friend", "brother": "sibling", "sister": "sibling",
}


def digits(s):
    d = re.sub(r"[^0-9]", "", str(s or ""))
    return d[1:] if len(d) == 11 and d.startswith("1") else d


def number_hash(n):
    return hashlib.sha256(digits(n).encode()).hexdigest()[:16]


def msg_hash(text):
    norm = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def _low(s):
    return str(s or "").strip().lower()


def resolve_claim(claim, contacts=None, sender=""):
    out = {"match": "none", "contact_id": None, "name": None, "relation": None, "number_hash": None,
           "business_id": None, "from_real_number": False}
    if not claim or not claim.get("claims_identity"):
        return out
    contacts = CONTACTS if contacts is None else contacts
    kind = _low(claim.get("kind"))
    if kind in ("business", "government"):
        b = _low(claim.get("business"))
        if not b:
            return out
        hit = next((x for x in BUSINESSES if any(a in b for a in x["aliases"]) or _low(x["name"]) == b), None)
        if not hit:
            return out
        out.update(match="business", business_id=hit["id"], name=hit["name"],
                   from_real_number=bool(sender) and digits(sender) == digits(hit["number"]))
        return out
    name = _low(claim.get("name"))
    hits = [c for c in contacts if _low(c["name"]) == name] if name else []
    if not hits and claim.get("relation"):
        g = REL_GROUP.get(_low(claim.get("relation")))
        if g:
            hits = [c for c in contacts if REL_GROUP.get(_low(c["relation"])) == g]
    if len(hits) != 1:
        return out
    c = hits[0]
    out.update(match="contact", contact_id=c["id"], name=c["name"], relation=c["relation"], number_hash=number_hash(c["number"]),
               from_real_number=bool(sender) and digits(sender) == digits(c["number"]))
    return out
