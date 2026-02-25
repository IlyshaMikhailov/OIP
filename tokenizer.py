import os
import re
from collections import defaultdict
import pymorphy3

INPUT_DIR = "web_pages"
TOKENS_DIR = "tokens_pages"
LEMMAS_DIR = "lemmas_pages"

os.makedirs(TOKENS_DIR, exist_ok=True)
os.makedirs(LEMMAS_DIR, exist_ok=True)

morph = pymorphy3.MorphAnalyzer()


STOP_WORDS = set([
    "и","в","не","на","с","что","он","как","а","то","для","это",
    "но","я","она","мы","вы","они","от","до","же","ли","у","о",
    "со","за","над","под","без","про","при","по","или","бы","ещё",
    "её","их","его","меня","тебя","тому","этом","так","та","те",
])

WORD_RE = re.compile(r"[а-яё]+", re.IGNORECASE)

def tokenize_html(raw_text: str):
    raw_text = raw_text.lower()
    words = WORD_RE.findall(raw_text)

    tokens = set()
    for w in words:
        if len(w) < 2:
            continue
        if w in STOP_WORDS:
            continue
        if not re.fullmatch(r"[а-яё]+", w):
            continue
        tokens.add(w)

    return sorted(tokens)

def group_by_lemma(tokens):
    lemma_dict = defaultdict(list)
    for t in tokens:
        lemma = morph.parse(t)[0].normal_form
        lemma_dict[lemma].append(t)

    # сортируем красиво и стабильно
    result = []
    for lemma in sorted(lemma_dict.keys()):
        toks = sorted(set(lemma_dict[lemma]))
        result.append((lemma, toks))
    return result

def main():
    html_files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".html")])
    if not html_files:
        print(f"Нет .html в папке {INPUT_DIR}")
        return

    for fname in html_files:
        src_path = os.path.join(INPUT_DIR, fname)

        with open(src_path, "r", encoding="utf-8") as f:
            html = f.read()

        tokens = tokenize_html(html)

        base = os.path.splitext(fname)[0]  # page_001
        tokens_path = os.path.join(TOKENS_DIR, f"{base}.tokens.txt")
        lemmas_path = os.path.join(LEMMAS_DIR, f"{base}.lemmas.txt")

        with open(tokens_path, "w", encoding="utf-8") as out:
            for t in tokens:
                out.write(t + "\n")

        lemma_groups = group_by_lemma(tokens)
        with open(lemmas_path, "w", encoding="utf-8") as out:
            for lemma, toks in lemma_groups:
                out.write(lemma + " " + " ".join(toks) + "\n")

        print(f"{fname}: tokens={len(tokens)}, lemmas={len(lemma_groups)}")

if __name__ == "__main__":
    main()
