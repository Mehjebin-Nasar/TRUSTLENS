import os
import sqlite3
from PIL import Image
import imagehash

conn = sqlite3.connect("database.db")

folder = "dataset/fake_images"

for file in os.listdir(folder):

    path = os.path.join(folder,file)

    img = Image.open(path)

    hash_value = str(imagehash.phash(img))

    conn.execute(
        "INSERT INTO image_hashes(hash,source,trust_level) VALUES (?,?,?)",
        (hash_value,"fake_dataset","scam")
    )

conn.commit()