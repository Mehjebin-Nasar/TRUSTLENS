from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3
import instaloader

# ==========================================
# APP INITIALIZATION
# ==========================================

app = Flask(__name__)
app.secret_key = "trustlens_secret_key"

# ==========================================
# DATABASE SETUP
# ==========================================

def init_db():
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        conn.commit()

init_db()

# ==========================================
# LOAD NLP MODEL
# ==========================================

with open("scam_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# ==========================================
# FETCH WEBSITE DATA
# ==========================================

def fetch_website_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ")
        text = " ".join(text.split())[:5000]

        images = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                images.append(urljoin(url, src))

        return text, images

    except:
        return "", []

# ==========================================
# BEHAVIOUR ANALYSIS (45%)
# ==========================================

def behaviour_score(url):
    score = 90

    if not url.startswith("https"):
        score -= 25

    if len(url) > 75:
        score -= 15

    if url.count("-") > 3:
        score -= 10

    suspicious_words = ["free", "win", "offer", "cheap", "prize", "money"]
    for word in suspicious_words:
        if word in url.lower():
            score -= 10

    return max(score, 0)

# ==========================================
# IMAGE BACKTRACKING MODULE (30%)
# ==========================================

def extract_instagram_username(url):
    return url.rstrip("/").split("/")[-1]

def get_profile_pic(username):
    try:
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)
        return profile.profile_pic_url
    except:
        return None

def calculate_image_trust(matches):
    if matches == 0:
        return 95
    elif matches <= 3:
        return 70
    elif matches <= 6:
        return 40
    else:
        return 15

def simulate_reverse_image_search():
    """
    Demo-safe simulation.
    Replace with real API if needed.
    """
    import random
    return random.randint(0, 8)

# ==========================================
# AUTH ROUTES
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        try:
            with sqlite3.connect("database.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password)
                )
                conn.commit()
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            error = "Username already exists."

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )
            user = cursor.fetchone()

        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================================
# MAIN ROUTES
# ==========================================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    if "user" not in session:
        return redirect(url_for("login"))

    url = request.form["url"].strip()

    # Auto-fix URL if missing protocol
    if not url.startswith(("http://", "https://")):
         url = "https://" + url

    text, images = fetch_website_data(url)

    # ==========================
    # TEXT ANALYSIS (25%)
    # ==========================

    try:
        vector = vectorizer.transform([text])
        probabilities = model.predict_proba(vector)[0]
        scam_prob = max(probabilities)
        text_score = round(100 * (1 - scam_prob), 2)
    except:
        text_score = 50  # fallback

    # ==========================
    # IMAGE ANALYSIS (30%)
    # ==========================

    image_score = 60  # default neutral
    matches = 0

    if "instagram.com" in url:
        username = extract_instagram_username(url)
        profile_pic_url = get_profile_pic(username)

        if profile_pic_url:
            matches = simulate_reverse_image_search()
            image_score = calculate_image_trust(matches)
        else:
            image_score = 30
    else:
        image_count = len(images)

        if image_count == 0:
            image_score = 30
        elif image_count < 3:
            image_score = 60
        else:
            image_score = 85

    # ==========================
    # BEHAVIOUR ANALYSIS (45%)
    # ==========================

    behaviour = behaviour_score(url)

    # ==========================
    # FINAL WEIGHTED SCORE
    # ==========================

    final_score = round(
        text_score * 0.25 +
        image_score * 0.30 +
        behaviour * 0.45,
        2
    )

    # ==========================
    # RISK CLASSIFICATION
    # ==========================

    if final_score >= 75:
        risk = "LOW RISK"
    elif final_score >= 40:
        risk = "MEDIUM RISK"
    else:
        risk = "HIGH RISK"

    return render_template(
        "result.html",
        final_score=final_score,
        text_score=text_score,
        image_score=image_score,
        behaviour_score=behaviour,
        risk=risk,
        matches=matches
    )

# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)