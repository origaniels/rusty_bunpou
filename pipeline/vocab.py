"""Build data/build/vocab.json, the vocabulary the app teaches, from the JLPT word lists.

Each word keeps the level of the easiest list it appears in. Within a level, words come in the
order they are best learned: the most frequent in Tatoeba's Japanese sentences first.

    pipeline/.venv/bin/python pipeline/vocab.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISTS = Path(__file__).resolve().parent / "vocab"
SENTENCES = ROOT / "data" / "raw" / "jpn_sentences_detailed.tsv"
OUT = ROOT / "data" / "build" / "vocab.json"
LEVELS = ["N5", "N4", "N3", "N2", "N1"]

SOURCE = ("Word lists: open-anki-jlpt-decks (MIT), based on Jonathan Waller's JLPT lists "
          "(tanos.co.uk, CC BY)")
SOURCE_FR = ("Listes de mots : open-anki-jlpt-decks (MIT), d'après les listes JLPT de Jonathan "
             "Waller (tanos.co.uk, CC BY) ; sens en français écrits pour cette appli")

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


def frequencies(words: list[dict]) -> dict[str, int]:
    """How many Tatoeba sentences contain each word (its first spelling, without ～)."""
    if not SENTENCES.exists():
        return {}
    text = "\n".join(line.split("\t")[2] for line in SENTENCES.read_text(encoding="utf8").splitlines()
                     if line.count("\t") >= 2)
    out = {}
    for w in words:
        form = w["word"].replace("～", "")
        if form and form not in out:
            out[form] = text.count(form)
    return out


def build() -> dict:
    fr = french()
    words = read_lists()
    for w in words:
        w.update(normalise(*w["key"]))
    unknown = set(fr) - {w["key"] for w in words}
    if unknown:
        raise SystemExit(f"fr.tsv has words that aren't in the lists: {sorted(unknown)[:5]}")
    freq = frequencies(words)
    order = {level: i for i, level in enumerate(LEVELS)}
    words.sort(key=lambda w: (order[w["level"]], -freq.get(w["word"].replace("～", ""), 0)))
    out = []
    for w in words:
        e, r = w["key"]
        out.append({
            "id": f"{e}|{r}", "level": w["level"], "word": w["word"], "reading": w["reading"],
            "also": w["also"], "suffix": w["suffix"], "en": w["en"], "fr": fr.get(w["key"], ""),
        })
    return {"source": SOURCE, "source_fr": SOURCE_FR, "words": out}


def main():
    vocab = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(vocab, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    per_level = {l: sum(1 for w in vocab["words"] if w["level"] == l) for l in LEVELS}
    with_fr = {l: sum(1 for w in vocab["words"] if w["level"] == l and w["fr"]) for l in LEVELS}
    print("wrote", OUT, f"({OUT.stat().st_size // 1024} KB)", per_level, "French:", with_fr)


if __name__ == "__main__":
    main()
