# 🕷️ OIP

###  **Авторы**
**Михайлов Илья** & **Ефремов Кирилл**  
**Группа:** 11-203

---
###  Установка
```bash
# 1. Клонировать репозиторий
git clone https://github.com/IlyshaMikhailov/OIP.git
cd OIP

# 2. Создать виртуальное окружение (Python 3.10)
python3.10 -m venv .venv310

# 3. Активировать окружение
# Windows:
.venv310\Scripts\activate
# Linux/Mac:
source .venv310/bin/activate

# 4. Установить зависимости
pip install -r requirements.txt
```
---
## ️Task 1 — Краулер (`task1`)

**Вход:**  
`links.txt`

**Выход:**  
`task1/output/pages/page_XXX.html`, `index.txt`

**Запуск:**
```bash
cd task1/crawler
python crawler.py
```
---
## Task 2 — Токенизация и лемматизация 
**Вход:**
task1/output/pages/

**Выход:**

Токены: task2/output/tokens/

Леммы: task2/output/lemmas/

**Запуск:**

```bash
cd task2/tokenizer
python tokenizer.py
```
---
## Task 3 — Инвертированный индекс и булев поиск
**Вход:**
task2/output/lemmas/

**Выход:**
task3/output/inverted_index.json, task3/output/inverted_index.txt

**Запуск (построение индекса):**

```bash
  cd task3/index
  python build_index.py
```
**Запуск (булев поиск):**

```bash
cd task3/search
python boolean_search.py
```
---
## Task 4 — TF‑IDF 
**Вход:**
task1/output/pages/, task2/output/tokens/, task2/output/lemmas/

**Выход:**
task4/output/tfidf_terms/, task4/output/tfidf_lemmas/

**Запуск:**

```bash
cd task4/tfidf
python tfidf.py
```