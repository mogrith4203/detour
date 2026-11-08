/* Detour phone-side claim resolver. Runs in the browser: Linda's contacts never leave the phone.
 * Given who a message CLAIMS to be (from the claim extractor), find the real person or business to ask.
 * Only a one-way hash of the resolved number goes to the carrier. Python twin: detour/resolver.py (parity-tested).
 */
(function (root, factory) {
  const M = (typeof module === "object" && module.exports) ? require("./matcher.js") : root.DetourMatcher;
  const api = factory(M);
  if (typeof module === "object" && module.exports) module.exports = api;
  if (typeof window !== "undefined") window.DetourResolver = api;
})(typeof self !== "undefined" ? self : this, function (M) {
  "use strict";
  // Linda's address book (synthetic, 555-01xx). Lives only on the phone.
  const CONTACTS = [
    { id: "c-jake", name: "Jake", relation: "grandson", number: "(214) 555-0130" },
    { id: "c-mia", name: "Mia", relation: "daughter", number: "(214) 555-0131" },
    { id: "c-ruth", name: "Ruth", relation: "friend", number: "(469) 555-0132" },
    { id: "c-tom", name: "Tom", relation: "son", number: "(972) 555-0133" },
  ];
  // Verified business registry (public). Businesses answer provenance checks by message hash only.
  const BUSINESSES = [
    { id: "lakeview", name: "Lakeview Credit Union", aliases: ["lakeview"], number: "(800) 555-0142" },
    { id: "parcelpost", name: "ParcelPost", aliases: ["parcelpost", "parcel post"], number: "(800) 555-0155" },
    { id: "txtoll", name: "TX Toll Services", aliases: ["tx toll", "txtoll", "toll services"], number: "(800) 555-0110" },
  ];
  const REL_GROUP = {
    grandson: "grandchild", granddaughter: "grandchild", grandchild: "grandchild",
    son: "child", daughter: "child", child: "child",
    nephew: "nephew/niece", niece: "nephew/niece", "nephew/niece": "nephew/niece",
    friend: "friend", brother: "sibling", sister: "sibling",
  };
  const digits = s => String(s || "").replace(/[^0-9]/g, "").replace(/^1(?=\d{10}$)/, "");
  const numberHash = n => M.sha256Sync(new TextEncoder().encode(digits(n))).slice(0, 16);
  const low = s => String(s || "").trim().toLowerCase();

  function resolveClaim(claim, contacts, sender) {
    const out = { match: "none", contact_id: null, name: null, relation: null, number_hash: null, business_id: null, from_real_number: false };
    if (!claim || !claim.claims_identity) return out;
    contacts = contacts || CONTACTS;
    const kind = low(claim.kind);
    if (kind === "business" || kind === "government") {
      const b = low(claim.business);
      if (!b) return out;
      const hit = BUSINESSES.find(x => x.aliases.some(a => b.includes(a)) || low(x.name) === b);
      if (!hit) return out;
      out.match = "business"; out.business_id = hit.id; out.name = hit.name;
      out.from_real_number = !!sender && digits(sender) === digits(hit.number);
      return out;
    }
    const name = low(claim.name);
    let hits = name ? contacts.filter(c => low(c.name) === name) : [];
    if (!hits.length && claim.relation) {
      const g = REL_GROUP[low(claim.relation)];
      if (g) hits = contacts.filter(c => REL_GROUP[low(c.relation)] === g);
    }
    if (hits.length !== 1) return out; // ambiguous or unknown: never guess who to ask
    const c = hits[0];
    out.match = "contact"; out.contact_id = c.id; out.name = c.name; out.relation = c.relation;
    out.number_hash = numberHash(c.number);
    out.from_real_number = !!sender && digits(sender) === digits(c.number);
    return out;
  }
  const msgHash = text => M.fingerprint(text);
  const msgHashSync = text => M.fingerprintSync(text);
  return { CONTACTS, BUSINESSES, resolveClaim, numberHash, msgHash, msgHashSync, digits };
});
