"""French content written for this app: grammar point texts (points_n*.py) and translations of
example sentences that have no French translation on Tatoeba (sentences_n*.tsv)."""
from __future__ import annotations

import importlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEVELS = ["N5", "N4", "N3", "N2", "N1"]


def point_texts() -> dict[str, dict]:
    """id -> {title?, meaning, structure, explanation} (title only where it differs from the original)."""
    out = {}
    for lv in LEVELS:
        try:
            mod = importlib.import_module(f"fr.points_{lv.lower()}")
        except ModuleNotFoundError:
            continue
        for pid, d in mod.FR.items():
            assert pid not in out, f"duplicate French text for {pid}"
            out[pid] = d
    return out


def sentence_translations() -> dict[int, tuple[str, str]]:
    """sentence id -> (Japanese text it was translated from, French)."""
    out = {}
    for f in sorted(HERE.glob("sentences_*.tsv")):
        for n, line in enumerate(open(f, encoding="utf8"), 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            sid, ja, fr = line.split("\t")
            assert fr.strip(), f"{f.name}:{n}: empty translation"
            out[int(sid)] = (ja, fr.strip())
    return out
