from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == "admin@trustlens.com" and password == "1234":
            return "Login Successful! Welcome to TRUSTLENS"
        else:
            return "Invalid Email or Password"

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
