// Runs the browser matcher (static/matcher.js) over cases for tests/test_parity.py.
// usage: node tests/parity.js <rules.json> <cases.json>  -> JSON results on stdout
const fs = require("fs");
const path = require("path");
const M = require(path.join(__dirname, "..", "static", "matcher.js"));

async function main() {
  const rules = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const cases = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
  for (const [k, src] of Object.entries(rules.patterns)) M.pyRe(src, k === "PHONE_RE" || k === "SPACED_DIGITS_RE" ? "" : "i");
  const out = [];
  for (const cs of cases) {
    const m = M.match(rules, cs.text);
    const threads = {};
    let res;
    for (const t of (cs.thread || []).concat([cs.text])) {
      const key = cs.sender || "unknown";
      res = await M.checkOnPhone(t, cs.sender, !!cs.known, rules, (threads[key] ||= []));
    }
    out.push({
      id: cs.id, decision: m.decision, score: m.score, asks: m.asks, best: m.best ? m.best.story_id : null,
      ranked: m.ranked.map(r => [r.story_id, r.score, r.detail.kw, r.detail.indicator]),
      redact: M.redact(rules, cs.text, ["Linda Park"]), redact_plain: M.redact(rules, cs.text),
      normalize: M.normalize(rules, cs.text), phones: M.phones(rules, cs.text), domains: M.domains(rules, cs.text),
      tokens: M.tokens(rules, cs.text), sender: M.senderStatus(rules, cs.sender || ""),
      fingerprint: M.fingerprintSync(cs.text), fingerprint_async: await M.fingerprint(cs.text),
      card: res.card, local_decision: res.local ? res.local.decision : null, strip: M.stripIndicators(rules, cs.text),
    });
  }
  process.stdout.write(JSON.stringify(out));
}
main().catch(e => { console.error(e); process.exit(1); });
