import os
import telebot
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# AI-style text matching (simple)
@bot.message_handler(func=lambda msg: True)
def ai_responder(message):
    text = message.text.lower()
    if "btc" in text:
        bot.reply_to(message, "₿ BTC is at $63,000 (example price).")
    elif "top crypto" in text:
        bot.reply_to(message, "Top Crypto: BTC, ETH, BNB")
    elif "top stock" in text or "stocks" in text:
        bot.reply_to(message, "Top Stocks: AAPL, MSFT, NVDA")
    else:
        bot.reply_to(message, "🤖 I'm a smart bot! Ask for BTC, stocks, crypto, or say help.")

@app.route(f"/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))