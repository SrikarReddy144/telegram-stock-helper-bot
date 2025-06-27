import os
import telebot
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Helpers
def get_top_cryptos():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
    r = requests.get(url, params=params).json()
    table = "Top 10 Cryptos\n"
    table += "{:<6} {:<10} {:<10}\n".format("Rank", "Name", "Price")
    for i, coin in enumerate(r, 1):
        table += "{:<6} {:<10} ${:<10,.2f}\n".format(i, coin['symbol'].upper(), coin['current_price'])
    return table

def get_top_stocks():
    # Sample fallback (no real API key)
    stocks = [
        {"symbol": "AAPL", "price": 210.12},
        {"symbol": "MSFT", "price": 332.67},
        {"symbol": "GOOGL", "price": 142.35},
        {"symbol": "AMZN", "price": 121.93},
        {"symbol": "NVDA", "price": 1200.13},
        {"symbol": "META", "price": 500.31},
        {"symbol": "TSLA", "price": 180.72},
        {"symbol": "BRK-A", "price": 622100.00},
        {"symbol": "V", "price": 280.90},
        {"symbol": "UNH", "price": 470.51},
    ]
    table = "Top 10 Stocks (sample)\n"
    table += "{:<6} {:<10} {:<10}\n".format("Rank", "Symbol", "Price")
    for i, stock in enumerate(stocks, 1):
        table += "{:<6} {:<10} ${:<10,.2f}\n".format(i, stock['symbol'], stock['price'])
    return table

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "🤖 Hello! I can show top crypto, top stocks, and price of BTC.
Try:
- top crypto
- top stocks
- btc price
")

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    text = message.text.lower()

    if "top crypto" in text or "top coins" in text or "cryptp" in text:
        bot.send_message(message.chat.id, get_top_cryptos(), parse_mode="Markdown")
    elif "top stock" in text or "stok" in text:
        bot.send_message(message.chat.id, get_top_stocks(), parse_mode="Markdown")
    elif "btc" in text or "bitcoin" in text:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        price = r.json().get("bitcoin", {}).get("usd", "N/A")
        bot.send_message(message.chat.id, f"💰 BTC Price: ${price}")
    else:
        bot.send_message(message.chat.id, "⚠️ I didn't understand. Try:
- top crypto
- top stocks
- btc price")

bot.polling()
