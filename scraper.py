import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def fetch_website_data(url):

    try:
        response = requests.get(url, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract text content
        text = soup.get_text()

        # Extract images
        images = []

        for img in soup.find_all("img"):
            src = img.get("src")

            if src:
                full_url = urljoin(url, src)
                images.append(full_url)

        return text, images

    except Exception as e:
        print("Error fetching website:", e)
        return "", []