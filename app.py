from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pickle
import socket

# Import image module
from image_module import image_trust_score

app = Flask(__name__)
app.secret_key = "trustlens_secret_key"


# ==============================
# DATABASE INITIALIZATION
# ==============================

def init_db():
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)
        conn.commit()

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

        return text,images

    except:
        return "",[]


# ==============================
# BEHAVIOUR ANALYSIS
# ==============================

def behaviour_score(url):

    score = 100

    if not url.startswith("https"):
        score -= 20

    if len(url) > 80:
        score -= 10

    if url.count("-") >= 4:
        score -= 10

    suspicious_words = [
        "free","win","offer","cheap",
        "gift","verify","login",
        "update","account"
    ]

    for word in suspicious_words:
        if word in url.lower():
            score -= 10

    try:
        domain = url.split("//")[1].split("/")[0]
        socket.gethostbyname(domain)
    except:
        score -= 20

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

    return render_template("index.html")


# ==============================
# WEBSITE ANALYSIS
# ==============================

@app.route("/analyze",methods=["POST"])
def analyze():

    if "user" not in session:
        return redirect(url_for("login"))

    url = request.form["url"]

    if not url.startswith(("http://","https://")):
        url = "https://" + url

    text,images = fetch_website_data(url)

    reasons = []


    # TEXT ANALYSIS

    if text:

        vector = vectorizer.transform([text])

        probabilities = model.predict_proba(vector)[0]

        scam_prob = max(probabilities)

        text_score = round(100*(1-scam_prob),2)

        if scam_prob > 0.7:
            reasons.append("Text resembles scam patterns")
        else:
            reasons.append("Text appears legitimate")

    else:

        text_score = 60
        reasons.append("Text could not be analyzed")


    # IMAGE ANALYSIS

    image_score,image_reason = image_trust_score(url)

    reasons.append(image_reason)


    # BEHAVIOUR ANALYSIS

    behaviour = behaviour_score(url)

    if behaviour < 60:
        reasons.append("Suspicious URL behaviour detected")
    else:
        reasons.append("URL structure appears normal")


    # DANGEROUS DOMAIN CHECK

    dangerous_tlds = [".xyz",".top",".click",".ru",".tk"]

    for tld in dangerous_tlds:

        if url.endswith(tld):

            behaviour -= 30

            reasons.append("High-risk domain extension detected")


    # FINAL SCORE

    final_score = round(

        text_score*0.25 +

        image_score*0.30 +

        behaviour*0.45

        ,2
    )

    final_score = max(0,min(100,final_score))


    # RISK LEVEL

    if final_score >= 80:

        risk = "LOW RISK"

    elif final_score >= 50:

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

        reasons=reasons

    )


# ==============================
# RUN SERVER
# ==============================

if __name__ == "__main__":
    app.run(debug=True)