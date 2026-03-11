import os
import json
import re
from collections import defaultdict

LEMMAS_DIR = "../../task2/ouput/lemmas_pages"
OUT_INDEX_JSON = "../data/inverted_index.json"
OUT_INDEX_TXT = "../data/inverted_index.txt"

DOCNUM_RE = re.compile(r"(\d+)")

def extract_doc_num(fname: str) -> int:
    """page_001.lemmas.txt -> 1"""
    m = DOCNUM_RE.search(fname)
    if not m:
        raise ValueError(f"Не могу извлечь номер документа: {fname}")
    return int(m.group(1))

def parse_lemma_line(line: str):
    parts = line.strip().split()
    if len(parts) < 1:
        return None
    lemma = parts[0]
    forms = parts[1:]  # не используем, но для полноты
    return lemma, forms

def main():
    index = defaultdict(set)  # lemma -> set(doc_num)

    files = sorted([f for f in os.listdir(LEMMAS_DIR) if f.endswith(".lemmas.txt")])
    if not files:
        raise SystemExit(f"Нет *.lemmas.txt в папке {LEMMAS_DIR}")

    for fname in files:
        doc_num = extract_doc_num(fname)
        path = os.path.join(LEMMAS_DIR, fname)

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parsed = parse_lemma_line(line)
                if not parsed:
                    continue
                lemma, _ = parsed
                index[lemma].add(doc_num)

    # JSON: {"лемма": [1, 5, 10], ...}
    index_json = {lemma: sorted(index[lemma]) for lemma in sorted(index.keys())}

    with open(OUT_INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(index_json, f, ensure_ascii=False, indent=2, sort_keys=True)

    # TXT: "лемма: 1 5 10"
    with open(OUT_INDEX_TXT, "w", encoding="utf-8") as f:
        for lemma in sorted(index.keys()):
            nums = sorted(index[lemma])
            f.write(f"{lemma}: " + " ".join(map(str, nums)) + "\n")

    doc_count = len(files)
    print(f"Готово: лемм={len(index_json)}, документов={doc_count}")
    print(f"Файлы: {OUT_INDEX_JSON}, {OUT_INDEX_TXT}")

if __name__ == "__main__":
    main()
