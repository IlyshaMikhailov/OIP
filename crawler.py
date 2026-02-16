import os
import requests
from time import sleep

# Папка для сохранения страниц
output_dir = "web_pages"
os.makedirs(output_dir, exist_ok=True)

# Файлы
links_file = "links.txt"
index_file = "index.txt"  # снаружи папки web_pages

# Читаем ссылки, убираем номера в начале, если есть
urls = []
with open(links_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # Если строка начинается с номера, отделяем его
        if " " in line:
            url = line.split(" ", 1)[1]
        else:
            url = line
        urls.append(url)

# Создаём index.txt снаружи папки
with open(index_file, "w", encoding="utf-8") as idx_f:
    for i, url in enumerate(urls, start=1):
        try:
            print(f"[{i}] Скачиваем: {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            file_name = f"page_{i}.html"
            file_path = os.path.join(output_dir, file_name)

            # Сохраняем страницу
            with open(file_path, "w", encoding="utf-8") as f_out:
                f_out.write(response.text)

            # Записываем номер и ссылку в index.txt
            idx_f.write(f"{i}\t{url}\n")

            # Пауза, чтобы не перегружать сервер
            sleep(1)

        except Exception as e:
            print(f"Ошибка при скачивании {url}: {e}")
