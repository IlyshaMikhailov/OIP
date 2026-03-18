from __future__ import annotations

import html
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from vector_search import VectorSearchEngine, _MORPH  # type: ignore

HOST = "127.0.0.1"
PORT = 8000
TOP_K = 10

engine = VectorSearchEngine()


class SearchHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        query = params.get("q", [""])[0].strip()
        html_page = render_page(query)
        encoded = html_page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="ignore")
        params = parse_qs(body)
        query = params.get("q", [""])[0].strip()
        location = "/?" + urlencode({"q": query})
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        return


def render_page(query: str) -> str:
    results = engine.search_with_meta(query, top_k=TOP_K) if query else []
    lemmas = engine.query_to_lemmas(query) if query else []

    results_block = render_results(query, lemmas, results)
    morph_info = (
        "Лемматизация запросов включена" if _MORPH is not None else "Лемматизация недоступна: поиск работает без pymorphy"
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Векторный поиск по документам</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f5f7fb;
      color: #1f2937;
    }}
    .wrap {{
      max-width: 980px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero {{
      background: #ffffff;
      border-radius: 18px;
      padding: 28px;
      box-shadow: 0 8px 28px rgba(31, 41, 55, 0.08);
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 32px;
      line-height: 1.15;
    }}
    .subtitle {{
      margin: 0;
      color: #4b5563;
      line-height: 1.5;
    }}
    .badge-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }}
    .badge {{
      display: inline-block;
      padding: 8px 12px;
      border-radius: 999px;
      background: #eef2ff;
      color: #3730a3;
      font-size: 14px;
    }}
    .search-box {{
      display: flex;
      gap: 12px;
      margin-top: 22px;
      flex-wrap: wrap;
    }}
    .search-input {{
      flex: 1 1 620px;
      min-width: 260px;
      border: 1px solid #d1d5db;
      border-radius: 14px;
      padding: 16px 18px;
      font-size: 17px;
      outline: none;
      background: #fff;
    }}
    .search-input:focus {{
      border-color: #6366f1;
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.16);
    }}
    .search-button {{
      border: 0;
      border-radius: 14px;
      padding: 16px 22px;
      background: #4f46e5;
      color: #fff;
      font-size: 16px;
      cursor: pointer;
      min-width: 165px;
    }}
    .search-button:hover {{
      background: #4338ca;
    }}
    .panel {{
      background: #ffffff;
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 8px 28px rgba(31, 41, 55, 0.08);
    }}
    .meta {{
      margin-bottom: 18px;
      color: #4b5563;
      line-height: 1.55;
    }}
    .result-card {{
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 18px;
      margin-bottom: 14px;
      background: #fcfcff;
    }}
    .result-card:last-child {{ margin-bottom: 0; }}
    .result-top {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }}
    .rank {{
      color: #6b7280;
      font-size: 14px;
      margin-bottom: 6px;
    }}
    .title {{
      font-size: 20px;
      margin: 0;
      line-height: 1.3;
    }}
    .score {{
      white-space: nowrap;
      font-size: 14px;
      color: #111827;
      background: #eef2ff;
      border-radius: 999px;
      padding: 8px 12px;
    }}
    .link {{
      color: #2563eb;
      word-break: break-all;
      text-decoration: none;
    }}
    .link:hover {{ text-decoration: underline; }}
    .snippet {{
      margin: 10px 0 0;
      color: #374151;
      line-height: 1.6;
    }}
    .empty {{
      color: #4b5563;
      line-height: 1.6;
      padding: 8px 2px;
    }}
    .footer-note {{
      margin-top: 18px;
      color: #6b7280;
      font-size: 14px;
    }}
    code {{
      background: #f3f4f6;
      border-radius: 8px;
      padding: 2px 6px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Векторная поисковая система</h1>
      <p class="subtitle">
        Поиск по корпусу из 100 документов на основе модели TF‑IDF по леммам и косинусной близости.<br>
        Система ранжирует документы по степени релевантности и выводит топ‑10 результатов по запросу.
      </p>
      <div class="badge-row">
        <span class="badge">Ранжирование: cosine similarity</span>
        <span class="badge">Представление: TF‑IDF</span>
        <span class="badge">Вывод: топ {TOP_K}</span>
        <span class="badge">{html.escape(morph_info)}</span>
      </div>
      <form class="search-box" method="post" action="/">
        <input
          class="search-input"
          type="text"
          name="q"
          placeholder="Введите запрос, например: нейтрино энергия"
          value="{html.escape(query)}"
          autofocus
        />
        <button class="search-button" type="submit">Найти</button>
      </form>
    </section>

    <section class="panel">
      {results_block}
      <div class="footer-note">
        Для запуска из проекта: <code>python task5/web_app.py</code>. После запуска откроется адрес <code>http://{HOST}:{PORT}</code>.
      </div>
    </section>
  </div>
</body>
</html>
"""


def render_results(query: str, lemmas: list[str], results: list[dict]) -> str:
    if not query:
        return (
            '<div class="empty">Введите поисковый запрос в строку выше. '
            'Например: <b>магниторецепция черепаха</b>, <b>нейтрино энергия</b>, <b>венера вода</b>.</div>'
        )

    meta = (
        f'<div class="meta">'
        f'Запрос: <b>{html.escape(query)}</b><br>'
        f'Нормализованные леммы: <b>{html.escape(", ".join(lemmas) if lemmas else "—")}</b><br>'
        f'Найдено результатов: <b>{len(results)}</b> (показаны лучшие {TOP_K})'
        f'</div>'
    )

    if not results:
        return meta + '<div class="empty">По запросу ничего не найдено. Попробуй изменить формулировку запроса.</div>'

    cards = []
    for rank, item in enumerate(results, start=1):
        title = html.escape(item["title"] or f"page_{item['doc_id']:03d}")
        url = html.escape(item.get("url", ""))
        snippet = html.escape(item.get("snippet", ""))
        link_html = f'<a class="link" href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>' if url else ''
        cards.append(
            f'''<article class="result-card">
  <div class="result-top">
    <div>
      <div class="rank">#{rank} • Документ page_{item['doc_id']:03d}</div>
      <h2 class="title">{title}</h2>
    </div>
    <div class="score">score = {item['score']:.6f}</div>
  </div>
  {link_html}
  <p class="snippet">{snippet}</p>
</article>'''
        )

    return meta + "\n".join(cards)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), SearchHandler)
    url = f"http://{HOST}:{PORT}"

    print("🌐 Web-интерфейс векторного поиска")
    print("Модель: TF-IDF по леммам + cosine similarity")
    print(f"Сервер запущен: {url}")
    print("Для остановки нажмите Ctrl+C")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
