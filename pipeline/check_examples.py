"""Run every N4–N1 point's matcher on its own example sentence; print the ones that don't match."""
import sys
from jp import tokenize
import grammar_n4, grammar_n3, grammar_n2, grammar_n1  # noqa: F401  (register points)
from patterns import POINTS

bad = 0
for p in POINTS:
    if len(sys.argv) > 1 and p["level"] not in sys.argv[1:]:
        continue
    toks = tokenize(p["ex"])
    m = p["match"](toks)
    if not m:
        bad += 1
        print(f"{p['level']} {p['id']:24} NO MATCH  {p['ex']}  {[(t.s, t.p1, t.p2, t.lemma, t.cf) for t in toks]}")
print(f"{bad} without match")
