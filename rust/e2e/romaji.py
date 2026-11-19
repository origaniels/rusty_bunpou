#!/usr/bin/env python3
"""Keys to type a hiragana word on a romaji keyboard (Gboard's Japanese QWERTY), or nothing if the
word has other characters.   romaji.py だった -> datta"""
import sys

BASE = dict(zip(
    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
    "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉ",
    "a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi fu he ho "
    "ma mi mu me mo ya yu yo ra ri ru re ro wa wo nn ga gi gu ge go za ji zu ze zo da di du de do "
    "ba bi bu be bo pa pi pu pe po xa xi xu xe xo".split()))
SMALL = {"ゃ": "ya", "ゅ": "yu", "ょ": "yo"}


def romaji(word: str) -> str:
    out, i = [], 0
    while i < len(word):
        c = word[i]
        nxt = word[i + 1] if i + 1 < len(word) else ""
        if c == "っ":
            r = romaji(nxt)  # double the next consonant
            if not r or r[0] in "aiueon":
                return ""
            out.append(r[0])
        elif nxt in SMALL and c in BASE:
            stem = BASE[c][:-1]  # き → k, し → sh, じ → j
            out.append(stem + (SMALL[nxt][1:] if stem in ("sh", "ch", "j") else SMALL[nxt]))
            i += 1
        elif c in BASE:
            out.append(BASE[c])
        elif c == "ー":
            out.append("-")
        else:
            return ""
        i += 1
    return "".join(out)


if __name__ == "__main__":
    print(romaji(sys.argv[1]))
