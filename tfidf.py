import os
import re
import math
from collections import Counter, defaultdict
import pymorphy3

INPUT_DIR = "web_pages"

OUT_TERMS_DIR = "tfidf_terms"
OUT_LEMMAS_DIR = "tfidf_lemmas"

os.makedirs(OUT_TERMS_DIR, exist_ok=True)
os.makedirs(OUT_LEMMAS_DIR, exist_ok=True)

morph = pymorphy3.MorphAnalyzer()

STOP_WORDS = set([
    "и","в","не","на","с","что","он","как","а","то","для","это",
    "но","я","она","мы","вы","они","от","до","же","ли","у","о",
    "со","за","над","под","без","про","при","по","или","бы","ещё",
    "её","их","его","меня","тебя","тому","этом","так","та","те"
])

WORD_RE = re.compile(r"[а-яё]+", re.IGNORECASE)
DOCNUM_RE = re.compile(r"(\d+)")  # page_001.html -> 001

def doc_num_from_filename(fname: str) -> int:
    m = DOCNUM_RE.search(fname)
    if not m:
        raise ValueError(f"Не могу извлечь номер документа из имени: {fname}")
    return int(m.group(1))

def tokenize(text: str):
    words = WORD_RE.findall(text.lower())
    tokens = []
    for w in words:
        if len(w) < 2:
            continue
        if w in STOP_WORDS:
            continue
        if not re.fullmatch(r"[а-яё]+", w):
            continue
        tokens.append(w)
    return tokens  # ВАЖНО: со всеми повторами (для tf)

def compute_idf(df: dict, n_docs: int):
    # idf(t) = log(N/df(t))
    return {term: math.log(n_docs / df_val) for term, df_val in df.items()}  # [web:184]

def write_tfidf_file(path, tf_counts: Counter, doc_len: int, idf: dict):
    # формат: <term> <idf> <tf-idf>\n
    # tf = count/len(doc) (как в определении относительной частоты) [web:180]
    with open(path, "w", encoding="utf-8") as f:
        for term in sorted(tf_counts.keys()):
            tf = tf_counts[term] / doc_len if doc_len else 0.0
            term_idf = idf.get(term, 0.0)
            tfidf = tf * term_idf
            f.write(f"{term} {term_idf:.6f} {tfidf:.6f}\n")

def main():
    html_files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".html")])
    if not html_files:
        raise SystemExit(f"Нет .html в папке {INPUT_DIR}")

    # 1) Собираем токены/леммы по всем документам
    doc_tokens = {}          # doc_num -> list[str] (с повторами)
    doc_term_counts = {}     # doc_num -> Counter(token)
    doc_lemma_counts = {}    # doc_num -> Counter(lemma) (по сумме вхождений токенов)
    df_terms = defaultdict(int)   # term -> document frequency
    df_lemmas = defaultdict(int)  # lemma -> document frequency

    for fname in html_files:
        doc_num = doc_num_from_filename(fname)
        with open(os.path.join(INPUT_DIR, fname), "r", encoding="utf-8") as f:
            html = f.read()

        tokens = tokenize(html)
        doc_tokens[doc_num] = tokens

        term_counts = Counter(tokens)
        doc_term_counts[doc_num] = term_counts

        # df по терминам (учитываем наличие в документе 1 раз)
        for term in term_counts.keys():
            df_terms[term] += 1

        # Леммы: считаем по вхождениям токенов этой леммы
        lemma_counts = Counter()
        for tok, c in term_counts.items():
            lemma = morph.parse(tok)[0].normal_form
            lemma_counts[lemma] += c
        doc_lemma_counts[doc_num] = lemma_counts

        for lemma in lemma_counts.keys():
            df_lemmas[lemma] += 1

    n_docs = len(doc_tokens)

    # 2) IDF для всех терминов/лемм
    idf_terms = compute_idf(df_terms, n_docs)
    idf_lemmas = compute_idf(df_lemmas, n_docs)

    # 3) Пишем по файлу на документ
    for doc_num in sorted(doc_tokens.keys()):
        tokens = doc_tokens[doc_num]
        doc_len = len(tokens)

        # A) термины
        out_terms = os.path.join(OUT_TERMS_DIR, f"page_{doc_num:03d}.txt")
        write_tfidf_file(out_terms, doc_term_counts[doc_num], doc_len, idf_terms)

        # B) леммы (tf = lemma_count / total_terms_in_doc)
        out_lemmas = os.path.join(OUT_LEMMAS_DIR, f"page_{doc_num:03d}.txt")
        write_tfidf_file(out_lemmas, doc_lemma_counts[doc_num], doc_len, idf_lemmas)

    print(f"Готово. Документов: {n_docs}")
    print(f"TF-IDF terms:  {OUT_TERMS_DIR}/page_XXX.txt")
    print(f"TF-IDF lemmas: {OUT_LEMMAS_DIR}/page_XXX.txt")

if __name__ == "__main__":
    main()
