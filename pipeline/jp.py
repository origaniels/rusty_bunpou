"""Tokenization helpers built on fugashi + unidic-lite."""
from __future__ import annotations

import re
from dataclasses import dataclass

import fugashi

_tagger = fugashi.Tagger()

# Readings that unidic-lite gets "technically right" but are not what a learner expects.
READING_OVERRIDES = {
    ("私", "ワタクシ"): "ワタシ",
    ("日本", "ニッポン"): "ニホン",
    ("明日", "アス"): "アシタ",
    ("今日", "コンニチ"): "キョウ",
}

KANJI_RE = re.compile(r"[㐀-鿿々]")
PUNCT = set("。、！？!?.,「」『』（）()・…〜ー　 \"'")


def kata2hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def has_kanji(s: str) -> bool:
    return bool(KANJI_RE.search(s))


@dataclass
class Tok:
    s: str        # surface
    p1: str       # pos1
    p2: str       # pos2
    ct: str       # conjugation type
    cf: str       # conjugation form
    lemma: str
    base: str     # orthographic dictionary form (what learners see as "dictionary form")
    kana: str     # reading of surface, hiragana
    base_kana: str  # reading of dictionary form, hiragana
    start: int
    end: int

    @property
    def is_verb(self):
        return self.p1 == "動詞"

    @property
    def is_adj(self):
        return self.p1 == "形容詞"


def tokenize(text: str) -> list[Tok]:
    out = []
    pos = 0
    for w in _tagger(text):
        f = w.feature
        s = w.surface
        start = text.find(s, pos)
        if start < 0:
            start = pos
        end = start + len(s)
        pos = end
        kana = f.kana if f.kana and f.kana != "*" else s
        ov = READING_OVERRIDES.get((s, kana))
        if ov:
            kana = ov
        base = f.orthBase if f.orthBase and f.orthBase != "*" else s
        lemma = f.lemma if f.lemma and f.lemma != "*" else s
        if s.startswith("行っ") and lemma == "行う":  # 行った is almost always いった
            lemma, base, kana, bk0 = "行く", "行く", "イッ" + s[2:], "イク"
        else:
            bk0 = None
        bk = bk0 or (f.kanaBase if f.kanaBase and f.kanaBase != "*" else kana)
        if (base, bk) in READING_OVERRIDES and READING_OVERRIDES[(base, bk)]:
            bk = READING_OVERRIDES[(base, bk)]
        out.append(Tok(s, f.pos1 or "", f.pos2 or "", f.cType or "*", f.cForm or "*",
                       lemma, base, kata2hira(kana), kata2hira(bk), start, end))
    return out


def ruby_segments(tok: Tok) -> list[list[str]]:
    """Split one token into [text, reading] segments; reading is '' for kana-only parts."""
    s, r = tok.s, tok.kana
    if not has_kanji(s) or not r or r == s:
        return [[s, ""]]
    hs = kata2hira(s)
    # strip common kana prefix
    i = 0
    while i < len(hs) and i < len(r) and hs[i] == r[i] and not has_kanji(s[i]):
        i += 1
    # strip common kana suffix
    j = 0
    while j < len(hs) - i and j < len(r) - i and hs[-1 - j] == r[-1 - j] and not has_kanji(s[-1 - j]):
        j += 1
    segs = []
    if i:
        segs.append([s[:i], ""])
    core_s = s[i:len(s) - j]
    core_r = r[i:len(r) - j]
    segs.append([core_s, core_r if core_r else ""])
    if j:
        segs.append([s[len(s) - j:], ""])
    return segs


def furigana(toks: list[Tok]) -> list[list[str]]:
    segs: list[list[str]] = []
    for t in toks:
        for seg in ruby_segments(t):
            # merge consecutive plain-kana segments to keep payload small
            if seg[1] == "" and segs and segs[-1][1] == "":
                segs[-1][0] += seg[0]
            else:
                segs.append(seg)
    return segs
