import os
from flask import Flask, request
import requests
from bot import handle_message

TOKEN = os.getenv("BOT_TOKEN")
SECRET_PATH = os.getenv("WEBHOOK_SECRET", "secret-path")  # default secret if not set
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

app = Flask(__name__)

@app.route(f"/{SECRET_PATH}", methods=["POST"])
def webhook():
    data = request.json
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_msg = data["message"]["text"]

        reply = handle_message(user_msg)
        requests.post(URL, json={"chat_id": chat_id, "text": reply})
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "✅ MoneyMaster Bot is Running!"
if app=="__name__":
    app.run(port=10000,ip='0.0.0.0')
