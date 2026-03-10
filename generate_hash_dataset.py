import imagehash
from PIL import Image
import os
import sqlite3

conn = sqlite3.connect("database.db")

folder = "dataset/fake_images"

for img in os.listdir(folder):

    image = Image.open(os.path.join(folder,img))

    hash_value = str(imagehash.phash(image))

    conn.execute(
        "INSERT INTO image_hashes(hash,source,trust_level) VALUES (?,?,?)",
        (hash_value,"fake_dataset","scam")
    )

conn.commit()