#!/usr/bin/env python3
"""Write a progress file for the emulator tests: some points learned today, reviews due now, a
leech (3 wrong among its last reviews), a sentence report, and the UI language.

    make_progress.py OUT.json [en|fr] [--due N] [--learned N]
"""
import argparse
import json
import time
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[2] / "data" / "build" / "content.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("lang", nargs="?", default="en")
    ap.add_argument("--due", type=int, default=6, help="reviews due now")
    ap.add_argument("--learned", type=int, default=8, help="points learned (due ones included)")
    args = ap.parse_args()
    content = json.loads(CONTENT.read_text(encoding="utf8"))
    now = int(time.time() * 1000)
    hour = 3_600_000
    ids = [p["id"] for p in content["points"] if p["level"] == "N5"][: args.learned]
    cards, log = {}, []
    for i, pid in enumerate(ids):
        due = now - 60_000 if i < args.due else now + 30 * hour
        cards[pid] = dict(state=1, stability=1.0, difficulty=5.0, due=due, last_review=now - 5 * hour,
                          reps=2, lapses=0, step=1, last_sentence=0, learned_at=now - 6 * hour)
        log.append(dict(point=pid, sentence=0, ts=now - 6 * hour, grade=3, answer=""))
    # the last learned point is a leech: 3 wrong among its last 5 reviews
    leech = ids[-1]
    for k, grade in enumerate([1, 3, 1, 1]):
        log.append(dict(point=leech, sentence=0, ts=now - (5 - k) * hour, grade=grade, answer="x"))
    first = content["points"][0]
    report = dict(point=first["id"], sentence=first["sentences"][0]["id"], ts=now - hour,
                  reason="translation", note="e2e test", answer="", lang=args.lang)
    progress = dict(cards=cards, settings=dict(language=args.lang), log=log, reports=[report])
    Path(args.out).write_text(json.dumps(progress, ensure_ascii=False), encoding="utf8")


if __name__ == "__main__":
    main()
