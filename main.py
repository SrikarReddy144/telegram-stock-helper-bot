import os
import requests
from flask import Flask, request
from telebot import TeleBot, types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")
SECRET_PATH = os.getenv("SECRET_PATH")
BASE_URL = os.getenv("BASE_URL")

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
alerts = {}

def get_crypto_price(coin_name):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_name.lower()}&vs_currencies=usd"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        return data.get(coin_name.lower(), {}).get("usd")
    return None

def get_stock_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol.upper()}&apikey={STOCK_API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json().get("price")
    return None

def get_top_crypto():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        return "\n".join([f"{i+1}. {c['name']} (${c['current_price']})" for i, c in enumerate(data)])
    return "Could not fetch top crypto."

@bot.message_handler(commands=['start'])
def send_welcome(msg):
    bot.reply_to(msg, "👋 Welcome! Ask me for any stock or crypto price.\nTry:\n- btc price\n- show apple stock\n- /alert btc 30000\n- /top")

@bot.message_handler(commands=['top'])
def top_crypto(msg):
    bot.reply_to(msg, get_top_crypto())

@bot.message_handler(commands=['alert'])
def set_alert(msg):
    try:
        _, asset, price = msg.text.split()
        alerts[msg.chat.id] = (asset.lower(), float(price))
        bot.reply_to(msg, f"🔔 Alert set for {asset.upper()} at ${price}")
    except:
        bot.reply_to(msg, "⚠️ Usage: /alert btc 30000")

@bot.message_handler(func=lambda m: True)
def smart_handler(msg):
    text = msg.text.lower()
    if "price" in text or "show" in text:
        if "stock" in text:
            parts = text.split()
            for word in parts:
                if len(word) <= 5 and word.isalpha():
                    price = get_stock_price(word)
                    if price:
                        bot.reply_to(msg, f"{word.upper()} stock: ${price}")
                        return
            bot.reply_to(msg, "⚠️ Couldn't find the stock symbol.")
        else:
            parts = text.split()
            for word in parts:
                price = get_crypto_price(word)
                if price:
                    bot.reply_to(msg, f"{word.upper()} price: ${price}")
                    return
            bot.reply_to(msg, "⚠️ Couldn't find the crypto.")
    else:
        bot.reply_to(msg, "🤖 Try asking: btc price, show AAPL stock, /top or /alert btc 30000")

@app.route(f"/{SECRET_PATH}", methods=["POST"])
def webhook():
    bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "🤖 Bot is running!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{BASE_URL}/{SECRET_PATH}")
    app.run(host="0.0.0.0", port=10000)
