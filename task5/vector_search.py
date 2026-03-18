from __future__ import annotations

import html
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

# Опциональная морфология: сначала pymorphy3, потом pymorphy2, иначе fallback без лемматизации
try:
    import pymorphy3  # type: ignore
    _MORPH = pymorphy3.MorphAnalyzer()
except Exception:
    try:
        import pymorphy2  # type: ignore
        _MORPH = pymorphy2.MorphAnalyzer()
    except Exception:
        _MORPH = None

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_PATH = BASE_DIR / "task3" / "output" / "inverted_index.json"
TFIDF_DIR = BASE_DIR / "task4" / "output" / "tfidf_lemmas"
PAGES_DIR = BASE_DIR / "task1" / "pages"
DOC_INDEX_PATH = BASE_DIR / "task1" / "data" / "index.txt"

WORD_RE = re.compile(r"[a-zа-яё]+", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


class VectorSearchEngine:
    def __init__(self) -> None:
        self.index = self._load_index(INDEX_PATH)
        self.doc_urls = self._load_doc_urls(DOC_INDEX_PATH)
        self.doc_vectors, self.idf = self._load_all_doc_vectors(TFIDF_DIR)

    @staticmethod
    def _load_index(path: Path) -> Dict[str, set[int]]:
        if not path.exists():
            raise FileNotFoundError(f"Не найден файл индекса: {path}")
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return {lemma: set(map(int, docs)) for lemma, docs in raw.items()}

    @staticmethod
    def _load_doc_urls(path: Path) -> Dict[int, str]:
        urls: Dict[int, str] = {}
        if not path.exists():
            return urls
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) != 2:
                    continue
                doc_id, url = parts
                try:
                    urls[int(doc_id)] = url
                except ValueError:
                    continue
        return urls

    @staticmethod
    def _load_all_doc_vectors(tfidf_dir: Path) -> Tuple[Dict[int, Dict[str, float]], Dict[str, float]]:
        if not tfidf_dir.exists():
            raise FileNotFoundError(f"Не найдена папка TF-IDF: {tfidf_dir}")

        doc_vectors: Dict[int, Dict[str, float]] = {}
        idf: Dict[str, float] = {}

        for path in sorted(tfidf_dir.glob("page_*.txt")):
            match = re.search(r"(\d+)", path.name)
            if not match:
                continue
            doc_id = int(match.group(1))
            vector: Dict[str, float] = {}

            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 3:
                        continue
                    lemma, idf_str, tfidf_str = parts
                    try:
                        term_idf = float(idf_str)
                        term_tfidf = float(tfidf_str)
                    except ValueError:
                        continue

                    idf.setdefault(lemma, term_idf)
                    if term_tfidf != 0.0:
                        vector[lemma] = term_tfidf

            doc_vectors[doc_id] = vector

        if not doc_vectors:
            raise ValueError("В папке TF-IDF не найдено ни одного векторного файла")

        return doc_vectors, idf

    @staticmethod
    def _normalize_word(token: str) -> str:
        token = token.lower().strip()
        if not token:
            return token
        if _MORPH is None:
            return token
        try:
            return _MORPH.parse(token)[0].normal_form
        except Exception:
            return token

    def query_to_lemmas(self, query: str) -> List[str]:
        tokens = WORD_RE.findall(query.lower())
        lemmas = [self._normalize_word(token) for token in tokens if len(token) >= 2]
        return lemmas

    @staticmethod
    def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        common = set(vec1.keys()) & set(vec2.keys())
        dot = sum(vec1[k] * vec2[k] for k in common)
        norm1 = math.sqrt(sum(v * v for v in vec1.values()))
        norm2 = math.sqrt(sum(v * v for v in vec2.values()))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot / (norm1 * norm2)

    def build_query_vector(self, lemmas: List[str]) -> Dict[str, float]:
        counts = Counter(lemma for lemma in lemmas if lemma in self.index)
        if not counts:
            return {}

        total = sum(counts.values())
        qvec = {
            lemma: (count / total) * self.idf.get(lemma, 0.0)
            for lemma, count in counts.items()
        }

        # fallback: если все веса обнулились из-за idf=0 (часто бывает из-за общего HTML-шаблона сайта),
        # оставляем бинарные веса, чтобы поиск всё равно работал
        if not any(weight > 0 for weight in qvec.values()):
            return {lemma: 1.0 for lemma in counts}

        return {lemma: weight for lemma, weight in qvec.items() if weight > 0}

    def candidate_docs(self, lemmas: List[str]) -> set[int]:
        candidates: set[int] = set()
        for lemma in lemmas:
            candidates |= self.index.get(lemma, set())
        return candidates

    @staticmethod
    def _read_page(doc_id: int) -> str:
        path = PAGES_DIR / f"page_{doc_id}.html"
        if not path.exists():
            path = PAGES_DIR / f"page_{doc_id:03d}.html"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")

    @classmethod
    def get_title(cls, doc_id: int) -> str:
        raw = cls._read_page(doc_id)
        if not raw:
            return f"page_{doc_id:03d}"
        match = TITLE_RE.search(raw)
        if not match:
            return f"page_{doc_id:03d}"
        title = html.unescape(match.group(1))
        title = SPACE_RE.sub(" ", title).strip()
        return title

    @classmethod
    def get_snippet(cls, doc_id: int, max_len: int = 180) -> str:
        raw = cls._read_page(doc_id)
        if not raw:
            return ""
        raw = SCRIPT_STYLE_RE.sub(" ", raw)
        text = TAG_RE.sub(" ", raw)
        text = html.unescape(text)
        text = SPACE_RE.sub(" ", text).strip()
        if len(text) <= max_len:
            return text
        return text[: max_len - 1].rstrip() + "…"

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        lemmas = self.query_to_lemmas(query)
        if not lemmas:
            return []

        qvec = self.build_query_vector(lemmas)
        if not qvec:
            return []

        candidates = self.candidate_docs(list(qvec.keys()))
        results: List[Tuple[int, float]] = []

        for doc_id in candidates:
            dvec = self.doc_vectors.get(doc_id, {})
            score = self.cosine_similarity(qvec, dvec)
            if score > 0:
                results.append((doc_id, score))

        results.sort(key=lambda item: (-item[1], item[0]))
        return results[:top_k]

    def search_with_meta(self, query: str, top_k: int = 10) -> List[dict]:
        results = self.search(query, top_k=top_k)
        enriched = []
        for doc_id, score in results:
            enriched.append(
                {
                    "doc_id": doc_id,
                    "score": score,
                    "title": self.get_title(doc_id),
                    "url": self.doc_urls.get(doc_id, ""),
                    "snippet": self.get_snippet(doc_id),
                }
            )
        return enriched


def main() -> None:
    try:
        engine = VectorSearchEngine()
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("Проверь наличие файлов:")
        print(f"  - {INDEX_PATH}")
        print(f"  - {TFIDF_DIR}")
        return

    print("🔍 Векторный поиск по документам")
    print("Модель: TF-IDF по леммам + cosine similarity")
    if _MORPH is None:
        print("⚠️ pymorphy не найден: запросы будут искаться без лемматизации")
    print("Пустая строка завершает программу.\n")

    while True:
        query = input("query> ").strip()
        if not query:
            break

        lemmas = engine.query_to_lemmas(query)
        print(f"Нормализованный запрос: {', '.join(lemmas) if lemmas else '—'}")

        results = engine.search_with_meta(query, top_k=10)
        print("-" * 100)
        if not results:
            print("Ничего не найдено.\n")
            continue

        for rank, item in enumerate(results, start=1):
            print(f"{rank:2d}. page_{item['doc_id']:03d} | score={item['score']:.6f}")
            print(f"    {item['title']}")
            if item["url"]:
                print(f"    {item['url']}")
            if item["snippet"]:
                print(f"    {item['snippet']}")
            print()


if __name__ == "__main__":
    main()
