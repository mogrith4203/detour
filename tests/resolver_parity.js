// node tests/resolver_parity.js <cases.json> -> JSON results (static/resolver.js)
const fs = require("fs"), path = require("path");
const R = require(path.join(__dirname, "..", "static", "resolver.js"));
const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
process.stdout.write(JSON.stringify({
  data: { contacts: R.CONTACTS, businesses: R.BUSINESSES },
  out: cases.map(c => ({ r: R.resolveClaim(c.claim, null, c.sender), nh: R.numberHash(c.sender), mh: R.msgHashSync(c.text || "") })),
}));
