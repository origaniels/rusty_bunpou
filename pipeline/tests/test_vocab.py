"""The vocabulary built from the JLPT word lists (see pipeline/vocab/README.md)."""
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build  # noqa: E402
import vocab  # noqa: E402
from jp import tokenize  # noqa: E402

BUILT = Path(__file__).resolve().parents[2] / "data" / "build" / "vocab.json"
KANJI = re.compile(r"[一-鿿々]")


@pytest.fixture(scope="module")
def built():
    return json.loads(BUILT.read_text(encoding="utf8"))


@pytest.fixture(scope="module")
def words(built):
    return built["words"]


@pytest.mark.parametrize("expression, reading, want", [
    ("会う", "あう", ("会う", "あう", "", "")),
    ("足; 脚", "あし", ("足", "あし", "脚", "")),
    ("回る、回す", "まわる、まわす", ("回る", "まわる", "回す（まわす）", "")),
    ("結婚", "けっこん (する)", ("結婚", "けっこん", "", "する")),
    ("運動", "うんどうする", ("運動", "うんどう", "", "する")),
    ("いただく", "頂く", ("頂く", "いただく", "", "")),
    ("パート (タイム)", "パート (タイム)", ("パート", "パート", "", "タイム")),
])
def test_rows_are_cleaned_up(expression, reading, want):
    w = vocab.normalise(expression, reading)
    assert (w["word"], w["reading"], w["also"], w["suffix"]) == want


def test_the_built_file_is_up_to_date(words):
    """The words as the lists give them (without Tatoeba, the order and examples aside)."""
    listed = {w["id"]: w for w in vocab.build()["words"]}
    for w in words:
        assert {**w, "ex": []} == listed[w["id"]], "run pipeline/vocab.py"


def test_only_word_parts_and_lone_kanji_are_left_out(words):
    built = {w["id"] for w in words}
    for w in vocab.build()["words"]:
        if w["id"] not in built:
            assert "～" in w["word"] or (len(w["word"]) == 1 and KANJI.search(w["word"])), w


def test_examples_show_the_word(built):
    sentences = built["sentences"]
    with_ex = [w for w in built["words"] if w["ex"]]
    assert len(with_ex) > 0.9 * len(built["words"])
    for w in with_ex:
        assert len(w["ex"]) <= vocab.EXAMPLES
        for i, a, b in w["ex"]:
            s = sentences[i]
            assert 0 <= a < b <= len(s["ja"]), (w["id"], s)
            assert "".join(seg[0] for seg in s["furi"]) == s["ja"]
            assert s["en"] and s["id"] > 0


def test_most_n5_and_n4_words_have_three_examples(built):
    easy = [w for w in built["words"] if w["level"] in ("N5", "N4")]
    assert sum(len(w["ex"]) == 3 for w in easy) > 0.9 * len(easy)


def test_every_word_is_complete_and_listed_once(words):
    assert len({w["id"] for w in words}) == len(words)
    for w in words:
        assert w["level"] in vocab.LEVELS
        assert w["word"] and w["reading"] and w["en"], w
        assert not KANJI.search(w["reading"]), f"a reading in kanji: {w}"


def test_n5_and_n4_have_french(words):
    missing = [w["id"] for w in words if w["level"] in ("N5", "N4") and not w["fr"]]
    assert not missing


def test_levels_come_in_order(words):
    order = [vocab.LEVELS.index(w["level"]) for w in words]
    assert order == sorted(order)


# ------------------------------------------------------------------ the build on small made-up lists

def make_lists(tmp_path, monkeypatch, rows_by_level, fr=None):
    """Point vocab.py at tiny word lists (and no Tatoeba frequencies unless given)."""
    for level in vocab.LEVELS:
        lines = ["expression,reading,meaning,tags,guid"]
        lines += [f'{e},{r},"{m}",JLPT,x' for e, r, m in rows_by_level.get(level, [])]
        (tmp_path / f"{level.lower()}.csv").write_text("\n".join(lines) + "\n", encoding="utf8")
    if fr is not None:
        (tmp_path / "fr.tsv").write_text(fr, encoding="utf8")
    monkeypatch.setattr(vocab, "LISTS", tmp_path)
    # a made-up Tatoeba is too small to tell a lone kanji from a word
    monkeypatch.setattr(vocab, "MIN_LONE_KANJI_USES", 0)


def tiny_corpus(*sentences):
    """A made-up Tatoeba: (Japanese, English[, French]) per sentence, ids from 1."""
    cands, toks = {}, {}
    for sid, (ja, en, *fr) in enumerate(sentences, 1):
        cands[sid] = dict(ja=ja, en=en, owner="someone", native=True)
        if fr:
            cands[sid].update(fr=fr[0], fr_id=1000 + sid, fr_owner="quelqu'un")
        toks[sid] = tokenize(ja)
    return cands, toks, build.Scorer(cands, toks)


def test_a_word_in_two_lists_keeps_the_easier_level(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {
        "N5": [("会う", "あう", "to meet")],
        "N3": [("会う", "あう", "to meet (again)"), ("論文", "ろんぶん", "thesis")],
    })
    words = vocab.build()["words"]
    assert [(w["word"], w["level"], w["en"]) for w in words] == [
        ("会う", "N5", "to meet"), ("論文", "N3", "thesis")]


def test_words_are_ordered_by_level_then_frequency(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {
        "N4": [("走る", "はしる", "to run")],
        "N5": [("犬", "いぬ", "dog"), ("猫", "ねこ", "cat")],
    })
    data = tiny_corpus(("猫がいる。", "a cat"), ("猫と犬。", "cat and dog"), ("猫だ。", "a cat"),
                       ("走る犬。", "a running dog"))
    assert [w["word"] for w in vocab.build(data)["words"]] == ["猫", "犬", "走る"]


def test_french_meanings_are_attached_to_their_rows(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [("犬", "いぬ", "dog"), ("猫", "ねこ", "cat")]},
               fr="# a comment\n\n犬\tいぬ\tchien\n")
    words = {w["word"]: w for w in vocab.build()["words"]}
    assert (words["犬"]["fr"], words["猫"]["fr"]) == ("chien", "")


@pytest.mark.parametrize("bad", [
    "犬\tいぬ\n",            # no French
    "犬\tいぬ\t \n",          # empty French
    "犬\tいぬ\tchien\textra\n",  # one column too many
])
def test_a_malformed_french_line_stops_the_build(tmp_path, monkeypatch, bad):
    make_lists(tmp_path, monkeypatch, {"N5": [("犬", "いぬ", "dog")]}, fr=bad)
    with pytest.raises(SystemExit, match="fr.tsv line 1"):
        vocab.build()


def test_french_for_a_word_that_is_not_listed_stops_the_build(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [("犬", "いぬ", "dog")]}, fr="猫\tねこ\tchat\n")
    with pytest.raises(SystemExit, match="aren't in the lists"):
        vocab.build()


def test_meanings_are_tidied_and_empty_rows_skipped(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [("犬", "いぬ", "dog,   hound "), ("", "", "nothing")]})
    words = vocab.build()["words"]
    assert [(w["word"], w["en"]) for w in words] == [("犬", "dog, hound")]


def test_without_tatoeba_the_list_order_is_kept(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [("犬", "いぬ", "dog"), ("猫", "ねこ", "cat"), ("鳥", "とり", "bird")]})
    assert [w["word"] for w in vocab.build()["words"]] == ["犬", "猫", "鳥"]


def test_the_credits_name_both_sources():
    assert "open-anki-jlpt-decks" in vocab.SOURCE and "tanos.co.uk" in vocab.SOURCE
    assert "tanos.co.uk" in vocab.SOURCE_FR and "français" in vocab.SOURCE_FR


def test_words_are_found_in_any_form_and_with_their_reading(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [
        ("会う", "あう", "to meet"), ("方", "ほう", "side"), ("方", "かた", "person"),
        ("分かる", "わかる", "to understand"), ("日曜日", "にちようび", "Sunday"), ("すぐに", "すぐに", "at once"),
    ]})
    data = tiny_corpus(("昨日先生に会った。", "I met the teacher yesterday."),
                       ("こっちの方がいい。", "This one is better."),
                       ("よくわかりました。", "I understood well."),
                       ("日曜日に行く。", "I'm going on Sunday."),
                       ("すぐに来て。", "Come at once."))
    out = vocab.build(data)
    shown = {w["id"]: ["".join(f"[{c}]" if a <= i < b else c for i, c in enumerate(out["sentences"][n]["ja"]))
                       for n, a, b in w["ex"]] for w in out["words"]}
    assert shown["会う|あう"] == ["昨日先生に[会][っ]た。"]
    assert shown["方|ほう"] == ["こっちの[方]がいい。"] and shown["方|かた"] == []
    assert shown["分かる|わかる"] == ["よく[わ][か][り]ました。"]
    assert shown["日曜日|にちようび"] == ["[日][曜][日]に行く。"]
    assert shown["すぐに|すぐに"] == ["[す][ぐ][に]来て。"]


def test_particles_and_word_parts_inside_longer_words_are_not_the_word(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [("自転車", "じてんしゃ", "bicycle"), ("大きい", "おおきい", "big")],
                                       "N3": [("より", "より", "twist, ply"), ("自転", "じてん", "rotation")],
                                       "N1": [("問題", "もんだい", "problem")]})
    data = tiny_corpus(("自転車より速い。", "Faster than a bicycle."), ("大問題だ。", "A big problem."))
    ex = {w["word"]: w["ex"] for w in vocab.build(data)["words"]}
    assert len(ex["自転車"]) == 1 and ex["自転"] == [] and ex["より"] == []
    assert len(ex["問題"]) == 1 and ex["大きい"] == []


def test_word_parts_and_lone_kanji_seldom_used_alone_are_left_out(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [("～人", "～じん", "person from"), ("お～", "お～", "honorific"),
                                              ("上", "じょう", "superior"), ("猫", "ねこ", "cat")]})
    monkeypatch.setattr(vocab, "MIN_LONE_KANJI_USES", 5)
    data = tiny_corpus(*[(f"猫が{n}匹いる。", "cats") for n in "一二三四五"])
    assert [w["word"] for w in vocab.build(data)["words"]] == ["猫"]


def test_examples_are_few_easy_and_not_near_copies(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [("猫", "ねこ", "cat")]})
    data = tiny_corpus(("猫がいる。", "There's a cat."), ("猫がいるよ。", "There's a cat!"),
                       ("猫が好き。", "I like cats.", "J'aime les chats."), ("黒い猫だ。", "A black cat."),
                       ("猫は寝ている。", "The cat is sleeping."))
    out = vocab.build(data)
    shown = [out["sentences"][i]["ja"] for i, _, _ in out["words"][0]["ex"]]
    assert len(shown) == vocab.EXAMPLES
    assert not {"猫がいる。", "猫がいるよ。"} <= set(shown)
    liked = next(s for s in out["sentences"] if s["ja"] == "猫が好き。")
    assert (liked["fr"], liked["fr_id"], liked["fr_owner"]) == ("J'aime les chats.", 1003, "quelqu'un")


def test_a_sentence_shared_by_two_words_is_stored_once(tmp_path, monkeypatch):
    make_lists(tmp_path, monkeypatch, {"N5": [("猫", "ねこ", "cat"), ("犬", "いぬ", "dog")]})
    out = vocab.build(tiny_corpus(("猫と犬がいる。", "A cat and a dog.")))
    assert len(out["sentences"]) == 1
    assert [w["ex"] for w in out["words"]] == [[[0, 0, 1]], [[0, 2, 3]]]
