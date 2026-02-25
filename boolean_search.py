import json
import re

INDEX_JSON = "inverted_index.json"

OPS = {"AND", "OR", "NOT"}
PRECEDENCE = {"NOT": 3, "AND": 2, "OR": 1}
ASSOC = {"NOT": "right", "AND": "left", "OR": "left"}

TOKEN_RE = re.compile(r"\s*(\(|\)|AND|OR|NOT|[A-Za-zА-Яа-яЁё0-9_-]+)\s*", re.IGNORECASE)

def load_index(path=INDEX_JSON):
    with open(path, "r", encoding="utf-8") as f:
        idx = json.load(f)
    index = {term: set(docs) for term, docs in idx.items()}
    all_docs = set()
    for docs in index.values():
        all_docs |= docs
    return index, all_docs

def tokenize_query(q: str):
    raw = TOKEN_RE.findall(q)
    if not raw:
        return []
    tokens = []
    for t in raw:
        up = t.upper()
        if up in OPS:
            tokens.append(up)
        elif t in ("(", ")"):
            tokens.append(t)
        else:
            tokens.append(t.lower())
    return tokens

def to_rpn(tokens):
    out = []
    stack = []

    for tok in tokens:
        if tok == "(":
            stack.append(tok)
        elif tok == ")":
            while stack and stack[-1] != "(":
                out.append(stack.pop())
            if not stack or stack[-1] != "(":
                raise ValueError("Несогласованные скобки")
            stack.pop()
        elif tok in OPS:
            while stack and stack[-1] in OPS:
                top = stack[-1]
                if (ASSOC[tok] == "left" and PRECEDENCE[tok] <= PRECEDENCE[top]) or \
                   (ASSOC[tok] == "right" and PRECEDENCE[tok] < PRECEDENCE[top]):
                    out.append(stack.pop())
                else:
                    break
            stack.append(tok)
        else:
            out.append(tok)

    while stack:
        if stack[-1] in ("(", ")"):
            raise ValueError("Несогласованные скобки")
        out.append(stack.pop())

    return out

def eval_rpn(rpn, index, all_docs):
    st = []
    for tok in rpn:
        if tok == "AND":
            b = st.pop(); a = st.pop()
            st.append(a & b)
        elif tok == "OR":
            b = st.pop(); a = st.pop()
            st.append(a | b)
        elif tok == "NOT":
            a = st.pop()
            st.append(all_docs - a)
        else:
            st.append(index.get(tok, set()))
    if len(st) != 1:
        raise ValueError("Некорректный запрос")
    return st[0]

def search(query: str, index, all_docs):
    tokens = tokenize_query(query)
    if not tokens:
        return set()
    rpn = to_rpn(tokens)
    return eval_rpn(rpn, index, all_docs)

def main():
    index, all_docs = load_index()

    print("Булев поиск. Операторы: AND OR NOT, скобки ().")
    print("Пример: (клеопатра AND цезарь) OR (антоний AND цицерон) OR помпей")
    print("Выход: список doc_id (например page_001).")
    print("Для выхода: пустая строка.\n")

    while True:
        q = input("query> ").strip()
        if not q:
            break
        try:
            res = sorted(search(q, index, all_docs))
            print(f"Документов: {len(res)}")
            for d in res:
                print(d)
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
