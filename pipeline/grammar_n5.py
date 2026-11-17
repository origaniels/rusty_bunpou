"""N5 grammar points: original explanations + token matchers.

Each matcher receives the token list of a sentence and returns a list of
(start_idx, end_idx_exclusive, hint_idx | None). The span [start, end) becomes the
cloze blank; hint_idx points at the content word whose dictionary form is shown as a hint.
"""
from __future__ import annotations

from jp import Tok

POINTS: list[dict] = []


def point(pid, title, meaning, structure, explanation):
    def deco(fn):
        POINTS.append(dict(id=pid, level="N5", title=title, meaning=meaning,
                           structure=structure, explanation=explanation.strip(), match=fn))
        return fn
    return deco


# ---------------------------------------------------------------- helpers

def at(toks, i):
    return toks[i] if 0 <= i < len(toks) else None


def is_end(toks, i):
    t = at(toks, i)
    return t is None or t.p1 == "補助記号"


VERB_AUX = ("ます", "た", "ず", "ない")


def ext(toks, j, allowed=VERB_AUX):
    """Extend a span end over trailing auxiliaries (ます, た, ん, ない, ませんでした)."""
    while j < len(toks):
        t = toks[j]
        if t.p1 == "助動詞" and t.lemma in allowed:
            j += 1
            continue
        if (t.p1 == "助動詞" and t.lemma == "です" and toks[j - 1].lemma == "ず"
                and at(toks, j + 1) and toks[j + 1].lemma == "た"):
            j += 2
            continue
        break
    # don't cut a word in half: 強くなっ|て → include the て
    if j < len(toks) and te(toks[j]) and toks[j - 1].p1 in ("動詞", "助動詞") and toks[j - 1].cf.startswith("連用形"):
        j += 1
    return j


def ext_adj(toks, j):
    """After adjectives: た and です."""
    while j < len(toks) and toks[j].p1 == "助動詞" and toks[j].lemma in ("た", "です"):
        j += 1
    return j


def particle(surfaces, p2=None):
    surfaces = set(surfaces)

    def f(t):
        return t.p1 == "助詞" and t.s in surfaces and (p2 is None or t.p2 in (p2 if isinstance(p2, tuple) else (p2,)))
    return f


def te(t):
    return t is not None and t.p1 == "助詞" and t.lemma == "て"


def lemma_is(t, *lemmas):
    return t is not None and t.lemma in lemmas


def content_verb(t):
    return t is not None and t.p1 == "動詞"


def nounish(t):
    return t is not None and t.p1 in ("名詞", "代名詞", "形状詞") and t.p2 != "数詞" or (t is not None and t.p1 == "接尾辞")


def single_particle(pred, extra=None):
    def m(toks):
        out = []
        for i, t in enumerate(toks):
            if pred(t) and (extra is None or extra(toks, i)):
                out.append((i, i + 1, None))
        return out
    return m


# ---------------------------------------------------------------- copula

@point("da", "だ", "is / am / are (casual)", "Noun / な-adj + だ",
       """
だ is the casual copula: it links a subject to a noun or な-adjective, like "is" in English.
It is the plain counterpart of です. In casual speech it is often dropped entirely, and
it is never used after い-adjectives (暑いだ is wrong).
""")
def m_da(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "だ" and t.p1 == "助動詞" and t.cf.startswith("終止形")
            and nounish(at(toks, i - 1)) and is_end(toks, i + 1)]


@point("desu", "です", "is / am / are (polite)", "Noun / adjective + です",
       """
です is the polite copula. After a noun or な-adjective it means "is". After an
い-adjective it carries no meaning of its own and simply makes the sentence polite.
""")
def m_desu(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "です" and t.p1 == "助動詞" and t.cf.startswith("終止形")
            and nounish(at(toks, i - 1))]


@point("deshita", "でした", "was (polite)", "Noun / な-adj + でした",
       """
でした is the past tense of です. It turns "X is Y" into "X was Y" while staying polite.
For い-adjectives, the past is carried by the adjective itself (暑かったです), not by でした.
""")
def m_deshita(toks):
    return [(i, i + 2, None) for i, t in enumerate(toks)
            if t.s == "でし" and t.lemma == "です" and at(toks, i + 1) is not None and toks[i + 1].s == "た"
            and nounish(at(toks, i - 1))]


@point("datta", "だった", "was (casual)", "Noun / な-adj + だった",
       """
だった is the past tense of だ, the casual copula: "was". Like だ, it attaches to
nouns and な-adjectives, never to い-adjectives.
""")
def m_datta(toks):
    return [(i, i + 2, None) for i, t in enumerate(toks)
            if t.s == "だっ" and t.lemma == "だ" and at(toks, i + 1) is not None and toks[i + 1].s == "た"
            and nounish(at(toks, i - 1))]


@point("janai", "じゃない・ではない", "is not", "Noun / な-adj + じゃない / ではない (+ です) / ではありません",
       """
To say something "is not" a noun or な-adjective, replace だ with じゃない (spoken) or ではない
(more formal/written). The polite versions are じゃないです / じゃありません and
ではありません. じゃ is simply a contraction of では.
""")
def m_janai(toks):
    out = []
    for i, t in enumerate(toks):
        if not nounish(at(toks, i - 1)):
            continue
        if t.s == "じゃ" and t.lemma == "だ":
            j = i + 1
        elif t.s == "で" and at(toks, i + 1) and toks[i + 1].s == "は":
            j = i + 2
        else:
            continue
        n = at(toks, j)
        if n and n.lemma == "無い" and n.p1 == "形容詞":
            out.append((i, ext_adj(toks, j + 1), None))
        elif n and n.lemma == "有る" and at(toks, j + 1) and toks[j + 1].s == "ませ":
            out.append((i, ext(toks, j + 1), None))
    return out


@point("na_adj", "な-adjective + な", "(attaches な-adjectives to nouns)", "な-adj + な + Noun",
       """
な-adjectives need な when they come directly before a noun: 静かな部屋 (a quiet room),
きれいな花 (a pretty flower). At the end of a sentence they take だ/です instead.
""")
def m_na(toks):
    return [(i, i + 1, i - 1) for i, t in enumerate(toks)
            if t.s == "な" and t.p1 == "助動詞" and t.lemma == "だ"
            and at(toks, i - 1) and toks[i - 1].p1 == "形状詞"
            and at(toks, i + 1) and toks[i + 1].p1 in ("名詞", "代名詞")]


# ---------------------------------------------------------------- particles

@point("wa", "は", "topic marker", "Topic + は + comment",
       """
は (pronounced わ) marks the topic: what the sentence is about. Think of it as
"as for X, ...". Everything after は is a comment about that topic. It often contrasts the
topic with other things, which is the main difference from が.
""")
def m_wa(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "は" and t.p2 == "係助詞"
            and not (at(toks, i - 1) and (te(toks[i - 1]) or toks[i - 1].s == "で"))]


@point("mo", "も", "also, too", "Noun + も",
       """
も means "also / too" and replaces は, が or を: 私も行きます (I'm going too).
It can stack after other particles: 東京にも (in Tokyo too). With a negative verb it means
"not ... either".
""")
def m_mo(toks):
    out = []
    for i, t in enumerate(toks):
        if t.s == "も" and t.p2 == "係助詞":
            p = at(toks, i - 1)
            if p is None or te(p) or p.s in ("何", "誰", "どこ", "いつ", "なに", "だれ", "で") or p.p2 == "数詞":
                continue
            out.append((i, i + 1, None))
    return out


@point("ga", "が", "subject marker", "Subject + が + verb / adjective",
       """
が marks the grammatical subject, the one who does or is something. Use it to introduce new
information, to answer "who/what" questions, and with verbs like ある, いる, 好き, 分かる,
which take が for their object.
""")
def m_ga(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "が" and t.p2 == "格助詞"
            and not (at(toks, i - 1) and toks[i - 1].lemma in ("事", "方"))]


@point("no", "の", "possessive / noun linker", "Noun + の + Noun",
       """
の links two nouns, with the first describing the second: 私の本 (my book),
日本の車 (a Japanese car), 先生の友達 (the teacher's friend). It covers "'s", "of" and
many other relations.
""")
def m_no(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "の" and t.p2 == "格助詞"
            and at(toks, i - 1) and toks[i - 1].p1 in ("名詞", "代名詞")
            and at(toks, i + 1) and toks[i + 1].p1 in ("名詞",)
            and toks[i + 1].lemma not in ("時", "後", "前", "方")]


@point("wo", "を", "direct object marker", "Object + を + verb",
       """
を (pronounced お) marks the direct object, the thing an action is done to:
パンを食べる (eat bread). With motion verbs it can also mark the space moved through:
公園を歩く (walk through the park).
""")
def m_wo(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "を" and t.p1 == "助詞"
            and not (at(toks, i + 1) and toks[i + 1].lemma == "下さる")]


@point("ni", "に", "to, at, in (target, time, location of existence)", "Noun + に",
       """
に points at a target: the destination (学校に行く), the receiver (友達にあげる), a specific
time (七時に起きる), or the place where something exists (部屋にいる).
""")
def m_ni(toks):
    out = []
    for i, t in enumerate(toks):
        if t.s == "に" and t.p2 == "格助詞":
            p = at(toks, i - 1)
            n = at(toks, i + 1)
            if p is None or p.p1 not in ("名詞", "代名詞", "接尾辞"):
                continue
            if p.lemma in ("前", "為"):
                continue
            if n is not None and n.lemma == "成る":
                continue
            out.append((i, i + 1, None))
    return out


@point("e", "へ", "to, toward (direction)", "Place + へ + motion verb",
       """
へ (pronounced え) marks the direction of movement: 日本へ行く (go to Japan).
It is very close to に; へ emphasizes the direction, に the arrival point.
""")
def m_e(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks) if t.s == "へ" and t.p2 == "格助詞"]


@point("de", "で", "at, in (place of action); by, with (means)", "Place / tool + で + verb",
       """
で marks where an action takes place (図書館で勉強する, study at the library) or the means
used to do it (バスで行く, go by bus; 箸で食べる, eat with chopsticks).
Compare に, which marks where something simply exists.
""")
def m_de(toks):
    out = []
    for i, t in enumerate(toks):
        if t.s == "で" and t.p2 == "格助詞":
            n = at(toks, i + 1)
            if n is not None and n.s in ("は", "も"):
                continue
            p = at(toks, i - 1)
            if p is None or p.p1 not in ("名詞", "代名詞", "接尾辞") or p.lemma == "後":
                continue
            out.append((i, i + 1, None))
    return out


QUOTE_VERBS = {"言う", "思う", "考える", "成る", "呼ぶ", "書く", "聞く", "為る", "答える", "云う"}


@point("to", "と", "and; with", "Noun + と + Noun / Person + と + verb",
       """
と joins nouns in a complete list: パンと牛乳 (bread and milk). After a person
it means "with": 友達と行く (go with a friend). It only joins nouns, not verbs or sentences.
""")
def m_to(toks):
    out = []
    for i, t in enumerate(toks):
        if t.s == "と" and t.p2 == "格助詞":
            p, n = at(toks, i - 1), at(toks, i + 1)
            if p is None or p.p1 not in ("名詞", "代名詞", "接尾辞") or p.s in ("なん", "何", "ちょっと", "もっ"):
                continue
            if n is None or n.p1 == "補助記号" or n.lemma in QUOTE_VERBS or n.p1 == "動詞":
                if not (n is not None and n.p1 == "動詞" and n.lemma not in QUOTE_VERBS
                        and n.lemma in ("行く", "来る", "話す", "会う", "遊ぶ", "住む", "結婚", "帰る")):
                    continue
            out.append((i, i + 1, None))
    return out


@point("ya", "や", "and (among others)", "Noun + や + Noun",
       """
や lists nouns as examples, implying there are other things too: 本やペン (books, pens and
so on). Compare と, which gives a complete list. It is often paired with など.
""")
def m_ya(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "や" and t.p1 == "助詞" and at(toks, i - 1) and toks[i - 1].p1 in ("名詞", "代名詞", "接尾辞")]


@point("kara_from", "から (from)", "from (starting point)", "Noun + から",
       """
から after a noun marks a starting point, in space or time: 駅から歩く (walk from the station),
九時から (from nine o'clock). It pairs naturally with まで.
""")
def m_kara_from(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "から" and t.p2 == "格助詞"
            and at(toks, i - 1) and toks[i - 1].p1 in ("名詞", "代名詞", "接尾辞")]


@point("made", "まで", "until, as far as", "Noun + まで",
       """
まで marks an end point in space or time: 駅まで (as far as the station), 五時まで (until five).
It is often combined with から: 九時から五時まで (from nine to five).
""")
def m_made(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "まで" and t.p1 == "助詞" and at(toks, i - 1) and toks[i - 1].p1 in ("名詞", "代名詞", "接尾辞")]


@point("ka", "か (question)", "question marker", "Sentence + か",
       """
Adding か to the end of a sentence turns it into a question: 学生ですか (Are you a student?).
In polite speech no question mark is needed; in casual speech か can sound blunt, so a rising
intonation is used instead.
""")
def m_ka(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "か" and t.p2 == "終助詞" and is_end(toks, i + 1) and at(toks, i + 1) is not None
            and at(toks, i - 1) and at(toks, i - 1).lemma in ("です", "ます")]


@point("ne", "ね", "right?, isn't it? (seeking agreement)", "Sentence + ね",
       """
ね at the end of a sentence invites the listener to agree, like "isn't it?" or "right?":
いい天気ですね (Nice weather, isn't it?). It makes speech softer and friendlier.
""")
def m_ne(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "ね" and t.p2 == "終助詞" and is_end(toks, i + 1)]


@point("yo", "よ", "(emphasis; telling new info)", "Sentence + よ",
       """
よ at the end of a sentence tells the listener something they may not know, or adds emphasis:
おいしいですよ (It's delicious, you know). Overusing it can sound pushy.
""")
def m_yo(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "よ" and t.p2 == "終助詞" and is_end(toks, i + 1)]


@point("yori", "より", "than", "A + は + B + より + adjective",
       """
より marks the thing being compared against: 犬は猫より大きい (dogs are bigger than cats).
The item with より is the "than" side. It often pairs with のほうが on the other side.
""")
def m_yori(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s == "より" and t.p2 == "格助詞"]


@point("dake", "だけ", "only, just", "Noun / verb + だけ",
       """
だけ means "only / just" and limits the word before it: 一つだけ (just one), 見るだけ
(just looking). Unlike しか, it is used with a positive verb.
""")
def m_dake(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks) if t.s == "だけ" and t.p1 == "助詞"]


@point("shika", "しか〜ない", "only, nothing but (with negative)", "Noun + しか + negative verb",
       """
しか means "only", but the verb that follows is always negative: 百円しかない
(I have only 100 yen; literally "except 100 yen, there isn't any"). It stresses that the
amount is small or not enough.
""")
def m_shika(toks):
    out = []
    for i, t in enumerate(toks):
        if t.s == "しか" and t.p1 == "助詞":
            if any(x.lemma in ("ない", "ず", "無い") for x in toks[i + 1:]):
                out.append((i, i + 1, None))
    return out


@point("gurai", "ぐらい・くらい", "about, approximately", "Amount + ぐらい / くらい",
       """
ぐらい (or くらい) after an amount means "about / approximately": 一時間ぐらい
(about an hour), 百人くらい (around 100 people). For points in time, ごろ is used instead.
""")
def m_gurai(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s in ("ぐらい", "くらい") and t.p1 == "助詞"]


@point("goro", "ごろ", "around (a point in time)", "Time + ごろ",
       """
ごろ after a point in time means "around": 三時ごろ (around three o'clock), 十月ごろ
(around October). Use ぐらい for amounts and durations instead.
""")
def m_goro(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s in ("ごろ", "頃") and at(toks, i - 1) is not None
            and (toks[i - 1].s.endswith(("時", "月", "日", "年")) or toks[i - 1].p2 == "数詞")]


@point("tachi", "たち", "(plural for people)", "Person + たち",
       """
Japanese nouns normally have no plural, but たち can be added to people (and pronouns) to make
a group: 私たち (we), 子供たち (the children). It is not used for objects.
""")
def m_tachi(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s in ("たち", "達") and t.p1 == "接尾辞"]


# ---------------------------------------------------------------- demonstratives

@point("kore", "これ・それ・あれ・どれ", "this one / that one / that one over there / which one",
       "これ / それ / あれ / どれ (standalone)",
       """
These pronouns stand in for a thing. これ: near the speaker. それ: near the listener.
あれ: far from both. どれ: which one (out of three or more). They stand alone and are never
followed directly by a noun; for that, use この/その/あの/どの.
""")
def m_kore(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s in ("これ", "それ", "あれ", "どれ") and t.p1 == "代名詞"
            and at(toks, i + 1) is not None and toks[i + 1].p1 == "助詞"
            and toks[i + 1].s not in ("くらい", "ぐらい", "だけ")]


@point("kono", "この・その・あの・どの", "this / that / that over there / which (+ noun)",
       "この / その / あの / どの + Noun",
       """
These always come directly before a noun: この本 (this book), その人 (that person),
あの店 (that shop over there), どの車 (which car). Same near/far logic as これ/それ/あれ/どれ.
""")
def m_kono(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s in ("この", "その", "あの", "どの") and t.p1 == "連体詞"
            and at(toks, i + 1) and toks[i + 1].p1 == "名詞"]


@point("koko", "ここ・そこ・あそこ・どこ", "here / there / over there / where",
       "ここ / そこ / あそこ / どこ",
       """
Place words following the same pattern: ここ (here, near me), そこ (there, near you),
あそこ (over there, far from both), どこ (where?).
""")
def m_koko(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s in ("ここ", "そこ", "あそこ", "どこ") and t.p1 == "代名詞"]


# ---------------------------------------------------------------- polite verbs

def _verb_then(toks, i, first_s, rest):
    """toks[i] is a verb, toks[i+1].s == first_s and following surfaces match rest."""
    j = i + 1
    for s in (first_s,) + tuple(rest):
        t = at(toks, j)
        if t is None or t.s != s:
            return None
        j += 1
    return j


@point("masu", "ます", "(polite non-past verb)", "Verb stem + ます",
       """
ます makes a verb polite in the present/future: 食べる → 食べます, 行く → 行きます.
The verb goes into its stem (連用形) form. Use it with strangers, teachers and colleagues.
""")
def m_masu(toks):
    out = []
    for i, t in enumerate(toks):
        n = at(toks, i + 1)
        if content_verb(t) and n is not None and n.s == "ます" and n.lemma == "ます" \
                and not (at(toks, i - 1) and te(toks[i - 1])):
            out.append((i, i + 2, i))
    return out


@point("masen", "ません", "(polite negative verb)", "Verb stem + ません",
       """
ません is the polite negative: 食べません (don't eat / won't eat), 行きません.
It is ます's "not" form.
""")
def m_masen(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t) and not (at(toks, i - 1) and te(toks[i - 1])):
            j = _verb_then(toks, i, "ませ", ["ん"])
            if j and not (at(toks, j) and at(toks, j).s in ("でし", "か")):
                out.append((i, j, i))
    return out


@point("mashita", "ました", "(polite past verb)", "Verb stem + ました",
       """
ました is the polite past: 食べました (ate), 行きました (went). Like ます, it attaches to the
verb stem, so whatever stem you use for ます works here too: 見ます → 見ました, します → しました.
""")
def m_mashita(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t) and not (at(toks, i - 1) and te(toks[i - 1])):
            j = _verb_then(toks, i, "まし", ["た"])
            if j:
                out.append((i, j, i))
    return out


@point("masendeshita", "ませんでした", "(polite past negative verb)", "Verb stem + ませんでした",
       """
ませんでした is the polite past negative: 食べませんでした (did not eat). It is literally
ません + でした.
""")
def m_masendeshita(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t):
            j = _verb_then(toks, i, "ませ", ["ん", "でし", "た"])
            if j:
                out.append((i, j, i))
    return out


@point("mashou", "ましょう", "let's ...", "Verb stem + ましょう",
       """
ましょう means "let's ...": 行きましょう (let's go). It is the polite volitional form and
also expresses "I'll ..." when offering to do something.
""")
def m_mashou(toks):
    out = []
    for i, t in enumerate(toks):
        n = at(toks, i + 1)
        if content_verb(t) and n is not None and n.s == "ましょう" and not (at(toks, i + 2) and toks[i + 2].s == "か"):
            out.append((i, i + 2, i))
    return out


@point("mashouka", "ましょうか", "shall we ...? / shall I ...?", "Verb stem + ましょうか",
       """
ましょうか turns "let's" into a suggestion or offer: 行きましょうか (shall we go?),
手伝いましょうか (shall I help?).
""")
def m_mashouka(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t):
            j = _verb_then(toks, i, "ましょう", ["か"])
            if j:
                out.append((i, j, i))
    return out


@point("masenka", "ませんか", "won't you ...? (invitation)", "Verb stem + ませんか",
       """
ませんか literally asks "won't you ...?" and is a polite, soft way to invite someone:
一緒に行きませんか (Would you like to go together?).
""")
def m_masenka(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t):
            j = _verb_then(toks, i, "ませ", ["ん", "か"])
            if j and is_end(toks, j):
                out.append((i, j, i))
    return out


# ---------------------------------------------------------------- plain verb forms

@point("nai", "ない (negative)", "do not (casual negative)", "Verb (ない-form)",
       """
The plain negative: 食べる → 食べない, 行く → 行かない (う-sound becomes あ-sound + ない),
する → しない, 来る → こない. Exception: ある → ない. Past: 食べなかった.
""")
def m_nai(toks):
    out = []
    for i, t in enumerate(toks):
        n = at(toks, i + 1)
        if content_verb(t) and n is not None and n.p1 == "助動詞" and n.lemma == "ない" \
                and n.s in ("ない", "なかっ"):
            j = ext(toks, i + 2, ("た",))
            if at(toks, j) and at(toks, j).s in ("で", "ほう", "方"):
                continue
            out.append((i, j, i))
    return out


@point("ta", "た (past)", "did (casual past)", "Verb (た-form)",
       """
The plain past. It is built exactly like the て-form, with た instead of て:
食べた, 行った, 読んだ, した, 来た.
""")
def m_ta(toks):
    out = []
    for i, t in enumerate(toks):
        n = at(toks, i + 1)
        if content_verb(t) and t.p2 == "一般" and n is not None and n.lemma == "た" and n.p1 == "助動詞" \
                and is_end(toks, i + 2):
            out.append((i, i + 2, i))
    return out


@point("tai", "たい", "want to ...", "Verb stem + たい",
       """
たい attaches to the verb stem to mean "want to": 食べたい (want to eat), 行きたい.
It conjugates like an い-adjective: 行きたくない, 行きたかった. Use it for your own wishes;
for others it sounds presumptuous.
""")
def m_tai(toks):
    out = []
    for i, t in enumerate(toks):
        n = at(toks, i + 1)
        if content_verb(t) and n is not None and n.lemma == "たい" and n.p1 == "助動詞":
            j = i + 2
            if n.s == "たかっ":
                j = ext_adj(toks, j)
            elif n.s == "たく" and at(toks, j) and at(toks, j).lemma == "無い":
                j = ext_adj(toks, j + 1)
            out.append((i, j, i))
    return out


@point("te_iru", "ている", "is ...ing; is in a state of", "Verb (て-form) + いる",
       """
て-form + いる describes an ongoing action (読んでいる, is reading) or a resulting state
(結婚している, is married; 知っている, knows). Polite: ています. In casual speech the い often
drops: 読んでる.
""")
def m_te_iru(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t) and te(at(toks, i + 1)) and lemma_is(at(toks, i + 2), "居る") \
                and toks[i + 2].p1 == "動詞":
            out.append((i, ext(toks, i + 3), i))
    return out


@point("te_kudasai", "てください", "please do ...", "Verb (て-form) + ください",
       """
て-form + ください is a polite request: 見てください (please look), 待ってください
(please wait). ください is often written in kana when used this way.
""")
def m_te_kudasai(toks):
    return [(i, i + 3, i) for i, t in enumerate(toks)
            if content_verb(t) and te(at(toks, i + 1)) and lemma_is(at(toks, i + 2), "下さる")
            and toks[i + 2].cf.startswith("命令形")]


@point("naide_kudasai", "ないでください", "please don't ...", "Verb (ない-form) + でください",
       """
To ask someone not to do something, use the ない-form + でください:
触らないでください (please don't touch).
""")
def m_naide(toks):
    out = []
    for i, t in enumerate(toks):
        n = at(toks, i + 1)
        if content_verb(t) and n is not None and n.s == "ない" and n.p1 == "助動詞" \
                and at(toks, i + 2) and toks[i + 2].s == "で" and lemma_is(at(toks, i + 3), "下さる"):
            out.append((i, i + 4, i))
    return out


@point("o_kudasai", "をください", "please give me ...", "Noun + を + ください",
       """
Noun + をください asks for something: 水をください (water, please).
It is how you order or request objects.
""")
def m_o_kudasai(toks):
    return [(i + 1, i + 2, None) for i, t in enumerate(toks)
            if t.s == "を" and lemma_is(at(toks, i + 1), "下さる") and toks[i + 1].cf.startswith("命令形")]


@point("temo_ii", "てもいい", "may, it's okay to ...", "Verb (て-form) + もいい",
       """
て-form + もいい gives or asks for permission: 入ってもいいですか (may I come in?),
食べてもいい (you can eat it). Literally "even if you do ..., it's good".
""")
def m_temo_ii(toks):
    return [(i, i + 4, i) for i, t in enumerate(toks)
            if content_verb(t) and te(at(toks, i + 1)) and at(toks, i + 2) and toks[i + 2].s == "も"
            and lemma_is(at(toks, i + 3), "良い")]


@point("tewa_ikenai", "てはいけない", "must not ...", "Verb (て-form) + はいけない",
       """
て-form + はいけない forbids something: ここで泳いではいけない (you must not swim here).
Literally "if you do ..., it won't do". Polite: てはいけません.
""")
def m_tewa(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t) and te(at(toks, i + 1)) and at(toks, i + 2) and toks[i + 2].s == "は" \
                and at(toks, i + 3) and toks[i + 3].base in ("いける", "行ける"):
            j = ext(toks, i + 4)
            if j > i + 4:
                out.append((i, j, i))
    return out


@point("tekara", "てから", "after doing ...", "Verb (て-form) + から",
       """
て-form + から means "after doing X, (then) Y", stressing the order: 手を洗ってから
食べる (eat after washing your hands).
""")
def m_tekara(toks):
    return [(i, i + 3, i) for i, t in enumerate(toks)
            if content_verb(t) and te(at(toks, i + 1)) and at(toks, i + 2) and toks[i + 2].s == "から"]


@point("ta_koto_ga_aru", "たことがある", "have done ... before (experience)", "Verb (た-form) + ことがある",
       """
た-form + ことがある talks about experience: 富士山に登ったことがある (I have climbed
Mt. Fuji). The negative ことがない means "have never ...".
""")
def m_ta_koto(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t) and lemma_is(at(toks, i + 1), "た") and at(toks, i + 2) \
                and toks[i + 2].lemma == "事" and at(toks, i + 3) and toks[i + 3].s in ("が", "は", "も") \
                and lemma_is(at(toks, i + 4), "有る", "無い"):
            out.append((i, ext(toks, i + 5) if toks[i + 4].lemma == "有る" else ext_adj(toks, i + 5), i))
    return out


@point("tari", "たり〜たりする", "doing things like A and B", "Verb (た-form) + り, Verb (た-form) + り + する",
       """
たり lists actions as examples, not a complete or ordered list: 本を読んだり、映画を見たり
する (I do things like reading books and watching movies). The last たり is followed by する.
""")
def m_tari(toks):
    idx = [i for i, t in enumerate(toks)
           if t.lemma == "たり" and t.p1 == "助詞" and at(toks, i - 1) is not None and toks[i - 1].p1 == "動詞"]
    if len(idx) >= 2:
        i = idx[0]
        return [(i - 1, i + 1, i - 1)]
    return []


@point("hou_ga_ii", "ほうがいい", "had better ...; should", "Verb (た-form / ない-form) + ほうがいい",
       """
ほうがいい gives advice: 早く寝たほうがいい (you'd better go to bed early).
Positive advice usually uses the past form (た); negative advice uses ない:
行かないほうがいい (you'd better not go).
""")
def m_hou(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t):
            n = at(toks, i + 1)
            if n is None or n.p1 != "助動詞" or n.lemma not in ("た", "ない"):
                continue
            if at(toks, i + 2) and toks[i + 2].s in ("ほう", "方") and at(toks, i + 3) and toks[i + 3].s == "が" \
                    and lemma_is(at(toks, i + 4), "良い"):
                out.append((i, i + 5, i))
    return out


@point("mae_ni", "前に", "before ...", "Verb (dictionary form) + 前に / Noun + の + 前に",
       """
前に means "before". After a verb it is always the dictionary form, even if the sentence is
in the past: 寝る前に (before sleeping). After a noun use の: 食事の前に (before the meal).
""")
def m_mae(toks):
    out = []
    for i, t in enumerate(toks):
        if t.s == "前" and at(toks, i + 1) and toks[i + 1].s == "に":
            p = at(toks, i - 1)
            if p is not None and p.p1 == "動詞" and p.cf.startswith(("終止形", "連体形")):
                out.append((i - 1, i + 2, i - 1))
    return out


@point("ato_de", "後で", "after ...", "Verb (た-form) + 後で / Noun + の + 後で",
       """
後で (あとで) means "after". After a verb it takes the past form: 食べた後で (after eating).
After a noun, use の: 授業の後で (after class).
""")
def m_ato(toks):
    out = []
    for i, t in enumerate(toks):
        if t.lemma == "後" and t.kana == "あと" and at(toks, i + 1) and toks[i + 1].s == "で":
            p = at(toks, i - 1)
            if p is not None and p.lemma == "た" and at(toks, i - 2) and toks[i - 2].p1 == "動詞":
                out.append((i - 2, i + 2, i - 2))
    return out


@point("ni_iku", "に行く (purpose)", "go (in order) to do ...", "Verb stem + に + 行く / 来る",
       """
Verb stem + に + a motion verb (行く, 来る, 帰る) expresses the purpose of the movement:
映画を見に行く (go to see a movie), 遊びに来る (come over to hang out).
""")
def m_ni_iku(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t) and t.cf.startswith("連用形") and at(toks, i + 1) and toks[i + 1].s == "に" \
                and lemma_is(at(toks, i + 2), "行く", "来る", "帰る"):
            out.append((i, ext(toks, i + 3), i))
    return out


@point("nagara", "ながら", "while doing ...", "Verb stem + ながら",
       """
ながら joins two actions done at the same time by the same person: 音楽を聞きながら
勉強する (study while listening to music). The main action is the second one.
""")
def m_nagara(toks):
    return [(i, i + 2, i) for i, t in enumerate(toks)
            if content_verb(t) and at(toks, i + 1) and toks[i + 1].s == "ながら"]


@point("nakereba", "なければならない", "must, have to", "Verb (ない-form minus い) + ければならない",
       """
なければならない means "must": 勉強しなければならない (I have to study). Literally "if I
don't study, it won't do". Variations: なければいけない, polite なければなりません.
""")
def m_nakereba(toks):
    out = []
    for i, t in enumerate(toks):
        if content_verb(t) and at(toks, i + 1) and toks[i + 1].s == "なけれ" and at(toks, i + 2) \
                and toks[i + 2].s == "ば" and at(toks, i + 3) and toks[i + 3].base in ("なる", "成る", "いける", "行ける"):
            j = ext(toks, i + 4)
            if j > i + 4:
                out.append((i, j, i))
    return out


@point("nasai", "なさい", "do ... (command, soft)", "Verb stem + なさい",
       """
なさい is a firm but not rude command, typical of parents and teachers:
早く寝なさい (go to bed!), よく聞きなさい (listen carefully).
""")
def m_nasai(toks):
    return [(i, i + 2, i) for i, t in enumerate(toks)
            if content_verb(t) and at(toks, i + 1) and toks[i + 1].s == "なさい"]


@point("kata", "方 (way of)", "how to ..., way of ...ing", "Verb stem + 方",
       """
Verb stem + 方 (かた) makes a noun meaning "the way of doing": 書き方 (how to write),
使い方 (how to use). The object of the verb takes の: 漢字の読み方.
""")
def m_kata(toks):
    return [(i, i + 2, i) for i, t in enumerate(toks)
            if content_verb(t) and at(toks, i + 1) and toks[i + 1].s == "方" and toks[i + 1].p1 == "接尾辞"]


@point("aru", "ある (exist, things)", "there is (inanimate)", "Thing + が + ある",
       """
ある says that a non-living thing exists or is somewhere: 机の上に本がある (there's a book
on the desk). It also means "to have": 時間がある. Its negative is irregular: ない.
""")
def m_aru(toks):
    out = []
    for i, t in enumerate(toks):
        if t.lemma == "有る" and t.p1 == "動詞" and at(toks, i - 1) is not None and toks[i - 1].s in ("が", "は", "も") \
                and toks[i - 2 if i >= 2 else 0].lemma != "事" and not (at(toks, i - 2) and toks[i - 2].s == "で"):
            out.append((i, ext(toks, i + 1), None))
    return out


@point("iru", "いる (exist, living)", "there is (animate)", "Person / animal + が + いる",
       """
いる says that a person or animal exists or is somewhere: 公園に子供がいる (there are
children in the park). It also means "to have" for family or pets: 兄がいる.
""")
def m_iru(toks):
    out = []
    for i, t in enumerate(toks):
        if t.lemma == "居る" and t.p1 == "動詞" and at(toks, i - 1) is not None and toks[i - 1].s in ("が", "は", "も", "に") \
                and not (at(toks, i - 1) and te(toks[i - 1])):
            out.append((i, ext(toks, i + 1), None))
    return out


# ---------------------------------------------------------------- adjectives

@point("i_adj_neg", "くない", "not (い-adjective negative)", "い-adj (drop い) + くない",
       """
To negate an い-adjective, swap the final い for くない: 高い → 高くない (not expensive).
Polite: 高くないです / 高くありません. Irregular: いい → よくない.
""")
def m_adj_neg(toks):
    out = []
    for i, t in enumerate(toks):
        n = at(toks, i + 1)
        if t.is_adj and t.p2 != "非自立可能" and t.cf.startswith("連用形") and t.s.endswith("く") \
                and n is not None and n.lemma == "無い" and n.p1 == "形容詞":
            out.append((i, ext_adj(toks, i + 2), i))
    return out


@point("i_adj_past", "かった", "was (い-adjective past)", "い-adj (drop い) + かった",
       """
The past of an い-adjective: swap い for かった: 楽しい → 楽しかった (was fun).
Add です for politeness: 楽しかったです (never 楽しいでした). Irregular: いい → よかった.
""")
def m_adj_past(toks):
    out = []
    for i, t in enumerate(toks):
        n = at(toks, i + 1)
        if t.is_adj and t.lemma not in ("無い",) and t.s.endswith("かっ") and n is not None and n.s == "た":
            if at(toks, i - 1) and at(toks, i - 1).is_adj and at(toks, i - 1).s.endswith("く"):
                continue
            out.append((i, ext_adj(toks, i + 2), i))
    return out


@point("kute", "くて", "and (joining い-adjectives)", "い-adj (drop い) + くて",
       """
To chain an い-adjective with something else, use its て-form: drop い and add くて:
安くておいしい (cheap and tasty). For な-adjectives and nouns, use で instead.
""")
def m_kute(toks):
    return [(i, i + 2, i) for i, t in enumerate(toks)
            if t.is_adj and t.lemma != "無い" and t.s.endswith("く") and te(at(toks, i + 1))
            and toks[i + 1].s == "て"]


@point("naru", "なる (become)", "become", "い-adj → く + なる / Noun, な-adj + に + なる",
       """
なる means "become". い-adjectives change い to く: 寒くなる (get cold). Nouns and
な-adjectives take に: 先生になる (become a teacher), 元気になる (get better).
""")
def m_naru(toks):
    out = []
    for i, t in enumerate(toks):
        if t.lemma == "成る" and t.p1 == "動詞" and i > 0:
            p = toks[i - 1]
            if p.is_adj and p.s.endswith("く") and p.lemma != "無い":
                out.append((i - 1, ext(toks, i + 1), i - 1))
    return out


@point("hoshii", "ほしい", "want (something)", "Noun + が + ほしい",
       """
ほしい is an い-adjective meaning "want (a thing)": 新しい車がほしい (I want a new car).
The thing wanted takes が. For wanting to do an action, use たい instead.
""")
def m_hoshii(toks):
    out = []
    for i, t in enumerate(toks):
        if t.lemma == "欲しい" and t.p1 == "形容詞" and at(toks, i - 1) is not None and toks[i - 1].s in ("が", "は", "も"):
            out.append((i, ext_adj(toks, i + 1) if t.s.endswith("かっ") else i + 1, None))
    return out


@point("suki", "好き", "like", "Noun + が + 好き",
       """
好き (すき) is a な-adjective meaning "liked": 猫が好きです (I like cats). The thing liked
takes が. 大好き means "really like / love"; the opposite is 嫌い (きらい).
""")
def m_suki(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.lemma == "好き" and t.p1 == "形状詞" and at(toks, i - 1) is not None and toks[i - 1].s in ("が", "は", "も")]


@point("ichiban", "一番", "the most, number one", "一番 + adjective",
       """
一番 (いちばん) before an adjective makes a superlative: 一番高い (the most expensive).
The group is often given with の中で: 果物の中でりんごが一番好きです.
""")
def m_ichiban(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s in ("一番", "いちばん") and at(toks, i + 1) and toks[i + 1].p1 in ("形容詞", "形状詞", "副詞")]


@point("amari", "あまり〜ない", "not very, not much", "あまり + negative",
       """
あまり with a negative verb or adjective means "not very / not much":
あまり高くない (not very expensive), あまり食べない (don't eat much).
""")
def m_amari(toks):
    out = []
    for i, t in enumerate(toks):
        if t.s in ("あまり", "余り", "あんまり") and t.p1 == "副詞":
            if any(x.lemma in ("無い", "ない", "ず") for x in toks[i + 1:]):
                out.append((i, i + 1, None))
    return out


# ---------------------------------------------------------------- conjunctions & misc

@point("kara_because", "から (because)", "because, so", "Sentence + から",
       """
から after a sentence gives the reason: 雨だから、行かない (it's raining, so I won't go).
The reason comes first, the result second. It is a bit more subjective and casual than ので.
""")
def m_kara_bec(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks) if t.s == "から" and t.p2 == "接続助詞"]


@point("node", "ので", "because, since", "Sentence + ので (な before nouns / な-adj)",
       """
ので also gives a reason, but sounds softer and more objective than から, which makes it
common in polite explanations: 熱があるので、休みます (I have a fever, so I'll rest).
After nouns and な-adjectives it becomes なので.
""")
def m_node(toks):
    return [(i, i + 2, None) for i, t in enumerate(toks)
            if t.s == "の" and t.p2 == "準体助詞" and at(toks, i + 1) and toks[i + 1].s == "で"
            and toks[i + 1].p1 == "助動詞" and at(toks, i + 2) and toks[i + 2].s == "、"]


@point("ga_but", "が (but)", "but", "Sentence + が、Sentence",
       """
が after a full sentence means "but": 高いですが、おいしいです (it's expensive, but tasty).
It is slightly formal; it can also just soften an introduction (すみませんが...).
""")
def m_ga_but(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks) if t.s == "が" and t.p2 == "接続助詞"]


@point("kedo", "けど", "but, although", "Sentence + けど / けれど(も)",
       """
けど is the casual "but": 行きたいけど、時間がない (I want to go, but I have no time).
けれど and けれども are longer, slightly more formal versions.
""")
def m_kedo(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.s in ("けど", "けれど", "けれども") and t.p2 == "接続助詞"]


@point("deshou", "でしょう", "probably; right? ", "Sentence + でしょう",
       """
でしょう expresses a guess, "probably": 明日は雨でしょう (it will probably rain tomorrow).
With rising intonation it asks for confirmation: "right?". Casual form: だろう.
""")
def m_deshou(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks) if t.s == "でしょう" and t.lemma == "です"]


@point("toki", "とき", "when, at the time of", "Verb / adjective / Noun + の + とき",
       """
とき (時) means "when / at the time when": 子供のとき (when I was a child),
暇なとき (when I'm free), 寝るとき (when I go to bed).
""")
def m_toki(toks):
    return [(i, i + 1, None) for i, t in enumerate(toks)
            if t.lemma == "時" and t.kana == "とき" and i > 0
            and toks[i - 1].p1 in ("動詞", "形容詞", "助詞", "助動詞")]


@point("to_iu", "という", "called, named", "Name + という + Noun",
       """
X という Y means "a Y called X": 田中という人 (a person named Tanaka),
「こころ」という本 (a book called "Kokoro").
""")
def m_to_iu(toks):
    return [(i, i + 2, None) for i, t in enumerate(toks)
            if t.s == "と" and at(toks, i + 1) and toks[i + 1].s in ("いう", "言う") and toks[i + 1].cf.startswith("連体形")
            and at(toks, i + 2) and toks[i + 2].p1 == "名詞"]
