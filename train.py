"""
train.py - GBA 6740 Group 2: AI-Enabled Phishing Email Analyzer

Run ONCE on your own machine. Reads the 4 Kaggle CSVs, trains
TF-IDF + Logistic Regression, prints accuracy, and writes two files
the website loads with plain <script> tags (works from file://):

    model.js   -> const MODEL = {...}   vocab, idf, coefficients, scaler, parity tests
    stats.js   -> const STATS = {...}   dashboard numbers + accuracy

Usage:
    pip install -r requirements.txt
    python train.py --data path/to/dataset --out path/to/site

Expected dataset layout (as downloaded from Kaggle):
    <data>/human-generated/phishing.csv
    <data>/human-generated/legit.csv
    <data>/llm-generated/phishing.csv
    <data>/llm-generated/legit.csv

IMPORTANT: normalize(), tokenize(), has_term() and numeric_features() are
mirrored in predict.js. If you change one here, change it there too, then
re-run. MODEL.tests lets the page verify both sides still agree.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import unicodedata
from collections import Counter
from email.header import decode_header, make_header
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split

SEED = 42
GROUPS = {  # id: (folder, file, source, class)
    "hp": ("human-generated", "phishing.csv", "human", 1),
    "hl": ("human-generated", "legit.csv", "human", 0),
    "lp": ("llm-generated", "phishing.csv", "llm", 1),
    "ll": ("llm-generated", "legit.csv", "llm", 0),
}
GROUP_NAMES = {"hp": "Human phishing", "lp": "LLM phishing", "hl": "Human legit", "ll": "LLM legit"}

URGENCY = ["verify", "confirm", "urgent", "immediately", "suspend", "act now", "expire",
           "limited time", "within 24 hours", "final notice", "locked", "unauthorized"]
CTA = ["click here", "click the link", "update now", "confirm your account",
       "verify your account", "log in", "sign in", "download"]

# Whitespace: Python's \s and JavaScript's \s disagree on a few characters
# (U+FEFF, U+0085, U+001C-001F). Both sides collapse the union of the two.
WS_RE = re.compile(r"[\s\ufeff]+")
EMAIL_RE = re.compile(r"\S+@\S+")
# re.ASCII so \b behaves like JavaScript's (ASCII-only word characters).
URL_RE = re.compile(
    r"https?://\S+|\b(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*"
    r"\.(?:com|net|org|io|co|info|biz|us|uk|ru|xyz)\b(?:/\S*)?",
    re.I | re.ASCII,
)
TOKEN_RE = re.compile(r"[a-z0-9]+")


# ---------------------------------------------------------------- loading
def decode_subject(s) -> str:
    """Some human-phishing subjects are still MIME-encoded (=?UTF-8?B?...?=)."""
    s = "" if pd.isna(s) else str(s)
    if "=?" not in s:
        return s
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s


def load_group(data_dir: Path, gid: str) -> list[str]:
    folder, fname, source, _ = GROUPS[gid]
    path = data_dir / folder / fname

    if source == "human":
        df = pd.read_csv(path)  # properly quoted; multi-line bodies are fine
        texts = [decode_subject(s) + " " + ("" if pd.isna(b) else str(b))
                 for s, b in zip(df["subject"], df["body"])]
    elif fname == "phishing.csv":
        # llm-generated/phishing.csv is NOT quoted: commas inside the text split
        # rows into 2-30 fields. The label is always the last field, so split
        # each line on its LAST comma.
        lines = path.read_text(encoding="utf-8").splitlines()[1:]
        texts = [ln.rsplit(",", 1)[0] for ln in lines if ln.strip()]
    else:
        texts = pd.read_csv(path)["text"].fillna("").astype(str).tolist()

    # The label column is ignored on purpose; folder + file name decide the class.
    assert len(texts) == 1000, f"{path}: expected 1000 rows, got {len(texts)}"
    return texts


# ------------------------------------------- mirrored in predict.js
def normalize(text: str) -> str:
    """NFKC + collapse whitespace. JS: s.normalize('NFKC').replace(/[\\s\\u001c-\\u001f\\u0085]+/g,' ').trim()"""
    return WS_RE.sub(" ", unicodedata.normalize("NFKC", str(text))).strip(" ")


def prep(text: str) -> str:
    """Lowercase and replace email addresses with a space."""
    return EMAIL_RE.sub(" ", text.lower())


def tokenize(text: str) -> list[str]:
    """prep(), then [a-z0-9]+ tokens of length >= 2, then unigrams + bigrams."""
    toks = [t for t in TOKEN_RE.findall(prep(text)) if len(t) >= 2]
    return toks + [f"{a} {b}" for a, b in zip(toks, toks[1:])]


def has_term(low: str, term: str) -> bool:
    """Term must start at a word start, so 'locked' doesn't match 'blocked'
    and 'log in' doesn't match 'dialog in'. Suffixes are allowed (suspended)."""
    return re.search(r"(?:^|[^a-z0-9])" + re.escape(term), low) is not None


NUMERIC_NAMES = ["log_words", "log_urls", "urgency_terms", "cta_terms", "caps_ratio", "punct_per_100w"]


def numeric_features(text: str) -> list[float]:
    low = prep(text)
    words = len(text.split(" ")) if text else 0
    letters = sum(("a" <= c <= "z") or ("A" <= c <= "Z") for c in text)
    caps = sum("A" <= c <= "Z" for c in text)
    punct = text.count("!") + text.count("?")
    return [
        math.log1p(words),
        math.log1p(len(URL_RE.findall(low))),
        float(sum(has_term(low, t) for t in URGENCY)),
        float(sum(has_term(low, t) for t in CTA)),
        caps / letters if letters else 0.0,
        100.0 * punct / max(words, 1),
    ]


# ---------------------------------------------------------------- model
def select_vocab(texts, max_features, min_df=2):
    """Deterministic vocabulary: keep terms in >= min_df docs, rank by total
    count, break ties alphabetically (sklearn's own tie-break varies by numpy version)."""
    tf, df = Counter(), Counter()
    for t in texts:
        grams = tokenize(t)
        tf.update(grams)
        df.update(set(grams))
    keep = [w for w in tf if df[w] >= min_df]
    keep.sort(key=lambda w: (-tf[w], w))
    return sorted(keep[:max_features])


def build_matrix(vec, texts, mean=None, std=None):
    X_txt = vec.transform(texts)
    num = np.array([numeric_features(t) for t in texts])
    if mean is None:
        mean, std = num.mean(axis=0), num.std(axis=0)
        std[std == 0] = 1.0
    X_num = csr_matrix((num - mean) / std)
    return hstack([X_txt, X_num]).tocsr(), mean, std


def train(texts, y, max_features, C):
    vec = TfidfVectorizer(analyzer=tokenize, vocabulary=select_vocab(texts, max_features),
                          sublinear_tf=True, norm="l2")
    vec.fit(texts)
    X, mean, std = build_matrix(vec, texts)
    clf = LogisticRegression(C=C, max_iter=10000, tol=1e-6).fit(X, y)
    return vec, clf, mean, std


def predict_proba(model, texts):
    vec, clf, mean, std = model
    X, _, _ = build_matrix(vec, texts, mean, std)
    return clf.predict_proba(X)[:, 1]


def pct(x):
    return round(100 * float(x), 1)


def per_group_acc(frame, pred):
    return (pd.Series(pred, index=frame.index) == frame.y).groupby(frame.group).mean()


# ---------------------------------------------------------------- stats
def dashboard_stats(df):
    stop = set(ENGLISH_STOP_WORDS) | {"com", "https", "http", "www", "org", "net", "html"}
    out = {k: {} for k in ["medianWords", "urls", "urlAny", "urgAny", "ctaAny", "caps", "excl"]}
    out["urgency"] = {t: {} for t in URGENCY}
    out["words"] = {}
    for gid, g in df.groupby("group"):
        texts = g["text"].tolist()
        low = [prep(t) for t in texts]
        n = len(texts)
        feats = [numeric_features(t) for t in texts]
        out["medianWords"][gid] = statistics.median(len(t.split(" ")) for t in texts)
        out["urls"][gid] = round(sum(len(URL_RE.findall(t)) for t in low) / n, 2)
        out["urlAny"][gid] = pct(sum(bool(URL_RE.search(t)) for t in low) / n)
        out["urgAny"][gid] = pct(sum(f[2] > 0 for f in feats) / n)
        out["ctaAny"][gid] = pct(sum(f[3] > 0 for f in feats) / n)
        out["caps"][gid] = pct(sum(f[4] for f in feats) / n)
        out["excl"][gid] = round(sum(t.count("!") for t in texts) / n, 2)
        for u in URGENCY:
            out["urgency"][u][gid] = pct(sum(has_term(t, u) for t in low) / n)
        docfreq = Counter(w for t in low for w in set(re.findall(r"[a-z]{3,}", t)) if w not in stop)
        out["words"][gid] = [[w, round(100 * c / n)] for w, c in docfreq.most_common(10)]
    return out


EDGE_CASES = [
    "﻿Verify your account\u0085immediately or it will be suspended!!!",
    "およびamazon.co.jp をご確認ください https://example.com/login",
    "constructor prototype __proto__ toString hasOwnProperty",
    "Your mailbox is BLOCKED. Please LOG IN at www.secure-mail-check.com within 24 hours.",
    "Hi team,\r\n\r\nNotes from today's meeting are attached. Thanks, Sam",
    "",
]


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="dataset", help="folder containing human-generated/ and llm-generated/")
    ap.add_argument("--out", default=".", help="where to write model.js and stats.js")
    ap.add_argument("--max-features", type=int, default=5000)
    ap.add_argument("--C", type=float, default=4.0)
    args = ap.parse_args()
    data_dir, out_dir = Path(args.data), Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    fit = lambda frame: train(frame.text.tolist(), frame.y.values, args.max_features, args.C)

    # ---- load + normalize
    rows = []
    for gid, (_, _, source, label) in GROUPS.items():
        for raw in load_group(data_dir, gid):
            rows.append({"raw": raw, "text": normalize(raw), "y": label, "group": gid, "source": source})
    df = pd.DataFrame(rows)
    raw_counts = df.group.value_counts().to_dict()

    # ---- remove duplicates (human phishing has every email about twice).
    # Without this, identical emails land in both train and test and inflate accuracy.
    assert df.groupby("text").y.nunique().max() == 1, "same text appears with both labels"
    df = df.drop_duplicates("text").reset_index(drop=True)
    counts = df.group.value_counts().to_dict()
    print(f"Loaded {sum(raw_counts.values())} rows -> {len(df)} distinct emails")
    for gid in GROUPS:
        print(f"  {GROUP_NAMES[gid]:15s} {raw_counts[gid]:5d} rows  {counts[gid]:5d} distinct")

    # ---- 5-fold cross-validation (the headline number; less luck than one split)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_overall, cv_groups = [], {g: [] for g in GROUPS}
    for tr_idx, te_idx in skf.split(df, df.group):
        tr_f, te_f = df.iloc[tr_idx], df.iloc[te_idx]
        pred = (predict_proba(fit(tr_f), te_f.text.tolist()) >= 0.5).astype(int)
        cv_overall.append((pred == te_f.y.values).mean())
        for g, a in per_group_acc(te_f, pred).items():
            cv_groups[g].append(a)
    cv = {"overall": {"mean": pct(np.mean(cv_overall)), "sd": pct(np.std(cv_overall))},
          "perGroup": {g: {"mean": pct(np.mean(v)), "sd": pct(np.std(v))} for g, v in cv_groups.items()}}
    print(f"\n5-fold CV accuracy: {cv['overall']['mean']}% +/- {cv['overall']['sd']}")
    for g in GROUPS:
        print(f"  {GROUP_NAMES[g]:15s} {cv['perGroup'][g]['mean']}% +/- {cv['perGroup'][g]['sd']}")

    # ---- exported model: stratified 80/20 split
    tr, te = train_test_split(df, test_size=0.2, stratify=df.group, random_state=SEED)
    model = fit(tr)
    vec, clf, mean, std = model
    te = te.assign(p=predict_proba(model, te.text.tolist()))
    te["pred"] = (te.p >= 0.5).astype(int)
    overall = (te.pred == te.y).mean()
    per_group = per_group_acc(te, te.pred.values)
    print(f"\nExported model, held-out test: {overall:.1%} (n={len(te)})")
    for g in GROUPS:
        print(f"  {GROUP_NAMES[g]:15s} {per_group[g]:.1%}  (n={(te.group == g).sum()})")

    # ---- generalization: train on one source, test on the other.
    cross = {}
    print("\nCross-source (does it learn phishing, or just the source's style?)")
    for a_src, b_src in [("human", "llm"), ("llm", "human")]:
        a, b = df[df.source == a_src], df[df.source == b_src]
        pred = (predict_proba(fit(a), b.text.tolist()) >= 0.5).astype(int)
        y = b.y.values
        rec_p, rec_l = pred[y == 1].mean(), 1 - pred[y == 0].mean()
        r = {"accuracy": pct((pred == y).mean()),
             "balancedAccuracy": pct((rec_p + rec_l) / 2),  # 50% = chance, even if classes are uneven
             "phishingRecall": pct(rec_p),
             "legitRecall": pct(rec_l),
             "predictedPhishing": pct(pred.mean())}
        cross[f"{a_src}_to_{b_src}"] = r
        print(f"  train {a_src:5s} -> test {b_src:5s}: {r['balancedAccuracy']}% balanced accuracy | "
              f"catches {r['phishingRecall']}% of phishing, {r['legitRecall']}% of legit | "
              f"calls {r['predictedPhishing']}% phishing")

    # ---- terms the model leans on (check these for dataset artifacts before presenting)
    vocab = vec.get_feature_names_out()
    coef_txt = clf.coef_[0][: len(vocab)]
    order = np.argsort(coef_txt, kind="stable")
    top_phish = [[vocab[i], round(float(coef_txt[i]), 3)] for i in order[::-1][:15]]
    top_legit = [[vocab[i], round(float(coef_txt[i]), 3)] for i in order[:15]]
    print("\nStrongest phishing terms:", ", ".join(w for w, _ in top_phish[:10]))
    print("Strongest legit terms:   ", ", ".join(w for w, _ in top_legit[:10]))

    # ---- parity tests: RAW text in, so JS normalization is tested too
    samples = pd.concat([te[te.group == g].head(2) for g in GROUPS])
    test_texts = samples.raw.tolist() + EDGE_CASES
    test_p = predict_proba(model, [normalize(t) for t in test_texts])
    tests = [{"text": t, "p": round(float(p), 6)} for t, p in zip(test_texts, test_p)]

    # ---- export model.js
    out_model = {
        "meta": {"trainedOn": len(tr), "testedOn": len(te), "seed": SEED, "C": args.C,
                 "tokenizer": "normalize, lowercase, strip emails, [a-z0-9]+ len>=2, unigrams+bigrams",
                 "tfidf": "sublinear tf (1+ln count) * idf, then L2 norm over vocab terms"},
        "vocab": vocab.tolist(),
        "idf": [round(float(x), 6) for x in vec.idf_],
        "coef": [round(float(x), 6) for x in coef_txt],
        "numeric": {"names": NUMERIC_NAMES,
                    "mean": [round(float(x), 6) for x in mean],
                    "std": [round(float(x), 6) for x in std],
                    "coef": [round(float(x), 6) for x in clf.coef_[0][len(vocab):]]},
        "intercept": round(float(clf.intercept_[0]), 6),
        "urgency": URGENCY,
        "cta": CTA,
        "tests": tests,
    }
    (out_dir / "model.js").write_text(
        "const MODEL = " + json.dumps(out_model, separators=(",", ":")) + ";\n", encoding="utf-8")

    # ---- export stats.js (computed on the distinct emails)
    stats = dashboard_stats(df)
    stats["counts"] = {"rows": raw_counts, "distinct": counts}
    stats["accuracy"] = {
        "cv": cv,
        "heldOut": {"overall": pct(overall), "perGroup": {g: pct(per_group[g]) for g in GROUPS},
                    "testSize": len(te)},
        "crossSource": cross,
    }
    stats["topTerms"] = {"phishing": top_phish, "legit": top_legit}
    (out_dir / "stats.js").write_text(
        "const STATS = " + json.dumps(stats, indent=1, ensure_ascii=True) + ";\n", encoding="utf-8")

    kb = (out_dir / "model.js").stat().st_size / 1024
    print(f"\nWrote {out_dir / 'model.js'} ({kb:.0f} KB) and {out_dir / 'stats.js'}")


if __name__ == "__main__":
    main()