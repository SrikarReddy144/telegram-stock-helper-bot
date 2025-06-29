import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request
from fuzzywuzzy import process

BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_PATH = os.getenv("SECRET_PATH")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

COINS = {
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'doge': 'dogecoin',
    'sol': 'solana',
    'xrp': 'ripple',
    'ada': 'cardano',
    'ltc': 'litecoin',
    'matic': 'polygon'
}
alerts = {}

# 🔹 Get crypto price
def get_crypto_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        res = requests.get(url, timeout=3)
        return res.json()[coin_id]['usd']
    except:
        return None

# 🔹 Get stock price
def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        return round(stock.fast_info['lastPrice'], 2)
    except:
        return None

# 🔹 Detect crypto from any user text
def extract_crypto(text):
    all_keys = list(COINS.keys()) + list(COINS.values())
    match, score = process.extractOne(text.lower(), all_keys)
    if score >= 70:
        return COINS.get(match, match)
    return None

# 🔹 Detect stock symbol from text
def extract_stock(text):
    words = text.upper().replace("$", "").split()
    for word in words:
        if len(word) <= 5 and word.isalpha():
            price = get_stock_price(word)
            if price:
                return word, price
    return None, None

# 🟢 Telegram commands
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Ask me for crypto or stock prices. Try:\n- btc\n- show tsla\n- eth price\n- alert btc 30000")

@bot.message_handler(commands=['alert'])
def alert(message):
    try:
        _, coin, target = message.text.split()
        target = float(target)
        user = message.chat.id
        alerts.setdefault(user, {})[coin.lower()] = target
        bot.reply_to(message, f"🔔 Alert set for {coin.upper()} at ${target}")
    except:
        bot.reply_to(message, "❗ Usage: /alert btc 30000")

@bot.message_handler(func=lambda m: True)
def handle_query(message):
    text = message.text.lower()

    # Check for crypto
    coin_id = extract_crypto(text)
    if coin_id:
        price = get_crypto_price(coin_id)
        if price:
            bot.reply_to(message, f"💰 {coin_id.title()} price: ${price}")
            return

    # Check for stock
    symbol, price = extract_stock(text)
    if symbol:
        bot.reply_to(message, f"📊 {symbol.upper()} stock: ${price}")
        return

    bot.reply_to(message, "❓ Sorry, I couldn't find anything for that. Try BTC, ETH, TSLA, AAPL, etc.")

# 🌐 Webhook routes
@app.route(f"/{SECRET_PATH}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "Bot is running."

# 🔁 Background alert checker
import threading, time
def check_alerts():
    while True:
        for user, user_alerts in alerts.items():
            for coin, target in list(user_alerts.items()):
                current = get_crypto_price(COINS.get(coin, coin))
                if current and current >= target:
                    bot.send_message(user, f"🔔 {coin.upper()} hit ${current} (target was ${target})")
                    alerts[user].pop(coin)
        time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=check_alerts, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
