import os
import json
import time
import threading
from flask import Flask, request
import requests
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

load_dotenv()
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_PATH = os.getenv("SECRET_PATH")
URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

ALERTS_FILE = "alerts.json"

if not os.path.exists(ALERTS_FILE):
    with open(ALERTS_FILE, "w") as f:
        json.dump([], f)

def save_alert(user_id, asset, condition, value):
    with open(ALERTS_FILE, "r") as f:
        alerts = json.load(f)
    alerts.append({
        "user_id": user_id,
        "asset": asset.upper(),
        "condition": condition,
        "value": value
    })
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f)

def get_crypto_price(symbol):
    try:
        response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd")
        data = response.json()
        return data[symbol.lower()]['usd']
    except:
        return None

def get_stock_price(symbol):
    try:
        r = requests.get(f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}")
        data = r.json()
        return data['quoteResponse']['result'][0]['regularMarketPrice']
    except:
        return None

def smart_price_lookup(query):
    if " " in query:
        query = query.split(" ")[-1]
    symbol = query.upper()
    price = get_crypto_price(symbol)
    if price:
        return f"💰 {symbol} price: ${price}"
    price = get_stock_price(symbol)
    if price:
        return f"📈 {symbol} stock: ${price}"
    return "❓ Sorry, I couldn't find anything for that. Try BTC, ETH, TSLA, AAPL, etc."

def parse_alert(text):
    text = text.lower()
    if "alert" in text or "notify" in text or "set" in text:
        for word in text.split():
            if word.replace('.', '', 1).isdigit():
                value = float(word)
                break
        else:
            return None

        if "above" in text or "more" in text or "over" in text:
            condition = ">"
        elif "below" in text or "less" in text or "under" in text:
            condition = "<"
        else:
            condition = ">"

        for token in text.split():
            if token.isalpha() and len(token) <= 6:
                asset = token
                break
        else:
            return None

        return asset.upper(), condition, value
    return None

def check_alerts():
    while True:
        with open(ALERTS_FILE, "r") as f:
            alerts = json.load(f)

        new_alerts = []
        for alert in alerts:
            user_id = alert["user_id"]
            asset = alert["asset"]
            condition = alert["condition"]
            value = alert["value"]

            price = get_crypto_price(asset) or get_stock_price(asset)
            if price is None:
                new_alerts.append(alert)
                continue

            if (condition == ">" and price >= value) or (condition == "<" and price <= value):
                requests.post(URL, json={
                    "chat_id": user_id,
                    "text": f"🔔 {asset} reached your alert target: ${price}"
                })
            else:
                new_alerts.append(alert)

        with open(ALERTS_FILE, "w") as f:
            json.dump(new_alerts, f)

        time.sleep(60)

@app.route(f'/{SECRET_PATH}', methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" not in data:
        return "ok"
    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text.startswith("/start"):
        send_message(chat_id, "👋 Hi! Ask me for any stock or crypto price. Try:\n- `btc`\n- `show apple`\n- `set alert btc 30000`")
        return "ok"

    parsed = parse_alert(text)
    if parsed:
        asset, cond, val = parsed
        save_alert(chat_id, asset, cond, val)
        send_message(chat_id, f"✅ Alert set for {asset} when it goes {'above' if cond == '>' else 'below'} ${val}")
    else:
        response = smart_price_lookup(text)
        send_message(chat_id, response)

    return "ok"

def send_message(chat_id, text):
    requests.post(URL, json={"chat_id": chat_id, "text": text})

@app.route('/')
def home():
    return "Bot is running."

if __name__ == "__main__":
    threading.Thread(target=check_alerts, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
