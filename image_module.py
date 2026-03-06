import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import imagehash


# ===============================
# Extract Images
# ===============================

def extract_images(url):

    images = []

    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        for img in soup.find_all("img"):

            src = img.get("src")

            if src:

                full_url = urljoin(url, src)

                images.append(full_url)

    except:
        pass

    return images[:6]


# ===============================
# Download Image
# ===============================

def download_image(url):

    try:

        response = requests.get(url, timeout=10)

        image = Image.open(BytesIO(response.content))

        return image

    except:

        return None


# ===============================
# Generate Image Hash
# ===============================

def generate_hash(image):

    try:

        return imagehash.phash(image)

    except:

        return None


# ===============================
# Detect Reused Images
# ===============================

def detect_reused_images(images):

    hashes = []
    duplicates = 0

    for img_url in images:

        image = download_image(img_url)

        if image:

            h = generate_hash(image)

            if h in hashes:
                duplicates += 1
            else:
                hashes.append(h)

    return duplicates


# ===============================
# Image Trust Score
# ===============================

def image_trust_score(url):

    images = extract_images(url)

    image_count = len(images)

    if image_count == 0:

        return 50, "No images found on the page"

    duplicates = detect_reused_images(images)

    # scoring logic

    if duplicates >= 3:

        return 35, "Multiple duplicated images detected"

    elif duplicates >= 1:

        return 55, "Some reused images detected"

    # now adjust score based on structure

    if image_count <= 2:

        return 60, "Very few images on page"

    elif image_count <= 5:

        return 75, "Normal image structure"

    else:

        return 90, "Rich image structure detected"