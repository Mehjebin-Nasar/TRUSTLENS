import pickle
import warnings
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "trustlens_secret_key"

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# ---------- CREATE TABLE ----------
def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


create_table()
# ---------- LOAD AI MODEL ----------
with open("scam_model.pkl", "rb") as f:
    scam_model = pickle.load(f)

with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)
    
def predict_message(text):
    vector = vectorizer.transform([text])
    prediction = scam_model.predict(vector)[0]
    probability = scam_model.predict_proba(vector)[0]

    if prediction == 1:
        trust_score = int((1 - probability[1]) * 100)
        result = "Scam"
    else:
        trust_score = int(probability[0] * 100)
        result = "Safe"

    return result, trust_score



# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?',
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Email or Password"

    return render_template('login.html')


# ---------- DASHBOARD ----------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    result = None

    if request.method == 'POST':
        message = request.form['message']
        result = predict_message(message)

    return render_template('dashboard.html',
                           username=session['username'],
                           result=result)

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['username'])


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, password)
        )
        conn.commit()
        conn.close()

        return "Registration Successful! You can now login."

    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)
