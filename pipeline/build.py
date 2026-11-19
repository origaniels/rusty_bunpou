"""Build content.json for the app from Tatoeba + grammar matchers (JLPT N5–N1).

Usage: .venv/bin/python build.py [--per-point 15] [--levels N5,N4,...]
"""
from __future__ import annotations

import argparse
import collections
import json
import pickle
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import zlib  # noqa: E402

import fr as french  # noqa: E402
from alternatives import NUANCE, alternatives  # noqa: E402
from extra_examples import EXTRA  # noqa: E402
from jp import KANJI_RE, furigana, has_kanji, tokenize  # noqa: E402

RAW = HERE.parent / "data" / "raw"
OUT = HERE.parent / "data" / "build"
CACHE = OUT / "tokens.pkl"

BAD_CHARS = re.compile(r"[A-Za-zＡ-Ｚａ-ｚ（）()\[\]《》“”\"/:;…・]")
QUOTES = re.compile(r"[「」『』]")
QUOTES_FROM = "N3"  # quoted sentences are allowed from this level up
CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞", "連体詞"}
MAX_LEN = 60
LEVELS = ["N5", "N4", "N3", "N2", "N1"]

# Sentence filters per level: (max lemma rank, rank above which a word counts as "hard",
#  max kanji rank, kanji rank counted as hard, ideal max length, absolute max length).
# Higher levels allow rarer words and longer sentences; N5 keeps the original strict filter.
FILTERS = {
    "N5": (3500, 1200, 650, 350, 22, 40),
    "N4": (6000, 2000, 1000, 600, 26, 45),
    "N3": (10000, 3500, 1500, 900, 30, 50),
    "N2": (20000, 6000, 2200, 1400, 34, 55),
    "N1": (10 ** 9, 10000, 10 ** 9, 2000, 38, 60),
}
FR_BONUS = 1.5  # quality bonus for sentences with a Tatoeba French translation (bilingual content)
MIN_SENTENCES = 3  # points with fewer sentences (Tatoeba + extra_examples.py) are left out (and reported)


def all_points():
    import grammar_n5
    import patterns
    for mod in ("grammar_n4", "grammar_n3", "grammar_n2", "grammar_n1"):
        try:
            __import__(mod)  # registers its points in patterns.POINTS
        except ModuleNotFoundError:
            continue
    return list(grammar_n5.POINTS) + list(patterns.POINTS)


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
        # Japanese doesn't use spaces; the tokenizer drops them, which would desync furigana and text
        text = re.sub(r"[ 　]+", "", text)
        if not (5 <= len(text) <= MAX_LEN) or BAD_CHARS.search(text):
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
    fra = load_french(jpn)
    out = {}
    for sid, (text, owner, nat) in jpn.items():
        ens = sorted((e for e in links.get(sid, []) if e in eng and len(eng[e]) <= 140))
        if not ens:
            continue
        out[sid] = dict(ja=text, owner=owner, native=nat, en=eng[ens[0]])
        if sid in fra:
            out[sid]["fr"], out[sid]["fr_id"], out[sid]["fr_owner"] = fra[sid]
    return out


def load_french(jpn):
    """Tatoeba French translation of each Japanese sentence: (text, French sentence id, its contributor).
    The lowest-numbered (oldest) short translation is used, like for English."""
    links = collections.defaultdict(list)
    for line in open(RAW / "jpn-fra_links.tsv", encoding="utf8"):
        a, b = map(int, line.split()[:2])
        if a in jpn:
            links[a].append(b)
    need = {b for v in links.values() for b in v}
    fra = {}
    for line in open(RAW / "fra_sentences_detailed.tsv", encoding="utf8"):
        p = line.rstrip("\n").split("\t")
        sid = int(p[0])
        if sid in need and len(p[2]) <= 140:
            fra[sid] = (p[2], p[3] if p[3] != "\\N" else "")
    out = {}
    for sid, fs in links.items():
        fs = sorted(f for f in fs if f in fra)
        if fs:
            text, owner = fra[fs[0]]
            out[sid] = (text, fs[0], owner)
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


def answer_parts(span):
    """The answer's tokens in kana, each marked p (particle), v (conjugating: verb, adjective,
    auxiliary, て/ば) or o (other). The app uses it to tell a missing or wrong particle, or the
    right word in the wrong form, from a plain wrong answer."""
    out = []
    for t in span:
        if t.p1 == "助詞" and t.p2 in ("格助詞", "係助詞", "副助詞") and t.lemma not in ("たり", "だり"):
            kind = "p"
        elif t.p1 in ("動詞", "形容詞", "助動詞") or (t.p1 == "助詞" and t.p2 == "接続助詞"):
            kind = "v"
        else:
            kind = "o"
        out.append([t.kana, kind])
    return out


def answers_for(span):
    surf = "".join(t.s for t in span)
    reading = "".join(t.kana for t in span)
    ans = [surf, reading]
    extra = []
    for a in ans:
        extra += [a.replace("ください", "下さい"), a.replace("下さい", "ください")]
        for good in ("良い", "よい"):
            if good in a:
                extra.append(a.replace(good, "いい"))
        if a.startswith("じゃ"):
            extra.append("では" + a[2:])
        if a.startswith("では"):
            extra.append("じゃ" + a[2:])
    seen, out = set(), []
    for a in ans + extra:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


class Scorer:
    """Corpus-frequency based difficulty filter, parameterised by JLPT level."""

    def __init__(self, cands, toks):
        lf, kf = collections.Counter(), collections.Counter()
        for sid, ts in toks.items():
            for t in ts:
                if t.p1 in CONTENT_POS:
                    lf[t.lemma] += 1
            for ch in KANJI_RE.findall(cands[sid]["ja"]):
                kf[ch] += 1
        self.lrank = {w: i for i, (w, _) in enumerate(lf.most_common())}
        self.krank = {k: i for i, (k, _) in enumerate(kf.most_common())}
        self.cands, self.toks = cands, toks
        self.cache = {}

    def quality(self, sid, level):
        key = (sid, level)
        if key in self.cache:
            return self.cache[key]
        max_rank, hard_rank, max_k, hard_k, ideal_len, max_len = FILTERS[level]
        c, ts = self.cands[sid], self.toks[sid]
        q = None
        n = len(c["ja"])
        if QUOTES.search(c["ja"]) and LEVELS.index(level) < LEVELS.index(QUOTES_FROM):
            n = 10 ** 6  # reject
        if n <= max_len:
            hard = proper = kp = 0
            ok = True
            for t in ts:
                if t.p1 not in CONTENT_POS:
                    continue
                if t.p2 == "固有名詞":
                    proper += 1
                    continue
                if t.p2 == "数詞":
                    continue
                r = self.lrank.get(t.lemma, 10 ** 6)
                if r > max_rank:
                    ok = False
                    break
                if r > hard_rank:
                    hard += 1
            if ok:
                for ch in KANJI_RE.findall(c["ja"]):
                    r = self.krank.get(ch, 10 ** 6)
                    if r > max_k:
                        ok = False
                        break
                    if r > hard_k:
                        kp += 1
            if ok:
                len_pen = max(0, 9 - n) + max(0, n - ideal_len)
                q = (2.0 if c["native"] else 0.0) + (FR_BONUS if "fr" in c else 0.0) - 1.5 * hard - 1.0 * kp - 0.25 * len_pen - 0.8 * proper
        self.cache[key] = q
        return q


def select(p, cands, toks, scorer, used_global, per_point):
    level = p["level"]
    en_rx = re.compile(p["en"], re.I) if p.get("en") else None
    matches = {}
    for sid, ts in toks.items():
        m = p["match"](ts)
        if len(m) != 1:
            continue
        if en_rx and not en_rx.search(cands[sid]["en"]):
            continue
        matches[sid] = m[0]
    # strict filter for the level first; fall back to the next levels' filters if too few
    chosen = []
    tiers = LEVELS[LEVELS.index(level):]
    for tier in tiers:
        pool = []
        for sid, mt in matches.items():
            q = scorer.quality(sid, tier)
            if q is not None:
                pool.append((q, sid, mt))
        pool.sort(key=lambda x: (-x[0], x[1]))
        hint_use = collections.Counter()
        for c in chosen:
            hint_use[c[4]] += 1
        for q, sid, (a, b, h) in pool:
            if len(chosen) >= per_point:
                break
            if any(c[0] == sid for c in chosen):
                continue
            ts = toks[sid]
            hl = ts[h].lemma if h is not None else "".join(t.s for t in ts[a:b])
            if hint_use[hl] >= (2 if h is not None else 99):
                continue
            ja = cands[sid]["ja"]
            if any(jaccard_bigrams(ja, cands[c[0]]["ja"]) > 0.5 for c in chosen):
                continue
            if used_global[sid] >= 2:
                continue
            hint_use[hl] += 1
            chosen.append((sid, a, b, h, hl))
        if len(chosen) >= 8:
            break
    return chosen, len(matches)


def extra_sentences(p, need, report_bad):
    """Original sentences from extra_examples.py for thin points (validated by the same matcher)."""
    out = []
    for ja, en in EXTRA.get(p["id"], []):
        if len(out) >= need:
            break
        ts = tokenize(ja)
        m = p["match"](ts)
        if len(m) != 1:
            report_bad.append((p["id"], ja, len(m)))
            continue
        a, b, h = m[0]
        sid = 900_000_000 + zlib.crc32(ja.encode()) % 99_999_999
        out.append((sid, a, b, h, ja, en, ts))
    return out


# word classes worth a dictionary lookup, and grammatical words that are not
WORD_POS = {"名詞", "代名詞", "動詞", "形容詞", "形状詞", "副詞"}
# one-kanji nouns UniDic splits off compounds: 日本 + 語, 日本 + 人
NOUN_TAILS = {"語", "人", "者", "製"}
NOT_WORDS = {
    "こと", "事", "もの", "物", "の", "よう", "様", "ところ", "所", "ため", "為", "わけ", "訳", "はず", "筈",
    "する", "為る", "いる", "居る", "ある", "有る", "在る", "なる", "成る", "くる", "来る", "いく", "おる", "居る",
    "れる", "られる", "せる", "させる", "ない", "無い", "そう", "みたい", "らしい", "ほう", "方", "まま", "ん",
    "すぎる", "過ぎる",
}


def dictionary_words(ts):
    """Dictionary forms of the sentence's content words, in order, without repeats.
    お/ご + noun and noun + suffix (日本 + 語) stay one word; verbs right after て/で are
    auxiliaries (〜てもらう, 〜ている), i.e. grammar, not words to look up."""
    out = []
    for i, t in enumerate(ts):
        if t.p1 not in WORD_POS or t.p2 == "数詞":
            continue
        prev = ts[i - 1] if i > 0 else None
        if t.p1 == "動詞" and t.p2 == "非自立可能" and prev and prev.p2 == "接続助詞" and prev.s in ("て", "で"):
            continue
        if t.p1 == "名詞" and t.s in NOUN_TAILS and prev and prev.p1 == "名詞":
            continue  # already attached to the noun before
        base = t.base
        if base.endswith("ずる") and t.s.endswith("じ"):  # 信ずる → 信じる (as for hints)
            base = base[:-2] + "じる"
        if t.p1 in ("名詞", "代名詞"):
            if prev and prev.p1 == "接頭辞" and prev.s in ("お", "ご", "御"):
                base = prev.s + t.s
            j = i + 1
            while j < len(ts) and ((ts[j].p1 == "接尾辞" and ts[j].p2.startswith("名詞"))
                                   or (ts[j].p1 == "名詞" and ts[j].s in NOUN_TAILS)):
                base += ts[j].s
                j += 1
        if base in NOT_WORDS or (not has_kanji(base) and len(base) < 2) or base in out:
            continue
        out.append(base)
    return out


def to_sentence(sid, a, b, h, cands, toks):
    ts = toks[sid]
    span = ts[a:b]
    hint = None
    if h is not None:
        ht = ts[h]
        base, base_kana = ht.base, ht.base_kana
        # UniDic gives classical dictionary forms for some verbs (信じる → 信ずる)
        if base.endswith("ずる") and ht.s.endswith("じ"):
            base, base_kana = base[:-2] + "じる", base_kana[:-2] + "じる"
        hint = base
        if has_kanji(base):
            hint += f"（{base_kana}）"
        tags = span_tags(span)
        if tags:
            hint += " · " + ", ".join(tags)
    c = cands[sid]
    d = dict(
        id=sid, ja=c["ja"], en=c["en"], owner=c["owner"],
        furi=furigana(ts), cloze=[span[0].start, span[-1].end],
        answers=answers_for(span), hint=hint, words=dictionary_words(ts),
    )
    if len(span) > 1:
        d["parts"] = answer_parts(span)
    if c.get("src"):
        d["src"] = c["src"]
    if c.get("fr"):
        d["fr"], d["fr_id"], d["fr_owner"] = c["fr"], c["fr_id"], c["fr_owner"]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-point", type=int, default=15)
    ap.add_argument("--levels", default=",".join(LEVELS))
    ap.add_argument("--show", default="", help="comma separated point ids: print their sentences")
    ap.add_argument("--thin", action="store_true", help="list points with fewer than 5 sentences")
    ap.add_argument("--missing-fr", default="", help="write sentences still needing a French translation "
                    "(id, Japanese, English, point) to this TSV file")
    args = ap.parse_args()
    levels = args.levels.split(",")

    print("loading tatoeba…", flush=True)
    cands = load_candidates()
    print(f"  {len(cands)} candidate sentences with English", flush=True)
    toks = get_tokens(cands)
    print("  tokenized", flush=True)
    scorer = Scorer(cands, toks)

    points = [p for p in all_points() if p["level"] in levels]
    fr_points, fr_sents = french.point_texts(), french.sentence_translations()
    missing_fr, stale_fr, used_fr = [], [], set()
    used_global = collections.Counter()
    points_out, report, dropped, thin, bad_extra = [], [], [], [], []
    order = 0
    for p in points:
        chosen, pool = select(p, cands, toks, scorer, used_global, args.per_point)
        extras = extra_sentences(p, args.per_point - len(chosen), bad_extra) if len(chosen) < 8 else []
        for sid, a, b, h, ja, en, ts in extras:
            cands[sid] = dict(ja=ja, en=en, owner="", native=True, src="app")
            toks[sid] = ts
            chosen.append((sid, a, b, h, None))
        if len(chosen) < MIN_SENTENCES:
            dropped.append((p["level"], p["id"], len(chosen)))
            continue
        for c in chosen:
            used_global[c[0]] += 1
        sents = [to_sentence(sid, a, b, h, cands, toks) for sid, a, b, h, _ in chosen]
        for (sid, a, b, _, _), sent in zip(chosen, sents):
            kana = next((x for x in sent["answers"] if not has_kanji(x)), None)
            if kana and p["id"] in NUANCE:
                alts = alternatives(p["id"], kana, toks[sid], a, b, set(sent["answers"]))
                if alts:
                    sent["alts"] = alts
        for s in sents:
            if "fr" in s:
                continue
            tr = fr_sents.get(s["id"])
            if tr and tr[0] == s["ja"]:
                s["fr"], s["fr_src"] = tr[1], "app"
                used_fr.add(s["id"])
            else:
                if tr:
                    stale_fr.append(s["id"])
                missing_fr.append((p["level"], s["id"], s["ja"], s["en"], p["id"]))
        report.append((p["level"], p["id"], pool, len(sents)))
        if len(sents) < 5:
            thin.append((p["level"], p["id"], len(sents)))
        po = dict(
            id=p["id"], level=p["level"], order=order, title=p["title"], meaning=p["meaning"],
            structure=p["structure"], explanation=" ".join(p["explanation"].split()), sentences=sents,
        )
        if p["id"] in NUANCE:
            po["nuance"] = list(NUANCE[p["id"]])
        if p["id"] in fr_points:
            f = fr_points[p["id"]]
            po["fr"] = dict(title=f.get("title", p["title"]), meaning=f["meaning"], structure=f["structure"],
                            explanation=f["explanation"])
        points_out.append(po)
        order += 1
        if p["id"] in args.show.split(","):
            print(f"== {p['id']} {p['title']}")
            for s in sents:
                a, b = s["cloze"]
                print("  ", s["ja"][:a] + "[" + s["ja"][a:b] + "]" + s["ja"][b:], "|", s["en"], "|", s["hint"])

    OUT.mkdir(parents=True, exist_ok=True)
    content = dict(version=3, source="Tatoeba (https://tatoeba.org), CC-BY 2.0 FR; some examples written for this app",
                   source_fr="Tatoeba (https://tatoeba.org), CC-BY 2.0 FR ; quelques exemples et traductions écrits pour cette appli",
                   points=points_out)
    (OUT / "content.json").write_text(json.dumps(content, ensure_ascii=False, separators=(",", ":")), encoding="utf8")

    print(f"\n{'level':6} {'points':>7} {'dropped':>8} {'sentences':>10} {'avg/pt':>7} {'median':>7} {'<8':>4}")
    for lv in levels:
        ns = [n for l, _, _, n in report if l == lv]
        if not ns:
            continue
        d = sum(1 for x in dropped if x[0] == lv)
        print(f"{lv:6} {len(ns):7} {d:8} {sum(ns):10} {sum(ns) / len(ns):7.1f} {statistics.median(ns):7} "
              f"{sum(1 for n in ns if n < 8):4}")
    ns = [n for *_, n in report]
    print(f"{'total':6} {len(ns):7} {len(dropped):8} {sum(ns):10} {sum(ns) / len(ns):7.1f} {statistics.median(ns):7} "
          f"{sum(1 for n in ns if n < 8):4}")
    if dropped:
        print("\ndropped (fewer than", MIN_SENTENCES, "usable sentences):", " ".join(f"{l}:{i}({n})" for l, i, n in dropped))
    if bad_extra:
        print("\nextra examples without exactly one match (skipped):")
        for pid, ja, n in bad_extra:
            print(f"  {pid}: {ja} ({n} matches)")
    no_fr = [p["id"] for p in points_out if "fr" not in p]
    unknown = sorted(set(fr_points) - {p["id"] for p in points_out})
    if unknown:
        print("  French texts for unknown point ids:", unknown)
    for lv in levels:
        miss = [p["id"] for p in points_out if p["level"] == lv and "fr" not in p]
        if miss and len(miss) < 20:
            print(f"  {lv} points without French text:", " ".join(miss))
    print(f"\nFrench: {len(points_out) - len(no_fr)}/{len(points_out)} points with French text, "
          f"{len(missing_fr)} sentences without a French translation, {len(used_fr)} translated for this app")
    if stale_fr:
        print("  translations whose Japanese no longer matches (re-check):", stale_fr)
    unused = sorted(set(fr_sents) - used_fr - set(stale_fr))
    if unused:
        print(f"  {len(unused)} translations not used by any selected sentence:", unused[:20])
    if args.missing_fr:
        with open(args.missing_fr, "w", encoding="utf8") as f:
            for row in missing_fr:
                f.write("\t".join(str(x) for x in row) + "\n")
    if args.thin:
        for l, i, n in dropped:
            thin.append((l, i, n))
        print("\nthin (<5):", " ".join(f"{l}:{i}({n})" for l, i, n in sorted(thin)))
    print("wrote", OUT / "content.json", f"({(OUT / 'content.json').stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
