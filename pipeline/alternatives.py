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
    # 静かなのに, 行ったのに; not だのに / ですのに / ますのに, nor ののに (子供のくせに)
    return not (prev and prev.s in ("だ", "です", "ます", "の"))


def _not_after_na(prev: Tok | None) -> bool:
    return not (prev and prev.s == "な")


def _you_da_after(prev: Tok | None) -> bool:
    # verb / adjective / auxiliary, or の / な (子供のようだ, 静かなようだ); not a bare noun
    return bool(prev) and (prev.p1 in ("動詞", "形容詞", "助動詞") or prev.s in ("の", "な"))


def _verb_before(prev: Tok | None) -> bool:
    # right after a verb or an auxiliary (会うたびに, 知りつつも), not after a noun or の
    return bool(prev) and prev.p1 in ("動詞", "助動詞")


def _verb_adj_before(prev: Tok | None) -> bool:
    return bool(prev) and prev.p1 in ("動詞", "助動詞", "形容詞")


def _noun_before(prev: Tok | None) -> bool:
    # right after a noun (子供に限らず, 英語はもとより)
    return bool(prev) and prev.p1 in ("名詞", "代名詞") or bool(prev) and prev.p1 == "接尾辞" and prev.p2.startswith("名詞")


def _not_after_no_na(prev: Tok | None) -> bool:
    return not (prev and prev.s in ("の", "な"))


def _not_after_na_da(prev: Tok | None) -> bool:
    return not (prev and prev.s in ("な", "だ"))


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
    [  # hearsay
        ("sou_hear", [("そうでした", POLITE_PAST), ("そうです", POLITE), ("そうだ", PLAIN)], _verb_adj_before),
        ("rashii", [("らしいです", POLITE), ("らしい", PLAIN)], _not_after_na_da),
    ],
    [  # a cause, good or bad
        ("okage_de", [("おかげで", "de"), ("おかげだ", "da"), ("おかげです", "desu"), ("おかげか", "ka")], _any),
        ("sei_de", [("せいで", "de"), ("せいだ", "da"), ("せいです", "desu"), ("せいか", "ka")], _any),
    ],
    [  # while (a span of time)
        ("uchi_ni", [("うちに", "")], _any),
        ("aida", [("あいだに", "")], _any),
    ],
    [  # while doing
        ("nagara", [("ながら", "")], _verb_before),
        ("tsutsu", [("つつ", "")], _verb_before),
    ],
    [  # although
        ("nagara_mo", [("ながらも", "")], _any),
        ("tsutsu_mo", [("つつも", "")], _verb_before),
    ],
    [  # covered with
        ("darake", [("だらけ", "")], _any),
        ("mamire", [("まみれ", "")], _any),
    ],
    [  # without doing (ないで / ずに: converted in alternatives(), the verb form changes)
        ("naide", [("ないで", "")], _any),
        ("zu_ni", [("ずに", "")], _any),
    ],
    [  # every time
        ("tabi_ni", [("たびに", "")], _verb_before),
        ("goto_ni", [("ごとに", "")], _verb_before),
    ],
    [  # as one thing changes, so does another
        ("ni_tsurete", [("につれて", "te"), ("につれ", "ren")], _any),
        ("ni_shitagatte", [("にしたがって", "te"), ("にしたがい", "ren")], _any),
        ("ni_tomonatte", [("にともなって", "te"), ("にともない", "ren")], _any),
    ],
    [  # on the occasion of
        ("ni_saishite", [("にさいして", "te"), ("にさいし", "ren")], _any),
        ("ni_atatte", [("にあたって", "te"), ("にあたり", "ren")], _any),
    ],
    [  # not only ... but also
        ("dake_de_naku", [("だけでなく", ""), ("だけではなく", ""), ("ばかりでなく", "")], _any),
        ("nomi_narazu", [("のみならず", "")], _any),
        ("bakari_ka", [("ばかりか", "")], _any),
        ("ni_kagirazu", [("にかぎらず", "")], _noun_before),
        ("wa_motoyori", [("はもとより", "")], _noun_before),
    ],
    [  # on the other hand
        ("ippou", [("いっぽうでは", ""), ("いっぽうで", "")], _any),
        ("hanmen", [("はんめん", "")], _any),
    ],
    [  # even
        ("sae", [("でさえ", "de"), ("さえ", "bare")], _any),
        ("sura", [("ですら", "de"), ("すら", "bare")], _any),
    ],
    [  # it must be / it should be
        ("ni_chigainai", [("にちがいない", PLAIN), ("にちがいありません", POLITE)], _not_after_no_na),
        ("hazu", [("はずだ", PLAIN), ("はずです", POLITE)], _you_da_after),
    ],
    [  # about, to the extent of
        ("hodo", [("ほど", "")], _any),
        ("gurai", [("くらい", ""), ("ぐらい", "")], _any),
    ],
    [  # in the end, after all that
        ("ageku", [("あげくのはてに", "hate"), ("あげくに", "ni"), ("あげく", "bare")], _any),
        ("sue_ni", [("すえに", "ni"), ("すえ", "bare")], _any),
    ],
    [  # for, considering
        ("ni_shite_wa", [("にしては", "")], _not_after_no_na),
        ("wari_ni", [("わりには", ""), ("わりに", "")], _verb_adj_before),
    ],
    [  # although, with blame
        ("noni", [("のに", "")], _noni_after),
        ("kuse_ni", [("くせに", "")], _not_after_na_da),
    ],
]

# nouns of gradual change: X に伴って / につれて / にしたがって all work after them (after other nouns
# にしたがって means "obeying" and に伴って "along with": no swap)
CHANGE_NOUNS = {"増加", "減少", "進歩", "発展", "変化", "上昇", "低下", "成長", "普及", "発達", "拡大", "進行", "経過",
                "増大", "悪化", "改善", "高齢化", "年齢"}

# nouns that まみれ can follow (something sticky or dirty covering you); だらけ goes with anything
MAMIRE_NOUNS = {"泥", "どろ", "汗", "あせ", "血", "ち", "ほこり", "埃", "油", "あぶら", "砂", "すな", "粉", "こな", "雪", "ゆき",
                "借金", "しゃっきん", "ゴミ", "ごみ", "傷", "きず"}

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
    "sou_hear": ("passing on what you heard, plainly as hearsay (\"I hear that\")",
                 "rapporter ce qu'on a entendu, clairement comme un ouï-dire (« il paraît que »)"),
    "okage_de": ("a cause you are grateful for: it led to something good",
                 "une cause dont on est reconnaissant : elle a mené à quelque chose de bien"),
    "sei_de": ("a cause you blame: it led to something bad",
               "une cause qu'on accuse : elle a mené à quelque chose de mal"),
    "uchi_ni": ("\"while it is still so\": do it in time, before the situation changes",
                "« tant que c'est encore le cas » : le faire à temps, avant que ça change"),
    "aida": ("\"during\" a span of time, neutral, with no idea of urgency",
             "« pendant » une période, neutre, sans idée d'urgence"),
    "nagara": ("the everyday \"while doing\" (two actions at once)",
               "le « en faisant » courant (deux actions à la fois)"),
    "tsutsu": ("the written, formal \"while doing\"",
               "le « en faisant » écrit, soutenu"),
    "nagara_mo": ("the more common \"although\", after verbs, adjectives or nouns",
                  "le « bien que » plus courant, après un verbe, un adjectif ou un nom"),
    "tsutsu_mo": ("the written \"although (doing)\", often for knowing or thinking something and doing the opposite",
                  "le « tout en (faisant) » écrit, souvent : savoir ou penser une chose et faire l'inverse"),
    "darake": ("\"full of, covered in\" anything, usually unpleasant (mistakes, dust, debts)",
               "« plein de, couvert de » n'importe quoi, souvent désagréable (fautes, poussière, dettes)"),
    "mamire": ("\"smeared all over\" with something sticky or dirty (mud, sweat, blood)",
               "« tout maculé » de quelque chose de collant ou de sale (boue, sueur, sang)"),
    "naide": ("the everyday \"without doing\"",
              "le « sans faire » courant"),
    "zu_ni": ("the slightly formal, written \"without doing\"",
              "le « sans faire » un peu soutenu, écrit"),
    "tabi_ni": ("\"each time\" something happens, often with a feeling about it",
                "« chaque fois que » quelque chose arrive, souvent avec un sentiment"),
    "goto_ni": ("\"every\" regular unit or interval (every hour, every time, step by step)",
                "« à chaque » unité ou intervalle régulier (toutes les heures, à chaque fois)"),
    "ni_tsurete": ("\"as\" one thing changes, another changes naturally with it",
                   "« à mesure que » : une chose change, une autre change naturellement avec elle"),
    "ni_shitagatte": ("\"as, in step with\": a change that follows another, a bit formal",
                      "« au fur et à mesure que » : un changement qui en suit un autre, un peu soutenu"),
    "ni_tomonatte": ("\"along with\": a formal word, often for events or official changes",
                     "« avec, en même temps que » : soutenu, souvent pour des événements ou changements officiels"),
    "ni_saishite": ("\"on the occasion of\", at that very moment (formal)",
                    "« à l'occasion de », au moment même (soutenu)"),
    "ni_atatte": ("\"when starting, in preparing for\" something you undertake",
                  "« au moment d'entreprendre », en se préparant à quelque chose"),
    "dake_de_naku": ("the everyday \"not only ... but also\"",
                     "le « non seulement ... mais aussi » courant"),
    "nomi_narazu": ("the formal, written \"not only ... but also\"",
                    "le « non seulement ... mais aussi » soutenu, écrit"),
    "bakari_ka": ("\"not only ... but even\": the second thing is more surprising",
                  "« non seulement ... mais même » : la seconde chose est plus surprenante"),
    "ni_kagirazu": ("\"not limited to\": the first is just one example among many",
                    "« pas seulement » : la première chose n'est qu'un exemple parmi d'autres"),
    "wa_motoyori": ("\"not to mention\": the first is obvious, the second is the point",
                    "« sans parler de » : la première chose va de soi, la seconde compte"),
    "ippou": ("\"while, on the other hand\": two facts set side by side, neutral",
              "« alors que, d'un autre côté » : deux faits mis côte à côte, neutre"),
    "hanmen": ("\"but at the same time\": two sides of one thing, one good and one bad",
               "« mais en revanche » : deux faces d'une même chose, l'une bonne, l'autre mauvaise"),
    "sae": ("the everyday \"even\"",
            "le « même » courant"),
    "sura": ("the literary, emphatic \"even\" (written)",
             "le « même » littéraire et appuyé (à l'écrit)"),
    "ni_chigainai": ("a firm conclusion you've reached: \"it must be\"",
                     "une conclusion ferme : « ça doit être »"),
    "hazu": ("what you expect from what you know: \"it should be\"",
             "ce qu'on attend d'après ce qu'on sait : « ça devrait être »"),
    "hodo": ("\"to the extent of\", a bit formal; also for comparisons",
             "« au point de », un peu soutenu ; aussi pour comparer"),
    "gurai": ("\"about, around\", everyday; also \"at least\" or \"so much that\"",
              "« environ », courant ; aussi « au moins » ou « tellement que »"),
    "ageku": ("\"in the end, after all that\": a tiresome or bad outcome",
              "« à la fin, après tout ça » : une issue pénible ou mauvaise"),
    "sue_ni": ("\"in the end, after long effort\": often a good outcome",
               "« à la fin, après de longs efforts » : souvent une bonne issue"),
    "ni_shite_wa": ("\"for\" someone or something: compared with what you'd expect of it",
                    "« pour » quelqu'un ou quelque chose : par rapport à ce qu'on en attendrait"),
    "wari_ni": ("\"considering\" a degree or amount: more or less than you'd expect",
                "« compte tenu de » un degré ou une quantité : plus ou moins que prévu"),
    "kuse_ni": ("a \"though\" that blames or looks down on someone",
                "un « alors que » qui reproche ou méprise"),
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
            continue
        stem = answer_kana[: len(answer_kana) - len(ending[0])]
        if not _context_ok(pid, ending[0], stem, ts, a, b, text):
            continue
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
            if not _swap_ok(pid, other, stem, prev, nxt, ts, b):
                continue
            if {pid, other} == {"naide", "zu_ni"}:
                alt = _without(answer_kana, to_zu=(other == "zu_ni"))
                if alt and alt not in accepted and alt not in out:
                    out.append(alt)
                continue
            for e, k in endings:
                if any("\u4e00" <= ch <= "\u9fff" for ch in e):  # kana only: the learner types kana
                    continue
                if ending[1] and k and k != ending[1]:
                    continue
                alt = stem + e
                if alt not in accepted and alt not in out:
                    out.append(alt)
    return out


def _context_ok(pid: str, ending: str, stem: str, ts: list[Tok], a: int, b: int, text: str) -> bool:
    """Whether this sentence's blank can take another point of the group at all."""
    # さえ〜ば (if only): すら can't
    if pid == "sae" and any(t.s in ("ば", "たら", "れば") for t in ts[b:]):
        return False
    # AほどBない (not as ... as): くらい would change the meaning
    if pid in ("hodo", "gurai") and any(t.lemma in ("ない", "無い", "ず") or t.s.startswith("ませ") for t in ts[b:]):
        return False
    # 〜につれて after a noun: only nouns of change (ご忠告に従って means "obeying")
    if pid in ("ni_tsurete", "ni_shitagatte", "ni_tomonatte") and a > 0 and ts[a - 1].p1 in ("名詞", "代名詞", "接尾辞") \
            and ts[a - 1].s not in CHANGE_NOUNS:
        return False
    # に従いなさい: the verb "obey"
    if pid == "ni_shitagatte" and b < len(ts) and ts[b].p1 in ("助動詞", "動詞"):
        return False
    # 近いうちに (soon), 今のうちに (while you can): set phrases
    if pid == "uchi_ni" and a > 0 and (ts[a - 1].s == "近い" or (a > 1 and ts[a - 1].s == "の" and ts[a - 2].s == "今")):
        return False
    # 一方である (keeps ...ing) is another point
    if pid == "ippou" and b < len(ts) and ts[b].lemma in ("ある", "有る"):
        return False
    # sentence-final ないで (please don't): a request, ずに can't
    if pid == "naide" and (b >= len(ts) or ts[b].s in ("。", "！", "!", "？", "?", "ね", "よ")):
        return False
    # ないでください / ないでくれ / ないでほしい: a request, ずに can't
    if pid == "naide" and any(t.s in ("ください", "下さい", "くれ", "くれる", "ほしい", "欲しい", "くださ") for t in ts[b:b + 2]):
        return False
    return True


def _swap_ok(pid: str, other: str, stem: str, prev: Tok | None, nxt: Tok | None, ts: list[Tok], b: int) -> bool:
    """Whether `other` can replace `pid` here (rules beyond the token before the blank)."""
    # まみれ only for something smeared on you (mud, sweat, blood), not mistakes or problems
    if other == "mamire":
        noun = stem or (prev.s if prev else "")
        return any(noun == n or (len(n) > 1 and noun.endswith(n)) for n in MAMIRE_NOUNS)
    # 同じくらい: a set phrase (同じほど sounds odd); どのくらい but not どのほど
    if other == "hodo" and prev is not None and prev.s in ("同じ", "どの", "この", "その", "あの"):
        return False
    # 〜ないうちに (before it happens): 間に can't follow a negative
    if other == "aida" and prev is not None and prev.lemma in ("ない", "無い", "ぬ", "ず"):
        return False
    return True


def _without(answer: str, to_zu: bool) -> str:
    """しないで ↔ せずに, 食べないで ↔ 食べずに, こないで ↔ こずに."""
    if to_zu:
        if not answer.endswith("ないで"):
            return ""
        stem = answer[: -len("ないで")]
        if stem.endswith("し"):  # する: しないで → せずに
            stem = stem[:-1] + "せ"
        return stem + "ずに"
    if not answer.endswith("ずに"):
        return ""
    stem = answer[: -len("ずに")]
    if stem.endswith("せ"):  # せずに → しないで
        stem = stem[:-1] + "し"
    return stem + "ないで"
