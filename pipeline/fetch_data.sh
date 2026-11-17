#!/bin/bash
# Download the Tatoeba exports used by build.py into data/raw/
set -euo pipefail
cd "$(dirname "$0")/../data" && mkdir -p raw && cd raw
B=https://downloads.tatoeba.org/exports
for f in per_language/jpn/jpn_sentences_detailed.tsv.bz2 per_language/eng/eng_sentences.tsv.bz2 \
         per_language/jpn/jpn-eng_links.tsv.bz2 user_languages.tar.bz2; do
  curl -sSLO "$B/$f"
done
bunzip2 -kf ./*.tsv.bz2
tar xjf user_languages.tar.bz2
