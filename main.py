import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
import telebot
from fuzzywuzzy import fuzz

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_PATH = os.getenv("SECRET_PATH")
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Known Crypto and Stock Maps ---
CRYPTO_MAP = {
    "btc": "bitcoin", "eth": "ethereum", "doge": "dogecoin", "sol": "solana",
    "ada": "cardano", "xrp": "ripple", "ltc": "litecoin", "bnb": "binancecoin"
}

STOCK_MAP = {
    "aapl": "Apple", "goog": "Google", "msft": "Microsoft", "tsla": "Tesla",
    "amzn": "Amazon", "meta": "Meta", "nflx": "Netflix", "nvda": "Nvidia"
}

alerts = {}

# --- Util: Fuzzy Extract Symbol ---
def extract_symbol(text):
    text = text.lower()
    candidates = list(CRYPTO_MAP.keys()) + list(CRYPTO_MAP.values()) + list(STOCK_MAP.keys()) + list(STOCK_MAP.values())
    best = max(candidates, key=lambda x: fuzz.partial_ratio(x, text))
    if fuzz.partial_ratio(best, text) > 60:
        return best
    return None

# --- Fetch Prices ---
def get_crypto_price(symbol):
    real_symbol = CRYPTO_MAP.get(symbol.lower(), symbol.lower())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={real_symbol}&vs_currencies=usd"
    try:
        data = requests.get(url).json()
        price = data[real_symbol]['usd']
        return f"{real_symbol.title()} → ${price}"
    except:
        return "❌ Crypto not found."

def get_stock_price(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol.upper()}&apikey={API_KEY}"
    try:
        data = requests.get(url).json()
        price = data["Global Quote"]["05. price"]
        return f"{symbol.upper()} → ${price}"
    except:
        return "❌ Stock not found."

# --- Commands ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hi! Ask me for any stock or crypto price. Try:\n- btc\n- show apple\n- set alert btc 30000")

@bot.message_handler(commands=['btc'])
def btc_price(message):
    bot.reply_to(message, get_crypto_price("btc"))

@bot.message_handler(commands=['stock'])
def stock_price(message):
    parts = message.text.split()
    if len(parts) > 1:
        sym = parts[1].lower()
        bot.reply_to(message, get_stock_price(sym))
    else:
        bot.reply_to(message, "⚠️ Use: /stock AAPL")

@bot.message_handler(commands=['top'])
def top_cryptos(message):
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=5&page=1"
    try:
        data = requests.get(url).json()
        reply = "\n".join([f"{coin['name']} ({coin['symbol'].upper()}): ${coin['current_price']}" for coin in data])
        bot.reply_to(message, f"🔥 Top 5 Cryptos:\n{reply}")
    except:
        bot.reply_to(message, "❌ Couldn't fetch top coins.")

@bot.message_handler(commands=['alert'])
def set_alert(message):
    try:
        parts = message.text.split()
        symbol, target = parts[1].lower(), float(parts[2])
        alerts[symbol] = target
        bot.reply_to(message, f"🔔 Alert set for {symbol.upper()} at ${target}")
    except:
        bot.reply_to(message, "⚠️ Use: /alert btc 30000")

# --- AI-style Free Messages ---
@bot.message_handler(func=lambda m: True)
def ai_response(message):
    text = message.text.lower()
    symbol = extract_symbol(text)

    if not symbol:
        bot.reply_to(message, "❌ Sorry, I couldn’t understand which stock or coin you meant.")
        return

    if symbol in CRYPTO_MAP or symbol in CRYPTO_MAP.values():
        bot.reply_to(message, get_crypto_price(symbol))
    elif symbol in STOCK_MAP or symbol in STOCK_MAP.values():
        sym = [k for k, v in STOCK_MAP.items() if v.lower() == symbol or k == symbol]
        if sym:
            bot.reply_to(message, get_stock_price(sym[0]))
        else:
            bot.reply_to(message, get_stock_price(symbol))
    else:
        bot.reply_to(message, "❌ I don’t know this asset.")

# --- Flask Webhook ---
@app.route(f"/{SECRET_PATH}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is alive!"

# --- Webhook Setup ---
import threading
@bot.message_handler(commands=['setwebhook'])
def manual_webhook(message):
    bot.remove_webhook()
    full_url = f"{BASE_URL}/{SECRET_PATH}"
    bot.set_webhook(url=full_url)
    bot.reply_to(message, f"✅ Webhook set to {full_url}")

# --- Start App ---
if __name__ == "__main__":
    threading.Thread(target=lambda: bot.remove_webhook()).start()
    threading.Thread(target=lambda: bot.set_webhook(url=f"{BASE_URL}/{SECRET_PATH}")).start()
    app.run(host="0.0.0.0", port=10000)
