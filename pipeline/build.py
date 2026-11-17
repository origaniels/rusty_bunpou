"""Build content.json for the app from Tatoeba + grammar matchers.

Usage: .venv/bin/python build.py [--per-point 15]
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pickle
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from jp import KANJI_RE, furigana, has_kanji, kata2hira, tokenize  # noqa: E402
from grammar_n5 import POINTS  # noqa: E402

RAW = HERE.parent / "data" / "raw"
OUT = HERE.parent / "data" / "build"
CACHE = OUT / "tokens.pkl"

BAD_CHARS = re.compile(r"[A-Za-zＡ-Ｚａ-ｚ「」『』（）()\[\]《》“”\"/:;…・]")
CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞", "連体詞"}


def load_candidates():
    native = set()
    for line in open(RAW / "user_languages.csv", encoding="utf8"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3 and p[0] == "jpn" and p[1] == "5":
            native.add(p[2])

    jpn = {}
    for line in open(RAW / "jpn_sentences_detailed.tsv", encoding="utf8"):
        p = line.rstrip("\n").split("\t")
        sid, text, owner = int(p[0]), p[2], p[3]
        if not (5 <= len(text) <= 40) or BAD_CHARS.search(text):
            continue
        if text[-1] not in "。？！?!":
            continue
        jpn[sid] = (text, owner if owner != "\\N" else "", owner in native)

    links = collections.defaultdict(list)
    for line in open(RAW / "jpn-eng_links.tsv", encoding="utf8"):
        a, b = line.split()
        a, b = int(a), int(b)
        if a in jpn:
            links[a].append(b)
    need = {b for v in links.values() for b in v}
    eng = {}
    for line in open(RAW / "eng_sentences.tsv", encoding="utf8"):
        p = line.rstrip("\n").split("\t")
        sid = int(p[0])
        if sid in need:
            eng[sid] = p[2]
    out = {}
    for sid, (text, owner, nat) in jpn.items():
        ens = sorted((e for e in links.get(sid, []) if e in eng and len(eng[e]) <= 110))
        if not ens:
            continue
        out[sid] = dict(ja=text, owner=owner, native=nat, en=eng[ens[0]])
    return out


def get_tokens(cands):
    if CACHE.exists():
        cached = pickle.load(open(CACHE, "rb"))
        if set(cached) >= set(cands):
            return cached
    toks = {sid: tokenize(c["ja"]) for sid, c in cands.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    pickle.dump(toks, open(CACHE, "wb"))
    return toks


def jaccard_bigrams(a, b):
    A = {a[i:i + 2] for i in range(len(a) - 1)}
    B = {b[i:i + 2] for i in range(len(b) - 1)}
    return len(A & B) / max(1, len(A | B))


def span_tags(span):
    tags = []
    lem = [t.lemma for t in span]
    if "ます" in lem or "です" in lem:
        tags.append("polite")
    if "た" in lem:
        tags.append("past")
    if any(t.lemma in ("ない", "ず") or (t.lemma == "無い" and t.p2 == "非自立可能") for t in span):
        tags.append("negative")
    return tags


def answers_for(span):
    surf = "".join(t.s for t in span)
    reading = "".join(t.kana for t in span)
    ans = [surf, reading]
    extra = []
    for a in ans:
        extra += [a.replace("ください", "下さい"), a.replace("下さい", "ください")]
        if a.startswith("じゃ"):
            extra.append("では" + a[2:])
        for good in ("良い", "よい"):
            if good in a:
                extra.append(a.replace(good, "いい"))
        if a.startswith("では"):
            extra.append("じゃ" + a[2:])
    seen, out = set(), []
    for a in ans + extra:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-point", type=int, default=15)
    args = ap.parse_args()

    print("loading tatoeba…", flush=True)
    cands = load_candidates()
    print(f"  {len(cands)} candidate sentences with English", flush=True)
    toks = get_tokens(cands)
    print("  tokenized", flush=True)

    # corpus-derived frequency ranks (proxy for "beginner" vocabulary/kanji)
    lf, kf = collections.Counter(), collections.Counter()
    for sid, ts in toks.items():
        for t in ts:
            if t.p1 in CONTENT_POS:
                lf[t.lemma] += 1
        for ch in KANJI_RE.findall(cands[sid]["ja"]):
            kf[ch] += 1
    lrank = {w: i for i, (w, _) in enumerate(lf.most_common())}
    krank = {k: i for i, (k, _) in enumerate(kf.most_common())}

    def quality(sid):
        c, ts = cands[sid], toks[sid]
        hard = 0
        proper = 0
        for t in ts:
            if t.p1 not in CONTENT_POS:
                continue
            if t.p2 == "固有名詞":
                proper += 1
                continue
            if t.p2 == "数詞":
                continue
            r = lrank.get(t.lemma, 10 ** 6)
            if r > 3500:
                return None
            if r > 1200:
                hard += 1
        kp = 0
        for ch in KANJI_RE.findall(c["ja"]):
            r = krank.get(ch, 10 ** 6)
            if r > 650:
                return None
            if r > 350:
                kp += 1
        n = len(c["ja"])
        len_pen = max(0, 9 - n) + max(0, n - 22)
        return (2.0 if c["native"] else 0.0) - 1.5 * hard - 1.0 * kp - 0.25 * len_pen - 0.8 * proper

    qual = {}
    for sid in cands:
        q = quality(sid)
        if q is not None:
            qual[sid] = q
    print(f"  {len(qual)} sentences pass the beginner filter", flush=True)

    used_global = collections.Counter()
    points_out = []
    report = []
    for order, p in enumerate(POINTS):
        pool = []
        for sid in qual:
            m = p["match"](toks[sid])
            if len(m) != 1:
                continue
            pool.append((qual[sid], sid, m[0]))
        pool.sort(key=lambda x: (-x[0], x[1]))
        chosen = []
        hint_use = collections.Counter()
        for q, sid, (a, b, h) in pool:
            if len(chosen) >= args.per_point:
                break
            ts = toks[sid]
            hl = ts[h].lemma if h is not None else "".join(t.s for t in ts[a:b])
            limit = 2 if h is not None else 99
            if hint_use[hl] >= limit:
                continue
            ja = cands[sid]["ja"]
            if any(jaccard_bigrams(ja, cands[c]["ja"]) > 0.5 for c, *_ in chosen):
                continue
            # spread sentences across points a bit
            if used_global[sid] >= 2:
                continue
            hint_use[hl] += 1
            chosen.append((sid, a, b, h))
        sents = []
        for sid, a, b, h in chosen:
            used_global[sid] += 1
            ts = toks[sid]
            span = ts[a:b]
            hint = None
            if h is not None:
                ht = ts[h]
                hint = ht.base
                if has_kanji(ht.base):
                    hint += f"（{ht.base_kana}）"
                tags = span_tags(span)
                if tags:
                    hint += " · " + ", ".join(tags)
            c = cands[sid]
            sents.append(dict(
                id=sid, ja=c["ja"], en=c["en"], owner=c["owner"],
                furi=furigana(ts), cloze=[span[0].start, span[-1].end],
                answers=answers_for(span), hint=hint,
            ))
        report.append((p["id"], len(pool), len(sents)))
        points_out.append(dict(
            id=p["id"], level=p["level"], order=order, title=p["title"], meaning=p["meaning"],
            structure=p["structure"], explanation=p["explanation"], sentences=sents,
        ))

    OUT.mkdir(parents=True, exist_ok=True)
    content = dict(version=1, source="Tatoeba (https://tatoeba.org), CC-BY 2.0 FR", points=points_out)
    (OUT / "content.json").write_text(json.dumps(content, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    for pid, pool, n in report:
        flag = "  <-- low" if n < 8 else ""
        print(f"{pid:16s} pool={pool:6d} chosen={n:3d}{flag}")
    print("wrote", OUT / "content.json")


if __name__ == "__main__":
    main()
