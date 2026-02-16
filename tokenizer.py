import os
import re
from collections import defaultdict
import pymorphy2

input_dir = "web_pages"

tokens_file = "tokens.txt"
lemmas_file = "lemmas.txt"

morph = pymorphy2.MorphAnalyzer()

STOP_WORDS = set([
    "и","в","не","на","с","что","он","как","а","то","для","это",
    "но","я","она","мы","вы","они","от","до","же","ли","у","о",
    "со","за","над","под","без","про","при","по","или","бы","ещё",
    "её","их","его","меня","тебя","тому","этом","так","та","те"
])


word_pattern = re.compile(r'\b[а-яА-ЯёЁ]+\b')

tokens_set = set()

for filename in os.listdir(input_dir):
    if filename.endswith(".html"):
        path = os.path.join(input_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()
            words = word_pattern.findall(text)
            for w in words:
                if w in STOP_WORDS:
                    continue
                tokens_set.add(w)

tokens = sorted(tokens_set)
with open(tokens_file, "w", encoding="utf-8") as f:
    for t in tokens:
        f.write(t + "\n")

lemma_dict = defaultdict(list)

for token in tokens:
    lemma = morph.parse(token)[0].normal_form
    lemma_dict[lemma].append(token)

with open(lemmas_file, "w", encoding="utf-8") as f:
    for lemma, token_list in lemma_dict.items():
        line = lemma + " " + " ".join(sorted(token_list)) + "\n"
        f.write(line)

print(f"Уникальные токены: {len(tokens)}, лемм: {len(lemma_dict)}")
