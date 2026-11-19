"""Grammar points that can often take each other's place in a sentence (から / ので, けど / が, ...).

When the learner types another point of the same group where it fits, the answer is possible but
not what the exercise is about: the app says what nuance the expected point adds (without giving
the answer) and lets them try again.

Each member lists the endings its blank can have, with a key: an ending is only swapped for one
with the same key (polite for polite, past for past); key "" matches any. `after(prev)` says
whether the ending can follow the token just before the blank (ので needs な after a noun, not だ).
"""
from __future__ import annotations

from jp import Tok

PLAIN, POLITE, PAST, POLITE_PAST, ATTR = "plain", "polite", "past", "polite-past", "attr"


def _any(prev: Tok | None) -> bool:
    return True


def _not_after_da(prev: Tok | None) -> bool:
    return not (prev and prev.s == "だ")


def _noni_after(prev: Tok | None) -> bool:
    # 静かなのに, 行ったのに; not だのに / ですのに / ますのに
    return not (prev and prev.s in ("だ", "です", "ます"))


def _not_after_na(prev: Tok | None) -> bool:
    return not (prev and prev.s == "な")


def _you_da_after(prev: Tok | None) -> bool:
    # verb / adjective / auxiliary, or の / な (子供のようだ, 静かなようだ); not a bare noun
    return bool(prev) and (prev.p1 in ("動詞", "形容詞", "助動詞") or prev.s in ("の", "な"))


def _mitai_after(prev: Tok | None) -> bool:
    # verb / adjective / noun directly (子供みたい), not after の / な
    return bool(prev) and prev.s not in ("の", "な") and prev.p1 in ("動詞", "形容詞", "助動詞", "名詞", "代名詞", "形状詞")


# group -> [(point id, [(ending, key)], after)]
GROUPS: list[list[tuple[str, list[tuple[str, str]], object]]] = [
    [  # giving a reason
        ("kara_because", [("から", "")], _not_after_na),
        ("node", [("ので", "")], _not_after_da),
    ],
    [  # but
        ("ga_but", [("が", "")], _not_after_na),
        ("kedo", [("けれども", ""), ("けれど", ""), ("けど", "")], _not_after_na),
        ("noni", [("のに", "")], _noni_after),
    ],
    [  # must
        ("nakereba", [("なければならない", PLAIN), ("なければなりません", POLITE), ("なければいけない", PLAIN),
                      ("なければいけません", POLITE)], _any),
        ("nakute_wa", [("なくてはいけない", PLAIN), ("なくてはいけません", POLITE), ("なくてはならない", PLAIN),
                       ("なくてはなりません", POLITE)], _any),
        ("naito", [("ないといけない", PLAIN), ("ないといけません", POLITE)], _any),
    ],
    [  # probably / maybe
        ("kamoshirenai", [("かもしれない", ""), ("かもしれません", "")], _any),
        ("deshou", [("でしょう", "")], _any),
        ("darou", [("だろう", "")], _any),
    ],
    [  # seems
        ("you_da", [("ようでした", POLITE_PAST), ("ようだった", PAST), ("ようです", POLITE), ("ようだ", PLAIN),
                    ("ような", ATTR)], _you_da_after),
        ("mitai", [("みたいでした", POLITE_PAST), ("みたいだった", PAST), ("みたいです", POLITE), ("みたいだ", PLAIN),
                   ("みたいな", ATTR), ("みたい", PLAIN)], _mitai_after),
        ("rashii", [("らしかった", PAST), ("らしいです", POLITE), ("らしい", PLAIN)], _mitai_after),
    ],
    [  # about
        ("ni_tsuite", [("については", "wa"), ("についての", "no"), ("について", "te")], _any),
        ("ni_kanshite", [("に関しては", "wa"), ("に関しての", "no"), ("に関して", "te"), ("にかんしては", "wa"),
                         ("にかんしての", "no"), ("にかんして", "te")], _any),
    ],
]

# what the expected point adds: "That could work, but here we're looking for <nuance>."
NUANCE = {
    "kara_because": ("the more direct, personal way to give a reason (also before requests and opinions)",
                     "la façon plus directe et personnelle de donner une raison (aussi avant une demande ou un avis)"),
    "node": ("the softer, more objective way to give a reason (explanations, polite excuses)",
             "la façon plus douce et objective de donner une raison (explications, excuses polies)"),
    "ga_but": ("the neutral, slightly formal \"but\" (writing, polite speech)",
               "le « mais » neutre, un peu soutenu (à l'écrit, en langage poli)"),
    "kedo": ("the conversational \"but\"",
             "le « mais » de la conversation"),
    "noni": ("a \"but\" that shows surprise or frustration: things didn't go as expected",
             "un « mais » qui exprime la surprise ou la frustration : ça ne s'est pas passé comme prévu"),
    "nakereba": ("the standard \"must\" for rules and duties, a bit formal",
                 "le « devoir » standard, pour les règles et obligations, un peu soutenu"),
    "nakute_wa": ("the spoken \"must\", a little less formal",
                  "le « devoir » de l'oral, un peu moins soutenu"),
    "naito": ("the casual spoken \"have to\", often a personal need",
              "le « il faut » familier de l'oral, souvent un besoin personnel"),
    "kamoshirenai": ("a possibility, not a likely guess (\"maybe, might\")",
                     "une simple possibilité, pas une supposition probable (« peut-être »)"),
    "deshou": ("a polite guess (\"probably\"), or asking for agreement",
               "une supposition polie (« sans doute »), ou demander l'accord"),
    "darou": ("a plain, casual guess (\"probably\"), often in thoughts or writing",
              "une supposition neutre, familière (« sans doute »), souvent en pensée ou à l'écrit"),
    "you_da": ("a judgement from what you observe yourself, a bit formal",
               "un jugement fondé sur ce qu'on observe soi-même, un peu soutenu"),
    "mitai": ("the casual, spoken \"seems / looks like\"",
              "le « on dirait » familier de l'oral"),
    "rashii": ("something you heard or read (hearsay), not your own observation",
               "une information entendue ou lue (ouï-dire), pas sa propre observation"),
    "ni_tsuite": ("the everyday \"about\"",
                  "le « à propos de » courant"),
    "ni_kanshite": ("the formal \"regarding\" (documents, announcements)",
                    "le « concernant » soutenu (documents, annonces)"),
}


QUESTION_WORDS = {"何", "なに", "なん", "どう", "どんな", "どの", "どこ", "どれ", "誰", "だれ", "いつ", "なぜ", "どうして", "いくら", "いくつ"}


def alternatives(pid: str, answer_kana: str, ts: list[Tok], a: int, b: int, accepted: set[str]) -> list[str]:
    """Answers (kana) using another point of `pid`'s group instead, that fit in the sentence `ts`
    whose blank is the tokens [a, b)."""
    prev = ts[a - 1] if a > 0 else None
    nxt = ts[b] if b < len(ts) else None
    text = "".join(t.s for t in ts)
    # a question (どうなるだろう, いないんでしょう？): かもしれない can't ask
    question = any(t.s in QUESTION_WORDS for t in ts[:a]) or text.rstrip("。").endswith(("？", "?", "か"))
    out: list[str] = []
    for group in GROUPS:
        ids = [m[0] for m in group]
        if pid not in ids:
            continue
        me = group[ids.index(pid)]
        ending = next(((e, k) for e, k in me[1] if answer_kana.endswith(e)), None)
        if ending is None:
            return []
        stem = answer_kana[: len(answer_kana) - len(ending[0])]
        # bare みたい followed by だった / です / な / に: らしい or ようだ can't take its place
        if ending[0] == "みたい" and nxt is not None and (nxt.p1 == "助動詞" or nxt.s in ("な", "に")):
            return []
        # からです is fine, のでです / けどです are not
        if ending[0] in ("から", "ので", "が", "けど", "けれど", "けれども", "のに") and nxt is not None and nxt.p1 == "助動詞":
            return []
        for other, endings, after in group:
            # the token before the ending matters only when the blank is the ending alone
            if other == pid or (not stem and not after(prev)):
                continue
            # でしょうか / だろうか, but not かもしれないか; not んかもしれない either
            if other == "kamoshirenai" and (question or (nxt is not None and nxt.s == "か") or (not stem and prev is not None and prev.s == "ん")):
                continue
            # まるで goes with ようだ / みたい, not らしい
            if other == "rashii" and "まるで" in text:
                continue
            for e, k in endings:
                if e.startswith("に関"):  # kana only: the learner types kana
                    continue
                if ending[1] and k and k != ending[1]:
                    continue
                alt = stem + e
                if alt not in accepted and alt not in out:
                    out.append(alt)
    return out
