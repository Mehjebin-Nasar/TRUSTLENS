import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def fetch_website_data(url):

    try:
        response = requests.get(url, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Extract important text
        text_parts = []

        if soup.title:
            text_parts.append(soup.title.get_text())

        for p in soup.find_all("p"):
            text_parts.append(p.get_text())

        for h in soup.find_all(["h1", "h2", "h3"]):
            text_parts.append(h.get_text())

        text = " ".join(text_parts)

        # Extract images
        images = []

        for img in soup.find_all("img")[:8]:
            src = img.get("src")

            if src:
                images.append(urljoin(url, src))

        return text, images

    except Exception as e:
        print("Error fetching website:", e)
        return "", []