import os
import re
import json
from collections import defaultdict

TOKENS_DIR = "tokens_pages"
OUT_INDEX_JSON = "inverted_index.json"
OUT_INDEX_TXT = "inverted_index.txt"

DOCNUM_RE = re.compile(r"(\d+)")  # достанем 001 из page_001.tokens.txt

def extract_doc_num(fname: str) -> int:
    """
    Ожидаем имена вида page_001.tokens.txt (или любые, где есть число).
    Вернём int: 1..100
    """
    m = DOCNUM_RE.search(fname)
    if not m:
        raise ValueError(f"Не могу извлечь номер документа из имени файла: {fname}")
    return int(m.group(1))

def main():
    index = defaultdict(set)  # term -> set(int docNum)

    files = sorted([f for f in os.listdir(TOKENS_DIR) if f.endswith(".tokens.txt")])
    if not files:
        raise SystemExit(f"Нет файлов *.tokens.txt в папке {TOKENS_DIR}")

    for fname in files:
        doc_num = extract_doc_num(fname)
        path = os.path.join(TOKENS_DIR, fname)

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                term = line.strip()
                if not term:
                    continue
                index[term].add(doc_num)

    # JSON: ключи-термины, значения — отсортированные списки int
    index_json = {term: sorted(index[term]) for term in index}

    with open(OUT_INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(index_json, f, ensure_ascii=False, indent=2, sort_keys=True)

    # TXT (не обязателен): "term: 1 5 10"
    with open(OUT_INDEX_TXT, "w", encoding="utf-8") as f:
        for term in sorted(index.keys()):
            nums = sorted(index[term])
            f.write(f"{term}: " + " ".join(map(str, nums)) + "\n")

    doc_count = len({extract_doc_num(x) for x in files})
    print(f"Готово: терминов={len(index_json)}, документов={doc_count}")
    print(f"Файлы: {OUT_INDEX_JSON}, {OUT_INDEX_TXT}")

if __name__ == "__main__":
    main()
