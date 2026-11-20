"""Tests for the content pipeline: grammar matchers, readings, furigana and answers."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build import answers_for, span_tags  # noqa: E402
from grammar_n5 import POINTS  # noqa: E402
from jp import furigana, ruby_segments, tokenize  # noqa: E402

BY_ID = {p["id"]: p for p in POINTS}


def blanks(pid, sentence):
    """Surface text of each blank the matcher produces for `sentence`."""
    toks = tokenize(sentence)
    return ["".join(t.s for t in toks[a:b]) for a, b, _ in BY_ID[pid]["match"](toks)]


# (point id, sentence, expected blank) — one or more positive examples per point
POSITIVE = [
    ("da", "明日は雨だ。", "だ"),
    ("desu", "これは本です。", "です"),
    ("deshita", "昨日は休みでした。", "でした"),
    ("datta", "彼女はきれいだった。", "だった"),
    ("janai", "これは私の本じゃない。", "じゃない"),
    ("janai", "私は学生ではありません。", "ではありません"),
    ("na_adj", "静かな部屋です。", "な"),
    ("wa", "私は学生です。", "は"),
    ("mo", "私も行きます。", "も"),
    ("wo", "パンを食べる。", "を"),
    ("e", "日本へ行く。", "へ"),
    ("de", "図書館で勉強する。", "で"),
    ("de", "バスで行く。", "で"),
    ("ato_de", "ご飯を食べた後で、散歩した。", "食べた後で"),
    ("kara_from", "駅から歩いた。", "から"),
    ("made", "駅まで歩いた。", "まで"),
    ("ka", "学生ですか。", "か"),
    ("ne", "いい天気ですね。", "ね"),
    ("yori", "犬は猫より大きい。", "より"),
    ("shika", "百円しかない。", "しか"),
    ("goro", "三時ごろ来ます。", "ごろ"),
    ("tachi", "子供たちが遊んでいる。", "たち"),
    ("kono", "この本は高い。", "この"),
    ("masu", "毎日コーヒーを飲みます。", "飲みます"),
    ("masen", "肉は食べません。", "食べません"),
    ("mashita", "昨日映画を見ました。", "見ました"),
    ("masendeshita", "昨日は勉強しませんでした。", "しませんでした"),
    ("mashou", "一緒に行きましょう。", "行きましょう"),
    ("mashouka", "窓を開けましょうか。", "開けましょうか"),
    ("masenka", "映画を見ませんか。", "見ませんか"),
    ("nai", "私は肉を食べない。", "食べない"),
    ("tai", "日本に行きたい。", "行きたい"),
    ("tai", "日本に行きたかったです。", "行きたかったです"),
    ("te_iru", "雨が降っている。", "降っている"),
    ("te_iru", "雨が降っています。", "降っています"),
    ("te_kudasai", "本を読んでください。", "読んでください"),
    ("naide_kudasai", "ここで写真を撮らないでください。", "撮らないでください"),
    ("o_kudasai", "水をください。", "ください"),
    ("temo_ii", "食べてもいいですか。", "食べてもいい"),
    ("tewa_ikenai", "ここで泳いではいけません。", "泳いではいけません"),
    ("tekara", "ご飯を食べてから、出かけた。", "食べてから"),
    ("ta_koto_ga_aru", "富士山に登ったことがあります。", "登ったことがあります"),
    ("tari", "本を読んだり、音楽を聞いたりします。", "読んだり"),
    ("hou_ga_ii", "早く寝たほうがいい。", "寝たほうがいい"),
    ("mae_ni", "寝る前に歯を磨く。", "寝る前に"),
    ("ni_iku", "映画を見に行きます。", "見に行きます"),
    ("nagara", "音楽を聞きながら勉強します。", "聞きながら"),
    ("nakereba", "勉強しなければなりません。", "しなければなりません"),
    ("nasai", "早く寝なさい。", "寝なさい"),
    ("kata", "漢字の書き方を教えてください。", "書き方"),
    ("i_adj_neg", "この本は高くない。", "高くない"),
    ("i_adj_past", "旅行は楽しかった。", "楽しかった"),
    ("kute", "この店は安くておいしい。", "安くて"),
    ("naru", "寒くなりました。", "寒くなりました"),
    ("hoshii", "新しい車が欲しい。", "欲しい"),
    ("suki", "猫が好きです。", "好き"),
    ("ichiban", "これが一番好きです。", "一番"),
    ("amari", "あまり高くないです。", "あまり"),
    ("kara_because", "雨だから、行かない。", "から"),
    ("node", "熱があるので、休みます。", "ので"),
    ("kedo", "行きたいけど、時間がない。", "けど"),
    ("deshou", "明日は雨でしょう。", "でしょう"),
    ("to_iu", "田中という人が来た。", "という"),
]

# (point id, sentence) — things a matcher must NOT pick up
NEGATIVE = [
    ("ya", "今や有名店ですね。"),  # 今や = nowadays
    ("ya", "外国語は１年やそこらで身につけられるものではない。"),  # やそこら = or so
    ("ya", "母はその先生のことやぶ医者だって思ってる。"),  # やぶ医者 = quack doctor
    ("kute", "遅くても来ないよりまし。"),  # くても = even if
    ("to_iu", "問題はお金がないということです。"),  # ということ = the fact that (N3)
    ("mo", "食べてもいい。"),             # ても is not "also"
    ("mo", "何も食べない。"),             # 何も is its own expression
    ("wa", "ここで泳いではいけない。"),    # ては is not the topic marker
    ("de", "私は学生ではありません。"),    # では of the copula
    ("de", "熱があるので、休みます。"),    # ので
    ("ni", "先生になりたい。"),           # になる (become)
    ("kore", "どれくらいかかりますか。"),  # どれくらい = how long
    ("to", "なんとか間に合った。"),        # なんとか
    ("ta", "食べたことがある。"),          # not sentence-final past
    ("nai", "食べないでください。"),       # ないでください has its own point
    ("masu", "食べています。"),            # ています belongs to ている
    ("shika", "しかし、行かない。"),       # しかし (however)
    ("amari", "あまりにも高い。"),         # no negative
    ("tari", "本を読んだりする。"),        # needs two たり
    ("ka", "何か食べる？"),
    ("deshita", "私のことでしたらご心配なく。"),   # でしたら is conditional, not "was"
    ("datta", "暇だったら来てください。"),
    ("mashita", "着きましたら電話します。"),
    ("i_adj_past", "高かったら買わない。"),               # not a sentence-final question marker after です/ます
]


@pytest.mark.parametrize("pid,sentence,expected", POSITIVE)
def test_matcher_finds_blank(pid, sentence, expected):
    assert expected in blanks(pid, sentence), f"{pid}: {blanks(pid, sentence)}"


@pytest.mark.parametrize("pid,sentence", NEGATIVE)
def test_matcher_rejects(pid, sentence):
    assert blanks(pid, sentence) == []


def test_every_point_has_a_positive_example():
    covered = {pid for pid, _, _ in POSITIVE}
    # points whose matcher is a plain particle lookup are covered via the bundled content tests
    allowed_missing = {"ga", "no", "ni", "to", "ya", "yo", "dake", "gurai", "kore", "koko", "ta", "aru", "iru",
                       "ga_but", "toki"}
    missing = {p["id"] for p in POINTS} - covered - allowed_missing
    assert not missing, missing


def test_points_metadata():
    ids = [p["id"] for p in POINTS]
    assert len(ids) == len(set(ids))
    for p in POINTS:
        assert p["title"] and p["meaning"] and p["structure"]
        assert len(p["explanation"]) > 60, p["id"]


@pytest.mark.parametrize("sentence,word,reading", [
    ("私は学生です。", "私", "わたし"), ("日本に行く。", "日本", "にほん"), ("明日は休みだ。", "明日", "あした"),
    ("夕食は何時か。", "何時", "なんじ"), ("何時ですか。", "何時", "なんじ"), ("今何時でしょうか。", "何時", "なんじ"),
])
def test_readings(sentence, word, reading):
    """The reading of `word` (possibly split over several tokens) is what a learner expects."""
    toks = tokenize(sentence)
    start = sentence.index(word)
    covered = [t for t in toks if t.start >= start and t.end <= start + len(word)]
    assert "".join(t.kana for t in covered) == reading


def test_nani_before_particles_nan_otherwise():
    assert tokenize("何か食べる。")[0].kana == "なに"
    assert tokenize("何を食べる？")[0].kana == "なに"


def test_itta_is_iku_not_okonau():
    t = next(t for t in tokenize("学校に行った。") if t.s.startswith("行"))
    assert (t.base, t.kana) == ("行く", "いっ")


def test_ruby_segments_split_okurigana():
    t = next(t for t in tokenize("本を読んだ。") if t.s == "読ん")
    assert ruby_segments(t) == [["読", "よ"], ["ん", ""]]
    t = tokenize("明かりをつけた。")[0]
    assert ruby_segments(t) == [["明", "あ"], ["かり", ""]]


def test_furigana_rebuilds_sentence():
    s = "私は毎朝コーヒーを飲みます。"
    segs = furigana(tokenize(s))
    assert "".join(x[0] for x in segs) == s
    assert all(r == "" or all("ぁ" <= c <= "ゖ" or c == "ー" for c in r) for _, r in segs)


def test_answers_accept_kana_and_kanji_variants():
    toks = tokenize("本を読んでください。")
    span = toks[2:5]
    ans = answers_for(span)
    assert "読んでください" in ans and "よんでください" in ans and "読んで下さい" in ans
    toks = tokenize("これは本じゃない。")
    a, b, _ = BY_ID["janai"]["match"](toks)[0]
    assert {"じゃない", "ではない"} <= set(answers_for(toks[a:b]))


def test_span_tags():
    toks = tokenize("昨日映画を見ませんでした。")
    a, b, _ = BY_ID["masendeshita"]["match"](toks)[0]
    assert span_tags(toks[a:b]) == ["polite", "past", "negative"]


def test_dictionary_words_for_lookups():
    from build import dictionary_words
    cases = {
        "タクシーを呼んでもらえませんか。": ["タクシー", "呼ぶ"],            # てもらう is grammar
        "日本語を勉強して、公園で遊んでいる。": ["日本語", "勉強", "公園", "遊ぶ"],  # 公園で ≠ て-form
        "私がお金を返すように頼むと、彼は聞こえないふりをします。": ["私", "お金", "返す", "頼む", "彼", "聞こえる", "ふり"],
        "この問題は複雑すぎる。": ["問題", "複雑"],
    }
    for ja, words in cases.items():
        assert dictionary_words(tokenize(ja)) == words, ja


def test_answer_parts_mark_particles_and_conjugations():
    from build import answer_parts
    ts = tokenize("学校には行きませんでした。")
    parts = answer_parts(ts[1:-1])  # に は 行き ませ ん でし た
    assert ["に", "p"] in parts and ["は", "p"] in parts
    assert all(k == "v" for kana, k in parts if kana not in ("に", "は"))
    # でした is a conjugation, not the particle で
    parts = answer_parts(tokenize("元気でした")[1:])
    assert all(k == "v" for _, k in parts), parts


def test_alternatives_fit_the_context():
    from alternatives import alternatives

    def alts(pid, ja, blank):
        ts = tokenize(ja)
        start = ja.rindex(blank)  # the last one (テニスが…が)
        a = next(k for k, t in enumerate(ts) if t.start == start)
        b = next(k for k, t in enumerate(ts) if t.end == start + len(blank)) + 1
        return alternatives(pid, blank, ts, a, b, {blank})

    assert alts("kara_because", "雨が降っているから、出かけない。", "から") == ["ので"]
    assert alts("kara_because", "学生だから、お金がない。", "から") == [], "だので is wrong"
    assert alts("kara_because", "一人になりたくないからです。", "から") == [], "のでです is wrong"
    assert alts("ga_but", "テニスがしたいのですが。", "が") == ["けれども", "けれど", "けど"], "not ですのに"
    assert alts("you_da", "子供のようだ。", "ようだ") == [], "子供のみたいだ is wrong"
    assert alts("you_da", "まるで酔っているようだ。", "ようだ") == ["みたいだ", "みたい"], "not まるで…らしい"
    assert alts("mitai", "もう嘘みたいだったよ。", "みたい") == [], "嘘らしいだった is wrong"
    assert alts("mitai", "風邪引いたみたい。", "みたい") == ["ようだ", "らしい"]
    assert "かもしれない" not in alts("darou", "失敗したらどうなるだろう。", "だろう"), "a question"
    assert "かもしれない" in alts("darou", "彼はおそらく来るだろう。", "だろう")
    # the blank includes the verb: same politeness
    ts = tokenize("行かなければなりません。")
    assert alternatives("nakereba", "いかなければなりません", ts, 0, len(ts) - 1, set()) == [
        "いかなくてはいけません", "いかなくてはなりません", "いかないといけません"]


def test_more_alternatives_and_their_context_rules():
    from alternatives import alternatives

    def alts(pid, ja, blank, kana=None):
        ts = tokenize(ja)
        start = ja.rindex(blank)
        a = next(k for k, t in enumerate(ts) if t.start == start)
        b = next(k for k, t in enumerate(ts) if t.end == start + len(blank)) + 1
        return alternatives(pid, kana or blank, ts, a, b, {kana or blank})

    assert alts("okage_de", "先生のおかげで合格した。", "おかげで") == ["せいで"]
    assert alts("naide", "朝ご飯を食べないで出かけた。", "食べないで", "たべないで") == ["たべずに"]
    assert alts("naide", "勉強しないで遊んだ。", "しないで") == ["せずに"], "する: せずに"
    assert alts("zu_ni", "勉強せずに遊んだ。", "せずに") == ["しないで"]
    assert alts("naide", "泣かないでください。", "泣かないで", "なかないで") == [], "a request: no ずに"
    assert alts("darake", "服が泥だらけになった。", "だらけ") == ["まみれ"]
    assert alts("darake", "この作文は間違いだらけだ。", "だらけ") == [], "間違いまみれ is wrong"
    assert alts("tabi_ni", "会うたびに、彼は背が伸びている。", "たびに") == ["ごとに"]
    assert alts("tabi_ni", "会議のたびに、同じ話をする。", "たびに") == [], "会議のごとに is wrong"
    assert alts("uchi_ni", "暗くならないうちに帰ろう。", "うちに") == [], "ないあいだに is wrong"
    assert alts("uchi_ni", "若いうちに旅行したい。", "うちに") == ["あいだに"]
    assert alts("sae", "時間さえあれば行ける。", "さえ") == [], "さえ〜ば: no すら"
    assert alts("hodo", "彼ほど背が高くない。", "ほど") == [], "AほどBない: no くらい"
    assert alts("kuse_ni", "子供のくせに生意気だ。", "くせに") == [], "子供ののに is wrong"
    assert "くせに" in alts("noni", "知っているのに教えてくれない。", "のに")
    assert alts("sou_hear", "明日は雨だそうだ。", "そうだ") == [], "雨だらしい is wrong"
    assert alts("sou_hear", "明日は雨が降るそうだ。", "そうだ") == ["らしい"]
    assert alts("ni_kagirazu", "子供に限らず、大人も楽しめる。", "に限らず", "にかぎらず")[:2] == ["だけでなく", "だけではなく"]
    assert "にかぎらず" not in alts("dake_de_naku", "歌うだけでなく、踊りもする。", "だけでなく"), "after a verb: no に限らず"
    assert alts("gurai", "彼は君と同じくらい速く走る。", "くらい") == [], "同じほど sounds odd"
    assert alts("naide", "音を立てないで。", "立てないで", "たてないで") == [], "please don't: no ずに"
    assert alts("ni_shitagatte", "ご忠告に従って行動します。", "に従って", "にしたがって") == [], "obeying, not 'as'"
    assert alts("uchi_ni", "近いうちに会いましょう。", "うちに") == [], "近いうちに: set phrase"
    assert "ですら" not in alts("sae", "時間さえもない。", "さえ"), "さえ ↔ すら, でさえ ↔ ですら"
    assert alts("gurai", "どのくらいバスを待っているんですか。", "くらい") == [], "どのほど is wrong"
    assert alts("gurai", "そこへ着くのにどれぐらいかかりますか。", "ぐらい") == ["ほど"], "どれほど is fine"
    assert alts("ni_shitagatte", "お父さんに従いなさい。", "に従い", "にしたがい") == [], "obey"
