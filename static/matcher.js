/* Detour on-device matcher: a faithful JS port of detour/core.py (normalize ... match) and the phone half of
 * detour/engine.py check_message. It runs in the browser (the "phone") with rules from GET /api/phone/rules, so a
 * message never leaves the phone unless the customer consents. tests/test_parity.py checks it against Python.
 *
 * Python regex sources are translated, not copied: Python's \w \d \b are Unicode-aware and "." excludes only "\n",
 * so they are rewritten to Unicode property classes and the "u" flag is used (code-point semantics, like Python).
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (typeof window !== "undefined") window.DetourMatcher = api;
  else if (root) root.DetourMatcher = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  /* ---------------------------------------------------------------- Python regex -> JS */
  const W = "\\p{L}\\p{N}_";  // Python 3 str \w: alphanumerics (isalnum) plus underscore
  const S_SET = "\\t-\\r\\x1c-\\x20\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";  // str.isspace()
  const BOUND = `(?:(?<=[${W}])(?![${W}])|(?<![${W}])(?=[${W}]))`;
  const NBOUND = `(?:(?<=[${W}])(?=[${W}])|(?<![${W}])(?![${W}]))`;
  const SYNTAX = "^$\\.*+?()[]{}|/";
  const I_FIX = "\\u0130\\u0131";  // Python re.I lets 'i' match dotted capital I and dotless i; JS folding does not

  function translate(src, ignoreCase) {
    let out = "", i = 0, inClass = false, classStart = 0, classHasI = false, outStart = 0;
    const cp = c => c.codePointAt(0);
    while (i < src.length) {
      const c = src[i];
      if (c === "\\") {
        const n = src[i + 1]; i += 2;
        if (n === "w") out += inClass ? W : `[${W}]`;
        else if (n === "W") { if (inClass) throw new Error("\\W in class unsupported"); out += `[^${W}]`; }
        else if (n === "d") out += "\\p{Nd}";
        else if (n === "D") { if (inClass) throw new Error("\\D in class unsupported"); out += "\\P{Nd}"; }
        else if (n === "s") out += inClass ? S_SET : `[${S_SET}]`;
        else if (n === "S") { if (inClass) throw new Error("\\S in class unsupported"); out += `[^${S_SET}]`; }
        else if (n === "b") out += inClass ? "\\x08" : BOUND;
        else if (n === "B") out += NBOUND;
        else if (n === "A") out += "^";
        else if (n === "Z") out += "(?![\\s\\S])";
        else if (/[0-9nrtfvxu]/.test(n)) out += "\\" + n;
        else if (SYNTAX.includes(n) || (n === "-" && inClass)) out += "\\" + n;
        else out += `\\u{${cp(n).toString(16)}}`;  // Python allows escaping any punctuation; u-mode does not
        continue;
      }
      if (inClass) {
        if (c === "]" && i > classStart) {
          if (ignoreCase && classHasI) out = out.slice(0, outStart) + I_FIX + out.slice(outStart);
          out += "]"; inClass = false; i++; continue;
        }
        if (c === "]") { out += "\\]"; i++; continue; }
        if (ignoreCase) {
          if (c === "i" || c === "I") classHasI = true;
          if (src[i + 1] === "-" && src[i + 2] && src[i + 2] !== "]") {
            const lo = c, hi = src[i + 2] === "\\" ? null : src[i + 2];
            if (hi && ((lo <= "i" && hi >= "i") || (lo <= "I" && hi >= "I"))) classHasI = true;
          }
        }
        out += c; i++; continue;
      }
      if (c === "[") {
        inClass = true; classHasI = false; out += "["; i++;
        if (src[i] === "^") { out += "^"; i++; }
        classStart = i; outStart = out.length; continue;
      }
      if (c === ".") { out += "[^\\n]"; i++; continue; }
      if (c === "$") { out += "(?=\\n?(?![\\s\\S]))"; i++; continue; }
      if (ignoreCase && (c === "i" || c === "I") && !/\(\?<?[=!]?$/.test(out.slice(-4))) { out += `[iI${I_FIX}]`; i++; continue; }
      out += c; i++;
    }
    return out;
  }
  function pyRe(src, flags) {  // flags: "" or "i"
    return new RegExp(translate(src, flags.includes("i")), "u" + flags);
  }
  const reCache = new Map();
  function R(src, flags = "", g = false) {
    const k = src + "\u0000" + flags + (g ? "g" : "");
    let r = reCache.get(k);
    if (!r) { r = new RegExp(translate(src, flags.includes("i")), "u" + flags + (g ? "g" : "")); reCache.set(k, r); }
    r.lastIndex = 0;
    return r;
  }
  const search = (src, flags, s) => R(src, flags).exec(s);
  const sub = (src, flags, s, fn) => s.replace(R(src, flags, true), fn);
  const findall = (src, flags, s) => [...s.matchAll(R(src, flags, true))];

  /* ---------------------------------------------------------------- Python string helpers */
  const PY_SPACE = new RegExp(`^[${S_SET}]+|[${S_SET}]+$`, "gu");
  const pyStrip = s => s.replace(PY_SPACE, "");
  const cps = s => Array.from(s);
  const pySlice = (s, n) => (s.length <= n ? s : cps(s).slice(0, n).join(""));
  function cmpCP(a, b) {  // Python sorts str by code point; JS sort() by UTF-16 unit
    const A = cps(a), B = cps(b);
    for (let i = 0; i < Math.min(A.length, B.length); i++) {
      const x = A[i].codePointAt(0), y = B[i].codePointAt(0);
      if (x !== y) return x - y;
    }
    return A.length - B.length;
  }
  const sortedSet = arr => [...new Set(arr)].sort(cmpCP);
  const has = (o, k) => o != null && Object.prototype.hasOwnProperty.call(o, k);
  const cap1 = a => (a ? a[0].toUpperCase() + a.slice(1) : a);

  function pyRound3(x) {
    // Python round(x, 3): correctly rounded on the exact binary value, ties to even. toFixed rounds ties up.
    const t = x * 2000;
    if (Number.isInteger(t) && t % 2 !== 0 && t / 2000 === x) {
      const lo = (t - 1) / 2, hi = (t + 1) / 2;
      return (lo % 2 === 0 ? lo : hi) / 1000;
    }
    return parseFloat(x.toFixed(3));
  }

  /* ---------------------------------------------------------------- rules (compiled once per rules object) */
  const compiled = new WeakMap();
  function prep(rules) {
    let c = compiled.get(rules);
    if (c) return c;
    const P = rules.patterns || {};
    const flag = k => (k === "PHONE_RE" || k === "SPACED_DIGITS_RE" ? "" : "i");
    const pats = {};
    for (const k of Object.keys(P)) { pyRe(P[k], flag(k)); pats[k] = [P[k], flag(k)]; }  // throws early if any won't compile
    const stories = {};
    for (const s of rules.stories || []) stories[s.id] = s;
    c = {
      pats, stories, storyList: rules.stories || [],
      stop: new Set(rules.stop || []), shorteners: new Set(rules.shorteners || []),
      allow: rules.allowlist || [], registered: rules.registered_senders || {},
      homo: new Map(Object.entries(rules.homoglyphs || {})), good: new Set(rules.known_good || []),
      warn: rules.thresholds ? rules.thresholds.warn : 0.6, clear: rules.thresholds ? rules.thresholds.clear : 0.3,
      window: rules.thread_window || 3, steps: rules.category_steps || {}, labels: rules.category_label || {},
    };
    compiled.set(rules, c);
    return c;
  }
  const P = (c, k) => c.pats[k];
  const pSearch = (c, k, s) => search(P(c, k)[0], P(c, k)[1], s);

  /* ---------------------------------------------------------------- signals (core.py) */
  function translateHomo(c, s) {
    let out = "";
    for (const ch of s) out += c.homo.has(ch) ? c.homo.get(ch) : ch;
    return out;
  }
  function normalize(c, text) {
    let t = (text || "").normalize("NFKC");
    t = translateHomo(c, t);
    t = sub(P(c, "SPACED_DIGITS_RE")[0], "", t, m => m.replace(/[ .]/g, ""));
    return t;
  }
  function disguises(c, text) {
    const raw = text || "", found = [];
    if (translateHomo(c, raw) !== raw) found.push("uses look-alike letters");
    if (search(P(c, "SPACED_DIGITS_RE")[0], "", raw.normalize("NFKC"))) found.push("spaces out a phone number");
    return found;
  }
  function phones(c, text) {
    return sortedSet(findall(P(c, "PHONE_RE")[0], "", normalize(c, text)).map(m => `(${m[1]}) ${m[2]}-${m[3]}`));
  }
  function senderStatus(c, sender) {
    const s = pyStrip(sender || "");
    if (search("\\A(?:\\d{5,6})\\Z", "", s)) return {status: "registered short code", registered: true};
    const p = phones(c, s);
    if (p.length && has(c.registered, p[0])) return {status: `registered business sender (${c.registered[p[0]]})`, registered: true};
    if (p.length) return {status: "unregistered 10-digit number", registered: false};
    return {status: "unknown sender", registered: false};
  }
  function domains(c, text) {
    const t = normalize(c, text);
    const found = findall(P(c, "URL_RE")[0], "i", t).map(m => m[1].toLowerCase().replace(/\.+$/, ""));
    for (const m of findall(P(c, "BARE_DOMAIN_RE")[0], "i", t)) found.push(m[1].toLowerCase());
    return sortedSet(found);
  }
  function isAllowlisted(c, value) {
    const v = value.toLowerCase();
    for (const k of c.allow) { const kl = k.toLowerCase(); if (v === kl || v.endsWith("." + kl)) return k; }
    return null;
  }
  function tokens(c, text) {
    let t = sub(P(c, "URL_RE")[0], "i", normalize(c, text), () => " ");
    t = sub("https?://\\S+", "", t, () => " ");
    t = sub(P(c, "BARE_DOMAIN_RE")[0], "i", t, () => " ");
    return findall("[a-z][a-z']+", "", t.toLowerCase()).map(m => m[0]).filter(w => !c.stop.has(w) && w.length > 2);
  }

  /* ---- Python's "idna" codec (IDNA 2003) for the 'disguised web address' ask */
  const T = (j, bias) => Math.min(26, Math.max(1, 36 * (j + 1) - bias));
  function adapt(delta, first, numchars) {
    delta = first ? Math.floor(delta / 700) : Math.floor(delta / 2);
    delta += Math.floor(delta / numchars);
    let div = 0;
    while (delta > 455) { delta = Math.floor(delta / 35); div += 36; }
    return div + Math.floor(36 * delta / (delta + 38));
  }
  function punyDecode(text) {  // encodings.punycode.punycode_decode(errors="strict")
    const pos = text.lastIndexOf("-");
    const base = pos === -1 ? [] : cps(text.slice(0, pos));
    const ext = (pos === -1 ? text : text.slice(pos + 1)).toUpperCase();
    let ch = 0x80, p = -1, bias = 72, e = 0;
    while (e < ext.length) {
      let result = 0, w = 1, j = 0;
      const first = e === 0;
      for (;;) {
        if (e >= ext.length) throw new Error("incomplete punycode string");
        const k = ext.charCodeAt(e++);
        let digit;
        if (k >= 0x41 && k <= 0x5a) digit = k - 0x41;
        else if (k >= 0x30 && k <= 0x39) digit = k - 22;
        else throw new Error("invalid extended code point");
        const t = T(j, bias);
        result += digit * w;
        if (!Number.isSafeInteger(result)) throw new Error("overflow");
        if (digit < t) break;
        w *= 36 - t; j++;
      }
      p += result + 1;
      ch += Math.floor(p / (base.length + 1));
      if (ch > 0x10ffff) throw new Error("invalid character");
      p %= base.length + 1;
      base.splice(p, 0, String.fromCodePoint(ch));
      bias = adapt(result, first, base.length);
    }
    return base.join("");
  }
  function punyEncode(str) {  // encodings.punycode.punycode_encode
    const chars = cps(str);
    const base = chars.filter(x => x.codePointAt(0) < 128).join("");
    const extended = [...new Set(chars.filter(x => x.codePointAt(0) >= 128))].sort(cmpCP);
    const deltas = [];
    let oldchar = 0x80, oldindex = -1;
    for (const cch of extended) {
      const code = cch.codePointAt(0);
      let index = -1, pos = -1;
      const curlen = chars.filter(x => x.codePointAt(0) < code).length;
      let delta = (curlen + 1) * (code - oldchar);
      for (;;) {
        // selective_find
        let found = false;
        while (true) {
          pos++;
          if (pos === chars.length) break;
          const x = chars[pos];
          if (x === cch) { index++; found = true; break; } else if (x.codePointAt(0) < code) index++;
        }
        if (!found) break;
        delta += index - oldindex; deltas.push(delta - 1); oldindex = index; delta = 0;
      }
      oldchar = code;
    }
    const digits = "abcdefghijklmnopqrstuvwxyz0123456789";
    let out = "", bias = 72;
    deltas.forEach((delta, points) => {
      let N = delta, j = 0;
      for (;;) {
        const t = T(j, bias);
        if (N < t) { out += digits[N]; break; }
        out += digits[t + ((N - t) % (36 - t))]; N = Math.floor((N - t) / (36 - t)); j++;
      }
      bias = adapt(delta, points === 0, base.length + points + 1);
    });
    return base ? base + "-" + out : out;
  }
  const B1 = /[­͏᠆᠋-᠍​-‍⁠︀-️﻿]/gu;
  function nameprep(label) {  // approximation of stringprep nameprep: map-to-nothing, case fold, NFKC
    return label.replace(B1, "").toLowerCase().normalize("NFKC");
  }
  const isAscii = s => /^[\x00-\x7f]*$/.test(s);
  function toASCII(label) {
    if (isAscii(label)) { if (label.length > 0 && label.length < 64) return label; throw new Error("label length"); }
    const np = nameprep(label);
    if (isAscii(np)) { if (np.length > 0 && cps(np).length < 64) return np; throw new Error("label length"); }
    if (np.toLowerCase().startsWith("xn--")) throw new Error("ACE prefix");
    const a = "xn--" + punyEncode(np);
    if (a.length < 64) return a;
    throw new Error("label too long");
  }
  function toUnicode(label) {
    if (cps(label).length > 1024) throw new Error("label way too long");
    if (!label.toLowerCase().startsWith("xn--")) return label;
    const result = punyDecode(label.slice(4));
    if (label.toLowerCase() !== toASCII(result)) throw new Error("IDNA does not round-trip");
    return result;
  }
  function decodeIdna(d) {
    if (!d.includes("xn--")) return d;
    try {
      if (!isAscii(d)) return d;
      if (!d) return "";
      const labels = d.split(".");
      let trailing = "";
      if (labels.length && labels[labels.length - 1].length === 0) { trailing = "."; labels.pop(); }
      return labels.map(toUnicode).join(".") + trailing;
    } catch (e) { return d; }
  }

  function riskyAsks(c, text) {
    const reasons = [];
    const raw = text;
    text = normalize(c, text);
    const doms = domains(c, text);
    const short = doms.filter(d => c.shorteners.has(d));
    if (short.length) reasons.push(`shortened link hides where it goes (${short[0]})`);
    const puny = doms.filter(d => d.includes("xn--"));
    if (puny.length) reasons.push(`disguised web address (${decodeIdna(puny[0])})`);
    const bad = doms.filter(d => !isAllowlisted(c, d) && !short.includes(d) && !puny.includes(d));
    if (bad.length) reasons.push(`link to an unverified site (${bad[0]})`);
    reasons.push(...disguises(c, raw));
    const badNums = phones(c, text).filter(p => !isAllowlisted(c, p));
    if (badNums.length && (pSearch(c, "CALL_VERB_RE", text) || pSearch(c, "URGENCY_RE", text) ||
        search("\\b(verify|confirm|unlock|reactivate)\\b", "i", text)))
      reasons.push(`asks you to contact an unverified number (${badNums[0]})`);
    const pay = pSearch(c, "PAYMENT_RE", text);
    if (pay) reasons.push(`payment request (${pay[0]})`);
    if (pSearch(c, "OFFPLATFORM_RE", text)) reasons.push("moves the chat to another app");
    if (pSearch(c, "SECRECY_RE", text)) reasons.push("asks you to keep it secret");
    if (pSearch(c, "CREDENTIAL_RE", text)) reasons.push("asks for codes or card details");
    return reasons;
  }

  const reEscape = s => s.replace(/[\^$\\.*+?()[\]{}|/]/g, "\\$&");
  function redact(c, text, ownerNames = []) {
    let t = normalize(c, text);
    t = sub("[\\w.+-]+@[\\w-]+\\.[\\w.]+", "", t, () => "[email]");
    t = sub("\\b\\d{3}-\\d{2}-\\d{4}\\b", "", t, () => "[ssn]");
    t = sub("\\b(?:\\d[ -]?){12,18}\\d\\b", "", t, () => "[card]");
    t = sub("\\b(ending|ends) (in )?\\d{4}\\b", "i", t, (m, g1) => g1 + " [last4]");
    t = sub("\\b\\d{1,5} [A-Z][a-z]+(?: [A-Z][a-z]+)? (?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Blvd|Ct|Court|Way|Pkwy)\\b\\.?", "", t, () => "[address]");
    t = sub("\\b(code|otp|pin|passcode)( is|:)? ?\\d{4,8}\\b", "i", t, (m, g1) => g1 + " [code]");
    t = sub("\\b\\d{6,}\\b", "", t, () => "[number]");
    for (const n of ownerNames || []) if (n) t = t.replace(new RegExp(reEscape(n), "giu"), () => "[name]");
    return t;
  }

  /* ---------------------------------------------------------------- matcher */
  function skillScore(c, text, story) {
    text = normalize(c, text);
    const low = text.toLowerCase();
    const ind = phones(c, text).filter(p => has(story.numbers, p)).concat(domains(c, text).filter(d => has(story.domains, d)));
    const asks = riskyAsks(c, text);
    if (ind.length && asks.length) return [0.97, {indicator: ind, kw: [], asks}];
    const kws = story.skill.keywords;
    const toks = new Set(tokens(c, text));
    const hit = [...toks].filter(w => has(kws, w));
    let kw = hit.reduce((a, w) => a + kws[w], 0) / 3.0;
    const phraseHits = (story.skill.phrases || []).filter(p => low.includes(p));
    kw = Math.min(1.0, kw + 0.2 * phraseHits.length);
    let score;
    if (asks.length) score = 0.65 * kw + 0.35 + (pSearch(c, "URGENCY_RE", text) ? 0.05 : 0);
    else score = 0.45 * kw;
    return [pyRound3(Math.min(score, 0.99)), {indicator: ind, kw: hit.sort(cmpCP).concat(phraseHits), asks}];
  }
  function match(c, text) {
    const ranked = [];
    for (const s of c.storyList) {
      if (s.tainted_only) continue;
      const [sc, det] = skillScore(c, text, s);
      ranked.push({story_id: s.id, title: s.title, score: sc, detail: det});
    }
    ranked.sort((a, b) => b.score - a.score);  // stable, like Python's sort(reverse=True)
    const best = ranked.length ? ranked[0] : null;
    const asks = riskyAsks(c, text);
    let top = best ? best.score : (asks.length ? 0.35 : 0.0);
    const nt = normalize(c, text);
    if (top < c.clear && pSearch(c, "MONEY_RE", nt) && (pSearch(c, "AUTHORITY_RE", nt) || pSearch(c, "URGENCY_RE", nt))) top = c.clear;
    const decision = top >= c.warn ? "warn" : top < c.clear ? "clear" : "unsure";
    return {decision, score: top, best, ranked: ranked.slice(0, 3), asks};
  }

  /* ---------------------------------------------------------------- engine.py helpers */
  function stripIndicators(c, text) {
    let t = sub(P(c, "PHONE_RE")[0], "", String(text == null ? "" : text), () => "[number]");
    t = sub("https?://\\S+|\\b[\\w-]+\\.(?:com|net|org|info|top|xyz|example|ly|io|co|app|site|online|link)\\b\\S*", "i", t, () => "[link]");
    return pySlice(t, 200);
  }

  /* SHA-256: pure JS (Node tests, non-secure origins) + crypto.subtle when available */
  const K = new Uint32Array([0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb,
    0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f,
    0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);
  function sha256Sync(bytes) {
    const l = bytes.length, nb = ((l + 9 + 63) >> 6) << 6, m = new Uint8Array(nb);
    m.set(bytes); m[l] = 0x80;
    const dv = new DataView(m.buffer);
    dv.setUint32(nb - 8, Math.floor(l / 0x20000000)); dv.setUint32(nb - 4, (l << 3) >>> 0);
    const H = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
    const w = new Uint32Array(64);
    const rot = (x, n) => (x >>> n) | (x << (32 - n));
    for (let o = 0; o < nb; o += 64) {
      for (let i = 0; i < 16; i++) w[i] = dv.getUint32(o + i * 4);
      for (let i = 16; i < 64; i++) {
        const s0 = rot(w[i - 15], 7) ^ rot(w[i - 15], 18) ^ (w[i - 15] >>> 3), s1 = rot(w[i - 2], 17) ^ rot(w[i - 2], 19) ^ (w[i - 2] >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
      }
      let [a, b, c, d, e, f, g, h] = H;
      for (let i = 0; i < 64; i++) {
        const t1 = (h + (rot(e, 6) ^ rot(e, 11) ^ rot(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) >>> 0;
        const t2 = ((rot(a, 2) ^ rot(a, 13) ^ rot(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
        h = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      H[0] += a; H[1] += b; H[2] += c; H[3] += d; H[4] += e; H[5] += f; H[6] += g; H[7] += h;
    }
    return [...H].map(x => x.toString(16).padStart(8, "0")).join("");
  }
  const fpNorm = text => sub("\\s+", "", pyStrip(text || "").toLowerCase(), () => " ");
  const utf8 = s => new TextEncoder().encode(s);
  function fingerprintSync(text) { return sha256Sync(utf8(fpNorm(text))).slice(0, 16); }
  async function fingerprint(text) {
    const subtle = typeof crypto !== "undefined" && crypto && crypto.subtle;
    if (subtle) {
      try {
        const buf = await subtle.digest("SHA-256", utf8(fpNorm(text)));
        return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
      } catch (e) { /* fall through */ }
    }
    return fingerprintSync(text);
  }
  const byteLen = s => utf8(s || "").length;

  /* ---------------------------------------------------------------- engine.check_message, phone side */
  async function checkOnPhone(text, sender, known, rules, thread) {
    const c = prep(rules);
    sender = sender || "";
    const steps = [];
    const out = (decision, card, local, extra = {}) => ({
      steps, card, local, cloud_bytes: 0, ...extra,
      report: {decision, story_id: (decision === "warn" && local && local.best) ? local.best.story_id : "", score: local ? Number(local.score) || 0 : 0},
    });
    if (known) {
      steps.push({stage: "contact", note: "Sender is a saved contact. Not screened."});
      return out("contact", {level: "clear", title: "From a saved contact", why: [], next_step: ""}, null);
    }
    thread = thread || [];
    thread.push(text);
    if (thread.length > c.window) thread.splice(0, thread.length - c.window);
    const ctx = thread.join(" ");
    const fp = await fingerprint(text);
    if (c.good.has(fp)) {
      const local = {decision: "clear", score: 0, best: null, ranked: [], asks: [],
        note: "Same message was already verified as legitimate (checked against a list of hashes synced to this phone)."};
      steps.push({stage: "local", agent: "On-device matcher", data: local});
      return out("clear", {level: "clear", title: "Looks legitimate", why: [local.note], next_step: ""}, local, {fingerprint: fp});
    }
    const local = match(c, ctx);
    local.sender = senderStatus(c, sender);
    local.thread_len = thread.length;
    steps.push({stage: "local", agent: "On-device matcher", data: local});
    const STRONG = ["link to", "asks you to contact", "shortened", "disguised"];
    if (local.decision === "warn" && local.sender.registered && !local.asks.some(a => STRONG.some(p => a.startsWith(p))))
      local.decision = "unsure";
    if (local.decision === "warn") {
      const story = c.stories[local.best.story_id];
      const step = has(c.steps, story.category) ? c.steps[story.category] : c.steps.other;
      let card;
      if (story.status !== "warn") {
        card = {level: "unsure", title: "Possible scam (still being confirmed)", story: stripIndicators(c, story.title),
          why: ["Matches a play only one decoy has seen so far."].concat(local.asks.slice(0, 1)), next_step: step};
      } else {
        const label = (has(c.labels, story.category) ? c.labels[story.category] : "scam").toLowerCase();
        card = {level: "warn", title: "This matches an active scam", story: stripIndicators(c, story.title),
          why: [`Same play our decoys caught: ${label}, pretending to be ${stripIndicators(c, story.impersonates || "someone you trust")}.`]
            .concat(local.asks.slice(0, 2).map(cap1)), next_step: step, story_id: story.id};
      }
      return out("warn", card, local, {fingerprint: fp});
    }
    if (local.decision === "unsure" && !local.asks.length && local.sender.registered) {
      return out("clear", {level: "clear", title: "Looks legitimate",
        why: [`Sent from a ${local.sender.status}.`, "It doesn't ask you to pay, click, or call a new number."], next_step: ""}, local, {fingerprint: fp});
    }
    if (local.decision === "clear") {
      return out("clear", {level: "clear", title: "No known scam pattern", why: ["No risky request and no match to an active play."], next_step: ""}, local, {fingerprint: fp});
    }
    const why = ["This doesn't match a play we know yet."].concat(local.asks.slice(0, 2).map(cap1));
    return out("unsure", {level: "unsure", title: "We're not sure about this one", why, next_step: c.steps.other, consent: true},
      local, {fingerprint: fp, context: ctx});
  }

  /* public API: rules-bound wrappers mirroring core.py names */
  const bind = fn => (rules, ...a) => fn(prep(rules), ...a);
  return {
    version: 1, translate, pyRe, pyRound3, sha256Sync, fingerprint, fingerprintSync, byteLen, prep,
    normalize: bind(normalize), disguises: bind(disguises), senderStatus: bind(senderStatus), phones: bind(phones),
    domains: bind(domains), decodeIdna, isAllowlisted: bind(isAllowlisted), tokens: bind(tokens), riskyAsks: bind(riskyAsks),
    redact: bind(redact), skillScore: (rules, text, story) => skillScore(prep(rules), text, story),
    match: bind(match), stripIndicators: bind(stripIndicators), checkOnPhone,
  };
});
