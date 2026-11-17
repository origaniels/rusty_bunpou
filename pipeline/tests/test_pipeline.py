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
    ("夕食は何時か。", "何時", "なんじ"), ("何時ですか。", "何時", "なんじ"),
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
