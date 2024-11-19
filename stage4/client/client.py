from flask import Flask, request, redirect, url_for, make_response, send_from_directory

app = Flask(__name__)

@app.route("/")
def home():
    user_id = request.cookies.get('username')
    if not user_id:  # Replace `is_valid_user` with your own validation logic
        return redirect(url_for('login'))
    return send_from_directory("html", "home.html")

@app.route("/info")
def info():
    user_id = request.cookies.get('username')
    if not user_id:  # Replace `is_valid_user` with your own validation logic
        return redirect(url_for('login'))
    return send_from_directory("html", "info.html")

@app.route('/login')
def login():
    return send_from_directory("html", "login.html")

app.run(port=8000)