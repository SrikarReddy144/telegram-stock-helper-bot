import os
from flask import Flask, request
import telebot
import requests
import yfinance as yf
from fuzzywuzzy import fuzz, process
from threading import Thread
import time

# Load secrets from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_PATH = os.getenv("SECRET_PATH")
BASE_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === In-Memory Alerts ===
alerts = []

# === Known cryptos for fuzzy matching ===
COMMON_CRYPTOS = ["bitcoin", "ethereum", "dogecoin", "solana", "cardano", "shiba inu", "polkadot", "litecoin"]

# === Helper Functions ===

def get_crypto_price(query):
    try:
        response = requests.get("https://api.coingecko.com/api/v3/coins/markets", params={
            "vs_currency": "usd",
            "ids": query.lower()
        })
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            coin = data[0]
            return f"{coin['name']} (${coin['symbol'].upper()}): ${coin['current_price']:,}"
        return None
    except:
        return None

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"].iloc[-1]
        name = stock.info.get("shortName", ticker)
        return f"{name} ({ticker.upper()}): ${price:.2f}"
    except:
        return None

def match_crypto(query):
    match, score = process.extractOne(query.lower(), COMMON_CRYPTOS)
    if score >= 60:
        return match
    return query

def check_alerts_loop():
    while True:
        time.sleep(30)
        for alert in alerts[:]:
            name = alert["name"]
            target = alert["price"]
            chat_id = alert["chat_id"]
            price = None

            # Try crypto first
            fixed = match_crypto(name)
            result = get_crypto_price(fixed)
            if result:
                try:
                    p = float(result.split("$")[-1].replace(",", ""))
                    price = p
                except:
                    continue
            else:
                # Try stock
                stock_result = get_stock_price(name.upper())
                if stock_result:
                    try:
                        p = float(stock_result.split("$")[-1])
                        price = p
                    except:
                        continue

            if price:
                if (alert["above"] and price >= target) or (not alert["above"] and price <= target):
                    bot.send_message(chat_id, f"🔔 Alert triggered!\n{name.upper()} is now at ${price} (target was ${target})")
                    alerts.remove(alert)

# === Telegram Bot Handlers ===

@bot.message_handler(commands=["start", "help"])
def start_msg(message):
    bot.reply_to(message, "👋 Hi! I can help you with crypto and stock prices.\n\nTry sending:\n- btc\n- price of apple\n- dogecoin\n- /alert btc 30000\n- /alert tsla below 150")

@bot.message_handler(commands=["alert"])
def set_alert(message):
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Usage: /alert <asset> <price> or /alert <asset> below <price>")
            return

        name = parts[1].lower()
        if "below" in parts:
            idx = parts.index("below")
            price = float(parts[idx + 1])
            above = False
        else:
            price = float(parts[2])
            above = True

        alerts.append({
            "name": name,
            "price": price,
            "chat_id": message.chat.id,
            "above": above
        })
        bot.reply_to(message, f"✅ Alert set for {name.upper()} {'above' if above else 'below'} ${price}")
    except:
        bot.reply_to(message, "❌ Couldn't set alert. Please check format.")

@bot.message_handler(func=lambda m: True)
def handle_query(message):
    q = message.text.lower().strip()

    # Handle known typo cases
    if "btc" in q or "bitcoin" in q:
        q = "bitcoin"
    elif "eth" in q or "ether" in q:
        q = "ethereum"

    # Try crypto first
    matched = match_crypto(q)
    result = get_crypto_price(matched)
    if result:
        bot.reply_to(message, f"📈 {result}")
        return

    # Try as stock
    words = q.split()
    possible_tickers = [word.upper() for word in words if word.isalpha() and len(word) <= 5]
    for ticker in possible_tickers:
        stock_result = get_stock_price(ticker)
        if stock_result:
            bot.reply_to(message, f"📊 {stock_result}")
            return

    bot.reply_to(message, "❓ Sorry, I couldn't find anything for that. Try asking for BTC, ETH, TSLA, AAPL, DOGE, etc.")

# === Flask Webhook ===

@app.route(f"/{SECRET_PATH}", methods=["POST"])
def webhook():
    if request.method == "POST":
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is alive!", 200

# === Start Everything ===

if __name__ == "__main__":
    Thread(target=check_alerts_loop, daemon=True).start()
    bot.remove_webhook()
    bot.set_webhook(url=f"{BASE_URL}/{SECRET_PATH}")
    app.run(host="0.0.0.0", port=10000)
