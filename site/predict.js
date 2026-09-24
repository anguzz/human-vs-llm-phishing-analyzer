/*
 * predict.js - browser-side mirror of train.py. Load after model.js:
 *   <script src="model.js"></script>
 *   <script src="predict.js"></script>
 *
 *   const r = predictEmail(text);   // { p, isPhishing, features, contributions }
 *   checkParity();                   // true if JS matches Python on MODEL.tests
 *
 * normalize / prep / tokenize / hasTerm / numericFeatures must stay identical
 * to the Python functions of the same name. Change both, then re-run train.py.
 */
(function (global) {
  "use strict";

  const URL_RE = /https?:\/\/\S+|\b(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|io|co|info|biz|us|uk|ru|xyz)\b(?:\/\S*)?/gi;
  const EMAIL_RE = /\S+@\S+/g;
  // Union of Python's and JavaScript's whitespace sets (see train.py WS_RE).
  const WS_RE = /[\s\u001c-\u001f\u0085]+/g;

  // Map, not {}: a plain object would treat "constructor" etc. as existing keys.
  const VOCAB = new Map(MODEL.vocab.map((w, i) => [w, i]));
  const escapeRe = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const termRe = t => new RegExp("(?:^|[^a-z0-9])" + escapeRe(t));
  const URGENCY = MODEL.urgency.map(t => [t, termRe(t)]);
  const CTA = MODEL.cta.map(t => [t, termRe(t)]);

  const normalize = s => String(s).normalize("NFKC").replace(WS_RE, " ").replace(/^ +| +$/g, "");
  const prep = s => s.toLowerCase().replace(EMAIL_RE, " ");

  function tokenize(text) {
    const toks = (prep(text).match(/[a-z0-9]+/g) || []).filter(t => t.length >= 2);
    const grams = toks.slice();
    for (let i = 0; i + 1 < toks.length; i++) grams.push(toks[i] + " " + toks[i + 1]);
    return grams;
  }

  function numericFeatures(text) {
    const low = prep(text);
    const words = text ? text.split(" ").length : 0;
    const letters = (text.match(/[A-Za-z]/g) || []).length;
    const caps = (text.match(/[A-Z]/g) || []).length;
    const punct = (text.match(/[!?]/g) || []).length;
    const urgencyHits = URGENCY.filter(([, re]) => re.test(low)).map(([t]) => t);
    const ctaHits = CTA.filter(([, re]) => re.test(low)).map(([t]) => t);
    const urls = (low.match(URL_RE) || []).length;
    return {
      values: [
        Math.log1p(words),
        Math.log1p(urls),
        urgencyHits.length,
        ctaHits.length,
        letters ? caps / letters : 0,
        (100 * punct) / Math.max(words, 1),
      ],
      words, chars: text.length, urls, urgencyHits, ctaHits,
      capsPct: letters ? (100 * caps) / letters : 0, punct,
    };
  }

  function predictEmail(raw) {
    const text = normalize(raw);

    // TF-IDF: sublinear tf * idf, L2-normalized over in-vocabulary terms
    const counts = new Map();
    for (const g of tokenize(text)) if (VOCAB.has(g)) counts.set(g, (counts.get(g) || 0) + 1);
    const weights = [];
    let norm = 0;
    for (const [g, c] of counts) {
      const i = VOCAB.get(g);
      const w = (1 + Math.log(c)) * MODEL.idf[i];
      weights.push([g, i, w]);
      norm += w * w;
    }
    norm = Math.sqrt(norm) || 1;

    let z = MODEL.intercept;
    const contributions = [];
    for (const [g, i, w] of weights) {
      const c = (w / norm) * MODEL.coef[i];
      z += c;
      contributions.push({ term: g, value: c });
    }

    const f = numericFeatures(text);
    const N = MODEL.numeric;
    f.values.forEach((x, i) => {
      const c = ((x - N.mean[i]) / N.std[i]) * N.coef[i];
      z += c;
      contributions.push({ term: "[" + N.names[i] + "]", value: c });
    });

    contributions.sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
    const p = 1 / (1 + Math.exp(-z));
    return { p, isPhishing: p >= 0.5, features: f, contributions };
  }

  function checkParity(tol = 1e-4) {
    let worst = 0;
    for (const t of MODEL.tests) worst = Math.max(worst, Math.abs(predictEmail(t.text).p - t.p));
    const ok = worst < tol;
    (ok ? console.info : console.error)(`Parity ${ok ? "OK" : "FAILED"}: max diff ${worst.toExponential(2)} over ${MODEL.tests.length} tests`);
    return ok;
  }

  Object.assign(global, { predictEmail, checkParity, normalizeEmail: normalize });
})(typeof window !== "undefined" ? window : globalThis);