import os
from flask import Flask, request
from telebot import TeleBot, types
import requests
from fuzzywuzzy import process
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_PATH = os.getenv("SECRET_PATH")
BASE_URL = os.getenv("BASE_URL")

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Coin alias map
ALIASES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "doge": "dogecoin",
    "shib": "shiba inu",
    "ltc": "litecoin",
    "dot": "polkadot",
    "ada": "cardano"
}

# Simple database (in-memory)
alerts = {}

# --- HELPER FUNCTIONS ---

def match_crypto(query):
    r = requests.get("https://api.coingecko.com/api/v3/coins/list")
    if r.status_code != 200:
        return None
    coins = r.json()
    names = [coin["id"] for coin in coins]
    match, score = process.extractOne(query.lower(), names)
    return match if score > 60 else None

def get_crypto_price(coin_id):
    r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd")
    if r.status_code == 200:
        data = r.json()
        return data.get(coin_id, {}).get("usd")
    return None

def get_stock_price(symbol):
    r = requests.get(f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}")
    try:
        return r.json()["quoteResponse"]["result"][0]["regularMarketPrice"]
    except:
        return None

# --- TELEGRAM HANDLERS ---

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "👋 Hi! Ask me for any stock or crypto price. Try:\n- btc\n- show apple\n- set alert btc 30000")

@bot.message_handler(commands=["btc"])
def btc_price(msg):
    price = get_crypto_price("bitcoin")
    if price:
        bot.send_message(msg.chat.id, f"₿ Bitcoin price: ${price}")
    else:
        bot.send_message(msg.chat.id, "❌ Couldn't fetch BTC price.")

@bot.message_handler(commands=["top"])
def top_cryptos(msg):
    r = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=5")
    if r.status_code != 200:
        bot.send_message(msg.chat.id, "❌ Failed to get top cryptos.")
        return
    data = r.json()
    text = "📈 Top 5 Cryptos:\n"
    for coin in data:
        text += f"- {coin['name']} (${coin['current_price']})\n"
    bot.send_message(msg.chat.id, text)

@bot.message_handler(commands=["alert"])
def set_alert(msg):
    try:
        parts = msg.text.split()
        symbol, target = parts[1], float(parts[2])
        alerts[msg.chat.id] = (symbol, target)
        bot.send_message(msg.chat.id, f"🔔 Alert set: {symbol.upper()} at ${target}")
    except:
        bot.send_message(msg.chat.id, "⚠️ Usage: /alert btc 30000")

# --- SMART NATURAL MESSAGE HANDLER ---

@bot.message_handler(func=lambda m: True)
def handle_query(msg):
    q = msg.text.strip().lower()

    # Replace aliases
    for word in q.split():
        if word in ALIASES:
            q = ALIASES[word]
            break

    # Try crypto match
    crypto = match_crypto(q)
    if crypto:
        price = get_crypto_price(crypto)
        if price:
            bot.send_message(msg.chat.id, f"💰 {crypto.title()} price: ${price}")
            return

    # Try stock price (symbols are upper)
    stock_price = get_stock_price(q.upper())
    if stock_price:
        bot.send_message(msg.chat.id, f"📊 {q.upper()} stock price: ${stock_price}")
        return

    bot.send_message(msg.chat.id, "❓ Sorry, I couldn't find anything for that. Try BTC, ETH, TSLA, AAPL, etc.")

# --- FLASK WEBHOOK ---

@app.route(f"/{SECRET_PATH}", methods=["POST"])
def webhook():
    bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok"

@app.route("/", methods=["GET"])
def root():
    return "✅ Bot is running."

# --- MAIN ---

if __name__ == "__main__":
    import telebot
    webhook_url = f"{BASE_URL}/{SECRET_PATH}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    app.run(host="0.0.0.0", port=10000)
