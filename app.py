from flask import Flask, request
from bot import handle_message
import os

app = Flask(__name__)
SECRET_PATH = os.getenv("SECRET_PATH", "your_secret_path")

@app.route(f"/{SECRET_PATH}", methods=["POST"])
def webhook():
    data = request.get_json()
    handle_message(data)
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "StockHelperBot is running!"

if __name__ == "__main__":
    app.run()