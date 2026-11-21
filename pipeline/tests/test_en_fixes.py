"""English translations written for the app replace Tatoeba's (see en_fixes.tsv)."""
import pytest

import build


def test_the_fixes_file_is_well_formed():
    fixes = build.english_fixes()
    assert fixes
    for sid, (ja, en) in fixes.items():
        assert sid > 0 and ja.endswith(("。", "？", "！")) and en.strip() == en and en


def test_a_fix_replaces_the_english_and_is_marked():
    sid, (ja, en) = next(iter(build.english_fixes().items()))
    cands = {sid: dict(ja=ja, en="old", owner="x")}
    build.apply_english_fixes(cands)
    assert cands[sid]["en"] == en and cands[sid]["en_src"] == "app"


def test_a_fix_for_a_changed_sentence_stops_the_build():
    sid, (ja, _) = next(iter(build.english_fixes().items()))
    with pytest.raises(SystemExit):
        build.apply_english_fixes({sid: dict(ja=ja + "x", en="old", owner="x")})
