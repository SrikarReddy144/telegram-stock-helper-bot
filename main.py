import os
import telebot
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_PATH = os.getenv("SECRET_PATH")
BASE_URL = os.getenv("BASE_URL")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

alerts = {}  # Example: {("user_id", "btc"): 30000}


# ✅ Basic command: /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "👋 Hi! I'm your smart crypto & stock bot. Try:\n\n- btc\n- show apple stock\n- /alert btc 30000")


# ✅ BTC command
@bot.message_handler(commands=["btc"])
def btc_price(message):
    price = get_crypto_price("bitcoin")
    bot.send_message(message.chat.id, f"₿ BTC: ${price}" if price else "BTC not found.")


# ✅ Stock command
@bot.message_handler(commands=["stock"])
def stock_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Usage: /stock AAPL")
        return
    symbol = parts[1].upper()
    price = get_stock_price(symbol)
    bot.send_message(message.chat.id, f"📈 {symbol}: ${price}" if price else "Stock not found.")


# ✅ Top cryptos
@bot.message_handler(commands=["top"])
def top_cryptos(message):
    try:
        res = requests.get("https://api.coingecko.com/api/v3/coins/markets", params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10})
        data = res.json()
        reply = "💎 Top 10 Cryptos:\n"
        for coin in data:
            reply += f"{coin['symbol'].upper()}: ${coin['current_price']}\n"
        bot.send_message(message.chat.id, reply)
    except:
        bot.send_message(message.chat.id, "Error getting top cryptos.")


# ✅ Alert: /alert btc 30000
@bot.message_handler(commands=["alert"])
def set_alert(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "Usage: /alert btc 30000")
        return
    asset = parts[1].lower()
    try:
        target = float(parts[2])
        alerts[(message.chat.id, asset)] = target
        bot.send_message(message.chat.id, f"🔔 Alert set for {asset.upper()} at ${target}")
    except:
        bot.send_message(message.chat.id, "Invalid amount.")


# ✅ AI-style smart reply
@bot.message_handler(func=lambda m: True)
def smart_reply(message):
    text = message.text.lower()
    if "btc" in text or "bitcoin" in text:
        return btc_price(message)
    if "eth" in text:
        return send_price(message, "ethereum")
    if "sol" in text:
        return send_price(message, "solana")
    if "doge" in text:
        return send_price(message, "dogecoin")
    if "stock" in text or "show" in text:
        words = text.split()
        for word in words:
            if word.isalpha() and len(word) <= 5:
                return send_stock(message, word.upper())
    bot.send_message(message.chat.id, "❓ I didn’t understand that. Try `/btc`, `/alert`, or `apple stock`.")


# 🔧 Reusable functions
def get_crypto_price(symbol):
    try:
        res = requests.get(f"https://api.coingecko.com/api/v3/simple/price", params={"ids": symbol, "vs_currencies": "usd"})
        return res.json()[symbol]["usd"]
    except:
        return None


def get_stock_price(symbol):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote-short/{symbol}?apikey={STOCK_API_KEY}"
        res = requests.get(url)
        data = res.json()
        return data[0]["price"] if data else None
    except:
        return None


def send_price(message, symbol):
    price = get_crypto_price(symbol)
    bot.send_message(message.chat.id, f"{symbol.upper()}: ${price}" if price else "Not found.")


def send_stock(message, symbol):
    price = get_stock_price(symbol)
    bot.send_message(message.chat.id, f"{symbol}: ${price}" if price else "Stock not found.")


# ✅ Webhook route
@app.route(f"/{SECRET_PATH}", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        bot.remove_webhook()
        bot.set_webhook(url=f"{BASE_URL}/{SECRET_PATH}")
        return "✅ Webhook set!", 200

    if request.method == "POST":
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200


# ✅ Flask home
@app.route("/")
def home():
    return "🤖 Bot is running."


# ✅ Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
