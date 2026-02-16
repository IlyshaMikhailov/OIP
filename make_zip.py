import zipfile
import os

with zipfile.ZipFile("pages_archive.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk("pages"):
        for file in files:
            full_path = os.path.join(root, file)
            z.write(full_path)

    z.write("index.txt")

print("Archive created.")