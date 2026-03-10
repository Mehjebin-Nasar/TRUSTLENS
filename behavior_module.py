import requests

def behavior_analysis(url):

    score = 100

    # HTTP instead of HTTPS
    if not url.startswith("https"):
        score -= 40

    suspicious_keywords = [
        "login",
        "verify",
        "secure",
        "account",
        "update",
        "bank"
    ]

    for word in suspicious_keywords:
        if word in url.lower():
            score -= 10

    try:
        response = requests.get(url, timeout=5)

        if len(response.history) > 2:
            score -= 20

        if response.status_code != 200:
            score -= 10

    except:
        score -= 50

    return max(0, min(score, 100))