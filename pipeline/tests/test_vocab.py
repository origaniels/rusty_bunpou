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
