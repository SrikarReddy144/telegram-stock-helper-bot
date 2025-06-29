import os
import re
import time
import requests
import yfinance as yf
from dotenv import load_dotenv
from flask import Flask, request
from fuzzywuzzy import fuzz, process
from telebot import TeleBot, types

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
SECRET_PATH = os.getenv("SECRET_PATH")
BASE_URL = os.getenv("BASE_URL", "")

bot = TeleBot(TOKEN)
app = Flask(__name__)

# Load CoinGecko coins list
COIN_LIST = []
COIN_NAME_MAP = {}
def fetch_coin_list():
    global COIN_LIST, COIN_NAME_MAP
    try:
        r = requests.get("https://api.coingecko.com/api/v3/coins/list")
        COIN_LIST = r.json()
        COIN_NAME_MAP = {coin['name'].lower(): coin['id'] for coin in COIN_LIST}
        COIN_NAME_MAP.update({coin['symbol'].lower(): coin['id'] for coin in COIN_LIST})
    except Exception as e:
        print("Error loading coin list:", e)

fetch_coin_list()

alerts = {}

def get_best_coin_match(query):
    choices = list(COIN_NAME_MAP.keys())
    match, score = process.extractOne(query.lower(), choices)
    return COIN_NAME_MAP.get(match) if score > 70 else None

def get_crypto_price(symbol):
    coin_id = get_best_coin_match(symbol)
    if not coin_id:
        return None
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    r = requests.get(url).json()
    return r.get(coin_id, {}).get("usd")

def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol.upper())
        data = stock.history(period="1d")
        if not data.empty:
            return round(data["Close"].iloc[-1], 2)
    except:
        pass
    return None

def detect_intent(text):
    t = text.lower()
    if any(word in t for word in ["price", "value", "show", "get"]):
        return "price"
    elif any(word in t for word in ["alert", "notify", "ping", "remind"]):
        return "alert"
    return "unknown"

def parse_price(text):
    numbers = re.findall(r'\d+\.?\d*', text.replace(',', ''))
    return float(numbers[0]) if numbers else None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(msg):
    bot.send_message(msg.chat.id, "👋 Welcome! Send me messages like:\n- `btc price`\n- `goog price`\n- `alert doge 0.2`")

@bot.message_handler(commands=['btc'])
def btc_price(msg):
    price = get_crypto_price("btc")
    bot.send_message(msg.chat.id, f"Bitcoin price: ${price}" if price else "Couldn't fetch BTC price.")

@bot.message_handler(commands=['stock'])
def stock_price(msg):
    bot.send_message(msg.chat.id, "Send a stock symbol like `TSLA`, `AAPL`, or `GOOG`.")

@bot.message_handler(commands=['top'])
def top_cryptos(msg):
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
        r = requests.get(url).json()
        text = "\n".join([f"{c['name']}: ${c['current_price']}" for c in r])
        bot.send_message(msg.chat.id, f"🔥 Top 10 Cryptos:\n{text}")
    except:
        bot.send_message(msg.chat.id, "Failed to fetch top cryptos.")

@bot.message_handler(func=lambda msg: True)
def smart_handler(msg):
    text = msg.text.strip()
    intent = detect_intent(text)
    symbol_match = re.search(r'\b[a-zA-Z]{2,10}\b', text)
    symbol = symbol_match.group() if symbol_match else None
    price = parse_price(text)

    if not symbol:
        bot.send_message(msg.chat.id, "❓ Please include a coin or stock name.")
        return

    if intent == "price":
        crypto = get_crypto_price(symbol)
        if crypto:
            bot.send_message(msg.chat.id, f"{symbol.upper()} (crypto): ${crypto}")
            return
        stock = get_stock_price(symbol)
        if stock:
            bot.send_message(msg.chat.id, f"{symbol.upper()} (stock): ${stock}")
            return
        bot.send_message(msg.chat.id, f"❌ Couldn't find price for '{symbol}'")
    elif intent == "alert":
        if price:
            alerts[(msg.chat.id, symbol.lower())] = price
            bot.send_message(msg.chat.id, f"🔔 Alert set: {symbol.upper()} at ${price}")
        else:
            bot.send_message(msg.chat.id, "⚠️ Couldn't detect alert price.")
    else:
        bot.send_message(msg.chat.id, "🤖 I didn't understand. Try 'btc price' or 'alert shib 0.01'.")

# Background checker (not suitable on free hosting — here for logic)
def check_alerts():
    while True:
        for (cid, symbol), target in alerts.items():
            crypto_price = get_crypto_price(symbol)
            if crypto_price and crypto_price >= target:
                bot.send_message(cid, f"🔔 {symbol.upper()} reached ${crypto_price} (≥ {target})")
                alerts.pop((cid, symbol))
        time.sleep(60)

@app.route(f"/{SECRET_PATH}", methods=["POST"])
def webhook():
    if request.method == "POST":
        bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "", 200
    return "Method Not Allowed", 405

# Only set webhook when run directly (for Render)
if __name__ == "__main__":
    bot.remove_webhook()
    full_url = f"{BASE_URL}/{SECRET_PATH}"
    bot.set_webhook(url=full_url)
    app.run(host="0.0.0.0", port=10000)
