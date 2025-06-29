import telebot
from flask import Flask, request
import os

API_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """🤖 Hello! I can show top crypto, top stocks, and price of BTC.
Use these commands:
/btc - Get Bitcoin price
/topcrypto - Show top 5 cryptocurrencies
/topstocks - Show top 5 stocks""")

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "", 200

@app.route('/', methods=['GET'])
def index():
    return "Bot is alive!"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://your-render-url.onrender.com/" + API_TOKEN)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
