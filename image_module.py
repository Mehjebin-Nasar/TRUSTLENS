import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
import imagehash
import sqlite3
from io import BytesIO
import pickle
import cv2
import numpy as np

# Load ML image model
image_ml_model = None

# ===============================
# Config
# ===============================

DB_PATH = "database.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ===============================
# Extract Images From Website
# ===============================

def extract_images(url):

    images = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        for img in soup.find_all("img")[:8]:

            src = img.get("src")

            if src:
                full_url = urljoin(url, src)
                images.append(full_url)

    except Exception:
        pass

    return images[:5]


# ===============================
# Download Image
# ===============================

def download_image(url):

    try:

        response = requests.get(url, headers=HEADERS, timeout=8)

        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGB")

    except Exception:
        pass

    return None


# ===============================
# Generate Perceptual Hash
# ===============================

def generate_hash(image):

    try:
        return imagehash.phash(image)

    except Exception:
        return None


# ===============================
# ML Image Analysis
# ===============================

def ml_image_score(image):

    if image_ml_model is None:
        return 70

    try:
        img_array = np.array(image)
        img_resized = cv2.resize(img_array, (128,128))
        img_flat = img_resized.flatten().reshape(1,-1)

        prediction = image_ml_model.predict(img_flat)[0]

        if prediction == 1:
            return 40
        else:
            return 80

    except:
        return 60


# ===============================
# Detect Watermark
# ===============================

def detect_watermark(image):

    try:

        img = np.array(image)

        edges = cv2.Canny(img, 100, 200)

        if edges.mean() > 50:
            return True
        else:
            return False

    except:
        return False


# ===============================
# Search Image Hash Database
# ===============================

def search_hash_database(hash_value):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:

        cursor.execute("SELECT hash, source, trust_level FROM image_hashes")
        rows = cursor.fetchall()

        best_match = None
        lowest_distance = 100

        for db_hash, source, trust in rows:

            try:

                db_hash = imagehash.hex_to_hash(db_hash)
                distance = hash_value - db_hash

                if distance < lowest_distance:

                    lowest_distance = distance
                    best_match = (source, trust, distance)

            except Exception:
                continue

        return best_match

    finally:
        conn.close()


# ===============================
# Calculate Trust Score
# ===============================

def calculate_image_score(match):

    base_score = 70

    if not match:
        return base_score, "Image not found in database"

    source, trust, distance = match

    if distance <= 5:
        similarity = "very similar"
    elif distance <= 10:
        similarity = "similar"
    else:
        return base_score, "Image appears unique"

    if trust == "trusted":

        score = base_score + 20
        reason = f"Image {similarity} to trusted source ({source})"

    elif trust == "scam":

        score = base_score - 30
        reason = f"Image {similarity} to known scam dataset"

    else:

        score = base_score
        reason = "Image source uncertain"

    score = max(0, min(score, 100))

    return score, reason

def calculate_hash_score(hash_value):
    hash_score, reason = calculate_image_score(match)

    ml_score = ml_image_score(image)

    final_score = (hash_score + ml_score) / 2
# ===============================
# Main Image Trust Analysis
# ===============================

def image_trust_score(url):

    try:

        images = extract_images(url)

        if not images:
            return 70, "No images detected"

        scores = []
        reasons = []

        for img_url in images:

            image = download_image(img_url)

            if not image:
                continue

            hash_value = generate_hash(image)

            if not hash_value:
                continue

            match = search_hash_database(hash_value)


            # watermark penalty
            if detect_watermark(image):
                final_score -= 10

            scores.append(final_score)
            reasons.append(reason)

        if not scores:
            return 65, "Images could not be analyzed"

        avg_score = sum(scores) / len(scores)

        return round(avg_score, 2), reasons[0]

    except Exception:
        return 60, "Image analysis failed"