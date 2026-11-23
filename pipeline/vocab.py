"""Build data/build/vocab.json, the vocabulary the app teaches, from the JLPT word lists.

Each word keeps the level of the easiest list it appears in. Within a level, words come in the
order they are best learned: the most used in Tatoeba's Japanese sentences first. Each word gets
a few of those sentences as examples. Word parts (お～, ～人) and lone kanji are left out: they
belong to a kanji section.

    pipeline/.venv/bin/python pipeline/vocab.py
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jp import furigana, has_kanji, kata2hira  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LISTS = Path(__file__).resolve().parent / "vocab"
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "build" / "vocab.json"
LEVELS = ["N5", "N4", "N3", "N2", "N1"]

SOURCE = ("Word lists: open-anki-jlpt-decks (MIT), based on Jonathan Waller's JLPT lists "
          "(tanos.co.uk, CC BY)")
SOURCE_FR = ("Listes de mots : open-anki-jlpt-decks (MIT), d'après les listes JLPT de Jonathan "
             "Waller (tanos.co.uk, CC BY) ; sens en français écrits pour cette appli")

# examples per word
EXAMPLES = 3
# a word of one kanji used on its own fewer times than this in Tatoeba is a kanji, not a word
MIN_LONE_KANJI_USES = 5
GRAMMAR_POS = {"助詞", "助動詞", "補助記号", "空白"}
AFFIX_POS = {"接頭辞", "接尾辞"}

# a note in brackets at the end ("結婚 (する)": a する verb)
SUFFIX = re.compile(r"\s*[（(]([^()（）]*)[)）]\s*$")
KANJI = re.compile(r"[\u4e00-\u9fff々]")


def split_variants(s: str) -> list[str]:
    return [v.strip() for v in re.split(r"[;、]", s) if v.strip()]


def normalise(expression: str, reading: str) -> dict:
    """The word as the app shows it: the first spelling and its reading, other spellings apart,
    and a bracketed note ("する") as a suffix."""
    suffix = ""
    m = SUFFIX.search(expression)
    if m:
        suffix = m.group(1).strip()
        expression = expression[: m.start()]
    m = SUFFIX.search(reading)
    if m:
        suffix = suffix or m.group(1).strip()
        reading = reading[: m.start()]
    # a few rows have the spelling and the reading swapped (いただく, 頂く)
    if KANJI.search(reading) and not KANJI.search(expression):
        expression, reading = reading, expression
    # する verbs written with する in the reading only (運動, うんどうする)
    if reading.endswith("する") and len(reading) > 2 and KANJI.match(expression[-1:]):
        reading, suffix = reading[: -len("する")], suffix or "する"
    spellings, readings = split_variants(expression), split_variants(reading)
    word = spellings[0]
    # readings pair with spellings when there are as many; otherwise the first reading is the word's
    read = readings[0] if readings else word
    also = []
    for i, s in enumerate(spellings[1:], 1):
        r = readings[i] if len(readings) == len(spellings) else ""
        also.append(s if not r or r == s or r == read else f"{s}（{r}）")
    for r in readings[1:]:
        if len(readings) != len(spellings) and r not in also:
            also.append(r)
    return {"word": word, "reading": read, "also": "、".join(also), "suffix": suffix}


def french() -> dict[tuple[str, str], str]:
    path = LISTS / "fr.tsv"
    out = {}
    if not path.exists():
        return out
    for n, line in enumerate(path.read_text(encoding="utf8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3 or not parts[2].strip():
            raise SystemExit(f"fr.tsv line {n}: expected expression, reading, French: {line!r}")
        out[(parts[0], parts[1])] = parts[2].strip()
    return out


def read_lists() -> list[dict]:
    """Every word once, at its easiest level, in list order."""
    seen, words = set(), []
    for level in LEVELS:
        with open(LISTS / f"{level.lower()}.csv", encoding="utf8", newline="") as f:
            for row in csv.DictReader(f):
                key = (row["expression"].strip(), row["reading"].strip())
                if key in seen or not key[0]:
                    continue
                seen.add(key)
                words.append({"key": key, "level": level, "en": " ".join(row["meaning"].split())})
    return words


def corpus():
    """Tatoeba's Japanese sentences with an English translation, their tokens and how hard each
    is (the grammar build's), or None without the raw data (see fetch_data.sh)."""
    if not (RAW / "jpn_sentences_detailed.tsv").exists():
        return None
    import build
    cands = build.load_candidates()
    build.apply_english_fixes(cands)
    toks = build.get_tokens(cands)
    return cands, toks, build.Scorer(cands, toks)


def find_words(words: list[dict], toks: dict) -> dict[int, list[tuple[int, int, int]]]:
    """Where each word is used: word index -> [(sentence id, first char, end char)].
    One token (in any form: 会っ(た) is 会う; in kana when the dictionary writes it in kanji,
    わかる for 分かる) with the word's reading too, so 方 (ほう) isn't 方 (かた). Or a few tokens in
    a row spelling a word no other word is spelled like (日曜+日: the tokenizer reads that 日 ひ).
    Particles, auxiliaries, prefixes and suffixes alone are not words: より or 大 (だい) of 大問題
    never match; but a word may end with one (すぐ+に)."""
    index = collections.defaultdict(set)
    spelled = collections.defaultdict(set)
    for i, w in enumerate(words):
        for spelling in [w["word"]] + [a for a in w["also"].split("、") if a and "（" not in a]:
            index[(spelling, kata2hira(w["reading"]))].add(i)
            spelled[spelling].add(i)
    hits = collections.defaultdict(list)
    for sid, ts in toks.items():
        for i, first in enumerate(ts):
            if first.p1 in GRAMMAR_POS:
                continue
            # the longest word starting here: 自転車, not 自転 (the tokenizer cuts it 自転 + 車)
            surface, longest = "", None
            for j in range(i, min(i + 4, len(ts))):
                t = ts[j]
                if t.p1 == "補助記号":
                    break
                if j == i:
                    if t.p1 in AFFIX_POS:
                        found = set()
                    else:
                        read = kata2hira(t.base_kana)
                        found = index.get((t.base, read), set()) | index.get((t.lemma, read), set())
                else:
                    form = surface + t.base
                    found = spelled[form] if len(spelled.get(form, ())) == 1 else set()
                if found:
                    longest = (found, t.end)
                surface += t.s
            if longest:
                for k in longest[0]:
                    hits[k].append((sid, first.start, longest[1]))
    return hits


def is_whole_word(w: dict, uses: int | None) -> bool:
    """Prefixes and suffixes (お～, ～人) are parts of words, and a lone kanji hardly ever used
    on its own (上 read じょう, 学 がく) is a kanji to learn rather than a word: both are left
    for a kanji section."""
    if "～" in w["word"] or "〜" in w["word"]:
        return False
    # (how much it is used is only known with Tatoeba: `uses` None)
    return uses is None or not (len(w["word"]) == 1 and has_kanji(w["word"]) and uses < MIN_LONE_KANJI_USES)


def similar(a: str, b: str) -> float:
    """How alike two sentences are: the share of their pairs of characters in common."""
    x = {a[i:i + 2] for i in range(len(a) - 1)}
    y = {b[i:i + 2] for i in range(len(b) - 1)}
    return len(x & y) / max(1, len(x | y))


def pick_examples(w: dict, uses: list, cands: dict, scorer, used: collections.Counter) -> list:
    """Up to EXAMPLES of the word's sentences: easy for its level, short, with a French
    translation when there is one, and not already shown for many other words."""
    best = {}
    # sentences easy for the word's level; for a word rare in Tatoeba (傘), harder ones too
    for level in LEVELS[LEVELS.index(w["level"]):]:
        for sid, a, b in uses:
            q = scorer.quality(sid, level)
            if q is None or sid in best:
                continue
            best[sid] = (q - 0.5 * used[sid] - 0.05 * len(cands[sid]["ja"]), sid, a, b)
        if len(best) >= EXAMPLES:
            break
    chosen = []
    for c in sorted(best.values(), reverse=True):
        # not two near copies (ここ座っていいですか？ and ここ座ってもいいですか？)
        if all(similar(cands[c[1]]["ja"], cands[o[1]]["ja"]) <= 0.5 for o in chosen):
            chosen.append(c)
        if len(chosen) == EXAMPLES:
            break
    for _, sid, _, _ in chosen:
        used[sid] += 1
    return [(sid, a, b) for _, sid, a, b in chosen]


def build(data=None) -> dict:
    """The vocabulary; `data` is `corpus()` (None: no frequency order, no examples)."""
    fr = french()
    words = read_lists()
    for w in words:
        w.update(normalise(*w["key"]))
    unknown = set(fr) - {w["key"] for w in words}
    if unknown:
        raise SystemExit(f"fr.tsv has words that aren't in the lists: {sorted(unknown)[:5]}")
    cands, toks, scorer = data or ({}, {}, None)
    hits = find_words(words, toks)
    for i, w in enumerate(words):
        w["uses"] = hits.get(i, [])
    words = [w for w in words if is_whole_word(w, len(w["uses"]) if data else None)]
    order = {level: i for i, level in enumerate(LEVELS)}
    # most used first; sorted() keeps the list order between words used as often
    words.sort(key=lambda w: (order[w["level"]], -len(w["uses"])))
    used, sentences, slot = collections.Counter(), [], {}
    out = []
    for w in words:
        e, r = w["key"]
        ex = []
        if scorer is not None:
            for sid, a, b in pick_examples(w, w["uses"], cands, scorer, used):
                if sid not in slot:
                    slot[sid] = len(sentences)
                    sentences.append(example_sentence(sid, cands[sid], toks[sid]))
                ex.append([slot[sid], a, b])
        out.append({
            "id": f"{e}|{r}", "level": w["level"], "word": w["word"], "reading": w["reading"],
            "also": w["also"], "suffix": w["suffix"], "en": w["en"], "fr": fr.get(w["key"], ""),
            "ex": ex,
        })
    return {"source": SOURCE, "source_fr": SOURCE_FR, "sentences": sentences, "words": out}


def example_sentence(sid: int, c: dict, ts: list) -> dict:
    """An example as the app shows it: with furigana, English, and French when Tatoeba has it."""
    s = {"id": sid, "ja": c["ja"], "en": c["en"], "owner": c["owner"], "furi": furigana(ts)}
    if c.get("en_src"):
        s["en_src"] = c["en_src"]
    if c.get("fr"):
        s["fr"], s["fr_id"], s["fr_owner"] = c["fr"], c["fr_id"], c["fr_owner"]
    return s


def main():
    data = corpus()
    if data is None:
        raise SystemExit("no Tatoeba data: run pipeline/fetch_data.sh first")
    vocab = build(data)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(vocab, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    per_level = {l: sum(1 for w in vocab["words"] if w["level"] == l) for l in LEVELS}
    with_fr = {l: sum(1 for w in vocab["words"] if w["level"] == l and w["fr"]) for l in LEVELS}
    print("wrote", OUT, f"({OUT.stat().st_size // 1024} KB)", per_level, "French:", with_fr)
    no_ex = {l: sum(1 for w in vocab["words"] if w["level"] == l and not w["ex"]) for l in LEVELS}
    fr_ex = sum(1 for s in vocab["sentences"] if "fr" in s)
    print(len(vocab["sentences"]), "example sentences,", fr_ex, "in French; words without:", no_ex)


if __name__ == "__main__":
    main()
