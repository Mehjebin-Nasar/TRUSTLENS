from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pickle
import socket
import os
from scraper import fetch_website_data
from text_module import text_trust_score
from image_module import image_trust_score
from behavior_module import behavior_analysis
app = Flask(__name__)
app.secret_key = "trustlens_secret_key"

# ensure upload folder exists
os.makedirs("static/uploads", exist_ok=True)

# ==============================
# DATABASE INITIALIZATION
# ==============================

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ==============================
# LOAD ML MODEL
# ==============================

with open("scam_model.pkl","rb") as f:
    model = pickle.load(f)

with open("vectorizer.pkl","rb") as f:
    vectorizer = pickle.load(f)

# ==============================
# FETCH WEBSITE DATA
# ==============================

def fetch_website_data(url):

    try:

        headers = {"User-Agent":"Mozilla/5.0"}
        response = requests.get(url,headers=headers,timeout=10)

        soup = BeautifulSoup(response.text,"html.parser")

        for tag in soup(["script","style","noscript"]):
            tag.decompose()

        text_parts = []

        if soup.title:
            text_parts.append(soup.title.get_text())

        for p in soup.find_all("p"):
            text_parts.append(p.get_text())

        for h in soup.find_all(["h1","h2","h3"]):
            text_parts.append(h.get_text())

        text = " ".join(text_parts)
        text = " ".join(text.split())[:5000]

        images = []

        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                images.append(urljoin(url,src))

        return text, images

    except:
        return "", []

# ==============================
# BEHAVIOUR ANALYSIS
# ==============================

def behaviour_score(url):

    score = 100

    if not url.startswith("https"):
        score -= 40

    if len(url) > 80:
        score -= 15

    if url.count("-") >= 3:
        score -= 20

    suspicious_words = [
        "free","win","offer","cheap",
        "gift","verify","login",
        "update","account","bonus",
        "claim","reward"
    ]

    for word in suspicious_words:
        if word in url.lower():
            score -= 20

    try:
        domain = url.split("//")[1].split("/")[0]
        socket.gethostbyname(domain)
    except:
        score -= 30

    return max(0,min(score,100))

# ==============================
# AUTH ROUTES
# ==============================

@app.route("/register",methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        try:

            with sqlite3.connect("database.db") as conn:

                cursor = conn.cursor()

                cursor.execute(
                    "INSERT INTO users(username,password) VALUES (?,?)",
                    (username,password)
                )

                conn.commit()

            return redirect(url_for("login"))

        except:

            return render_template("register.html",error="Username already exists")

    return render_template("register.html")


@app.route("/login",methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("database.db") as conn:

            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username,password)
            )

            user = cursor.fetchone()

        if user:

            session["user"] = username
            return redirect(url_for("dashboard"))

        else:

            return render_template("login.html",error="Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))

# ==============================
# MAIN ROUTES
# ==============================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")

# ==============================
# IMAGE UPLOAD ANALYSIS
# ==============================

@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["image"]

    filepath = os.path.join("static/uploads", file.filename)
    file.save(filepath)

    image_score, image_reason = image_trust_score(filepath)

    return render_template(
        "result.html",
        image_score=image_score,
        reasons=[image_reason]
    )

# ==============================
# WEBSITE ANALYSIS
# ==============================

@app.route("/analyze", methods=["POST"])
def analyze():

    url = request.form["url"]

    # get website data
    text, images = fetch_website_data(url)

    # text analysis
    text_score = text_trust_score(text)

    # image analysis
    image_scores = []

    for img in images:
        try:
            score, _ = image_trust_score(img)
            image_scores.append(score)
        except:
            pass

    avg_image_score = sum(image_scores) / len(image_scores) if image_scores else 50

    # behavior analysis
    behavior_score, behavior_reason = behavior_analysis(url)

    # final trust score
    final_score = (
    0.45 * behavior_score +
    0.35 * text_score +
    0.20 * avg_image_score
)
    if final_score >= 75:
        label = "Low Risk"
    elif final_score >= 50:
        label = "Medium Risk"
    else:
        label = "High Risk"
    return render_template(
    "result.html",
    text_score=text_score,
    image_score=avg_image_score,
    behavior_score=behavior_score,
    behavior_reason=behavior_reason,
    final_score=final_score,
    label=label
)
if __name__ == "__main__":
    app.run(debug=True)