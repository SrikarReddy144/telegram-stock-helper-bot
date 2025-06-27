import telebot
from flask import Flask
import threading
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 Bot is working!")

def run_bot():
    print("Bot polling started...")
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))