"""French content: every grammar point has French text, translation files are well formed."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import fr  # noqa: E402
import grammar_n1  # noqa: E402,F401
import grammar_n2  # noqa: E402,F401
import grammar_n3  # noqa: E402,F401
import grammar_n4  # noqa: E402,F401
import grammar_n5  # noqa: E402
from patterns import POINTS  # noqa: E402

ALL_IDS = {p["id"] for p in grammar_n5.POINTS} | {p["id"] for p in POINTS}
TEXTS = fr.point_texts()


def test_every_point_has_french_text():
    assert sorted(ALL_IDS - set(TEXTS)) == []


def test_no_french_text_for_unknown_points():
    assert sorted(set(TEXTS) - ALL_IDS) == []


def test_french_texts_are_complete():
    for pid, t in TEXTS.items():
        assert t["meaning"].strip() and t["structure"].strip(), pid
        assert len(t["explanation"]) > 60, f"{pid}: explanation too short"
        assert re.search(r"[぀-ヿ一-鿿]", t["explanation"]), f"{pid}: no Japanese example"


def test_french_typography():
    # the build turns " :" into a no-break space; a plain space must never remain before : ; ! ?
    for pid, t in TEXTS.items():
        for field, text in t.items():
            assert not re.search(r" [:;!?]", text), f"{pid}.{field}: plain space before punctuation"
    assert fr.typo("C'est « bon » : oui !") == "C'est « bon » : oui !"


def test_sentence_translation_files():
    rows = fr.sentence_translations()
    assert len(rows) > 2000
    for sid, (ja, text) in rows.items():
        assert ja.endswith(("。", "？", "！", "?", "!")), (sid, ja)
        assert text and not re.search(r"[぀-ヿ]", text), f"{sid}: French contains kana"
        assert text[-1] in ".!?…»", f"{sid}: no final punctuation: {text}"
