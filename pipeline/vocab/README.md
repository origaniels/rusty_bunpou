# JLPT word lists

`n1.csv` … `n5.csv` come from open-anki-jlpt-decks (github.com/jamsinclair/open-anki-jlpt-decks,
commit 1ad66734417a, MIT licence, see `LICENSE-word-lists`). Those lists are based on Jonathan
Waller's JLPT lists (tanos.co.uk, Creative Commons BY). The app credits both.

`fr.tsv`: French meanings, written for this app (`expression<TAB>reading<TAB>French`, keyed like
the CSV rows). Levels without French show the English meaning.

`../vocab.py` turns them into `data/build/vocab.json`.
