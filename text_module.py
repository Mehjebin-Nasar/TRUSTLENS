import random

def text_trust_score(text):

    suspicious_words = [
        "shocking",
        "breaking",
        "secret",
        "you won't believe",
        "limited offer",
        "click here",
        "urgent",
        "act now",
        "free money",
        "password"
    ]

    score = 100

    for word in suspicious_words:
        if word in text.lower():
            score -= 20

    if len(text) < 200:
        score -= 20

    return max(0, min(score, 100))