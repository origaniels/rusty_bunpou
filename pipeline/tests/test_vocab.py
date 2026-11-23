"""The vocabulary built from the JLPT word lists (see pipeline/vocab/README.md)."""
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vocab  # noqa: E402

BUILT = Path(__file__).resolve().parents[2] / "data" / "build" / "vocab.json"
KANJI = re.compile(r"[一-鿿々]")


@pytest.fixture(scope="module")
def words():
    return json.loads(BUILT.read_text(encoding="utf8"))["words"]


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
    assert words == vocab.build()["words"], "run pipeline/vocab.py"


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
    monkeypatch.setattr(vocab, "SENTENCES", tmp_path / "no-sentences.tsv")


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
    (tmp_path / "sents.tsv").write_text(
        "1\tjpn\t猫がいる。\tx\n2\tjpn\t猫と犬。\tx\n3\tjpn\t猫だ。\tx\n4\tjpn\t走る犬\tx\n", encoding="utf8")
    monkeypatch.setattr(vocab, "SENTENCES", tmp_path / "sents.tsv")
    assert [w["word"] for w in vocab.build()["words"]] == ["猫", "犬", "走る"]


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
