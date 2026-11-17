"""Compact grammar-point definitions for N4–N1.

Each point is a regex over the sentence text. The blank is the match (or the named group `b`),
which must line up with token boundaries so a pattern can't match inside another word.
Options decide what else goes into the blank and what must come before it:

    pre="v"   include the preceding verb (with its auxiliaries) in the blank; hint = dictionary form
    pre="va"  same, but the head may also be an い/な-adjective
    after="n" / "v" / "va" / "any"
              require that kind of word right before the blank (not included)
    tail=True extend the blank over trailing ます/た/ない/です (for patterns ending in a verb/adjective)
    neg=regex reject sentences matching this regex
    req=regex the sentence must also match this (e.g. a negative later in the sentence)
    check=f    f(toks, i, k) -> bool on the matched tokens [i, k) (before `pre` extension)
    en=regex   the English translation must match (e.g. "can" for potential vs passive)
"""
from __future__ import annotations

import re

from jp import Tok

POINTS: list[dict] = []

AUX_TAIL = ("ます", "た", "ず", "ない", "です", "たい")


def _is_content_head(t: Tok, kinds: str) -> bool:
    if "v" in kinds and t.p1 == "動詞":
        return True
    if "a" in kinds and (t.p1 == "形容詞" or t.p1 == "形状詞"):
        return True
    return False


def head_index(toks: list[Tok], i: int, kinds: str) -> int | None:
    """Index of the verb/adjective that the conjugated chain ending right before token i starts with."""
    j = i - 1
    while j >= 0:
        t = toks[j]
        if t.p1 == "助動詞" or (t.p1 == "助詞" and t.lemma in ("て", "ば")) or t.p1 == "接尾辞" and t.p2 == "動詞的":
            j -= 1
            continue
        if t.p1 == "動詞" and t.p2 == "非自立可能" and j > 0 and toks[j - 1].p1 == "助詞" and toks[j - 1].lemma == "て":
            j -= 2  # 〜ている / 〜てしまう etc.
            continue
        if t.p1 == "動詞" and t.p2 == "非自立可能" and j > 0 and toks[j - 1].p1 == "動詞":
            j -= 1  # compound verbs: 食べ始める
            continue
        return j if _is_content_head(t, kinds) else None
    return None


def _prev_kind(toks: list[Tok], i: int) -> str:
    if i == 0:
        return ""
    p = toks[i - 1]
    if p.p1 in ("名詞", "代名詞") or p.p1 == "接尾辞" and p.p2.startswith("名詞"):
        return "n"
    if p.p1 in ("動詞", "助動詞"):
        return "v"
    if p.p1 in ("形容詞", "形状詞"):
        return "a"
    return p.p1


def _tail(toks: list[Tok], j: int) -> int:
    while j < len(toks) and toks[j].p1 == "助動詞" and toks[j].lemma in AUX_TAIL:
        j += 1
    return j


def make_matcher(pat: str, pre: str | None, after: str | None, tail: bool, neg: str | None,
                 req: str | None = None, check=None):
    rx = re.compile(pat)
    nrx = re.compile(neg) if neg else None
    qrx = re.compile(req) if req else None

    def match(toks: list[Tok]):
        if not toks:
            return []
        text = "".join(t.s for t in toks)
        if nrx and nrx.search(text):
            return []
        if qrx and not qrx.search(text):
            return []
        starts = {t.start: k for k, t in enumerate(toks)}
        ends = {t.end: k for k, t in enumerate(toks)}
        out = []
        for m in rx.finditer(text):
            g = "b" if "b" in rx.groupindex else 0
            a, b = m.span(g)
            if a == b or a not in starts or b not in ends:
                continue  # must align with whole tokens
            i, k = starts[a], ends[b] + 1
            if check is not None and not check(toks, i, k):
                continue
            if tail:
                k = _tail(toks, k)
            hint = None
            if pre:
                optional = pre.endswith("?")
                h = head_index(toks, i, pre.rstrip("?"))
                if h is None and not optional:
                    continue
                if h is not None:
                    i, hint = h, h
            if after:
                kind = _prev_kind(toks, i)
                if after != "any" and (not kind or kind not in after):
                    continue
                if after == "any" and i == 0:
                    continue
            out.append((i, k, hint))
        return out

    return match


def point(level: str, pid: str, title: str, meaning: str, structure: str, explanation: str, pat: str,
          ex: str, *, pre: str | None = None, after: str | None = None, tail: bool = False,
          neg: str | None = None, req: str | None = None, check=None, en: str | None = None,
          custom=None):
    """`custom(toks) -> [(i, k, hint)]` replaces the regex matcher for points a pattern can't express."""
    POINTS.append(dict(
        id=pid, level=level, title=title, meaning=meaning, structure=structure,
        explanation=explanation.strip(), ex=ex, en=en,
        match=custom or make_matcher(pat, pre, after, tail, neg, req, check),
    ))


# ---- reusable token checks -------------------------------------------------

def first_lemma(*lemmas):
    return lambda toks, i, k: toks[i].lemma in lemmas


def first_pos(p1, p2=None):
    return lambda toks, i, k: toks[i].p1 == p1 and (p2 is None or toks[i].p2.startswith(p2))


def last_pos(p1, p2=None):
    return lambda toks, i, k: toks[k - 1].p1 == p1 and (p2 is None or toks[k - 1].p2.startswith(p2))


def prev_is(*surfaces):
    return lambda toks, i, k: i > 0 and toks[i - 1].s in surfaces


def prev_not(*surfaces):
    return lambda toks, i, k: i == 0 or toks[i - 1].s not in surfaces


def prev_cf(prefix):
    """The word right before the blank has a conjugation form starting with `prefix` (e.g. 終止形, 連用形)."""
    return lambda toks, i, k: i > 0 and toks[i - 1].cf.startswith(prefix)


def all_of(*fs):
    return lambda toks, i, k: all(f(toks, i, k) for f in fs)


# verb ending classes (token-aligned stems), used in patterns
NARU = "な(?:る|り|っ|ら|れ|ろ)"
SURU = "(?:する|し|さ|すれ|しろ|せよ)"
ARU = "(?:ある|あり|あっ|あれ|あろ)"
IKU = "(?:いく|いき|いっ|いか|いけ|いこ|行く|行き|行っ|行か|行け|行こ)"
KURU = "(?:くる|き|こ|くれ|来る|来|来れ)"
