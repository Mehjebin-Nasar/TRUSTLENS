import requests
import whois
from datetime import datetime
from urllib.parse import urlparse


def behavior_analysis(url):

    score = 100
    reasons = []

    # HTTPS check
    if not url.startswith("https"):
        score -= 40
        reasons.append("Website is not using HTTPS")

    # Suspicious keywords
    suspicious_keywords = ["login","verify","secure","account","update","bank"]

    for word in suspicious_keywords:
        if word in url.lower():
            score -= 10
            reasons.append("Suspicious keyword detected in URL")

    # Domain age check
    try:
        domain = urlparse(url).netloc
        domain_info = whois.whois(domain)

        creation_date = domain_info.creation_date

        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if creation_date:
            age_days = (datetime.now() - creation_date).days

            if age_days < 30:
                score -= 30
                reasons.append("Domain is very new")

    except:
     reasons.append("Domain age unavailable (WHOIS blocked)")

    # Website response behaviour
    try:
        response = requests.get(url, timeout=5)

        if len(response.history) > 2:
            score -= 20
            reasons.append("Too many redirects")

        if response.status_code != 200:
            score -= 10
            reasons.append("Website returned abnormal status code")

    except:
        score -= 50
        reasons.append("Website could not be reached")

    return max(0, min(score, 100)), reasons