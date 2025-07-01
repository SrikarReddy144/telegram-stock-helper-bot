import requests
from flask import Flask, request
import threading
import time

TOKEN = "PLACEHOLDER"  # Replace with your bot token
ALERTS = {}

def get_crypto_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=inr"
    try:
        return requests.get(url).json()[symbol.lower()]["inr"]
    except:
        return None

def get_stock_price(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    try:
        return requests.get(url).json()["quoteResponse"]["result"][0]["regularMarketPrice"]
    except:
        return None

def check_alerts():
    while True:
        time.sleep(60)
        for chat_id in list(ALERTS):
            for symbol in list(ALERTS[chat_id]):
                current = get_crypto_price(symbol)
                target = ALERTS[chat_id][symbol]
                if current and current <= target:
                    send_message(chat_id, f"🔔 {symbol.upper()} Alert!\nCurrent: ₹{current} ≤ ₹{target}")
                    del ALERTS[chat_id][symbol]

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def handle_command(data):
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"].lower()

    if text.startswith("/start"):
        send_message(chat_id, "👋 Hi! Ask me for crypto or stock prices. Try:\n- btc\n- show AAPL\n- set alert btc 30000")
    elif text.startswith("btc") or text.startswith("eth"):
        price = get_crypto_price(text.split()[0])
        if price:
            send_message(chat_id, f"💰 {text.upper()} price: ₹{price}")
        else:
            send_message(chat_id, "❓ Sorry, couldn't fetch that.")
    elif text.startswith("show"):
        symbol = text.split()[1].upper()
        price = get_stock_price(symbol)
        if price:
            send_message(chat_id, f"📈 {symbol} stock: ₹{price}")
        else:
            send_message(chat_id, "❓ Stock not found.")
    elif text.startswith("set alert"):
        parts = text.split()
        if len(parts) == 4:
            symbol, price = parts[2], float(parts[3])
            if chat_id not in ALERTS:
                ALERTS[chat_id] = {}
            ALERTS[chat_id][symbol.lower()] = price
            send_message(chat_id, f"✅ Alert set for {symbol.upper()} at ₹{price}")
        else:
            send_message(chat_id, "❌ Invalid alert format. Try: set alert btc 30000")
    else:
        send_message(chat_id, "❓ Sorry, I couldn't find anything for that. Try BTC, ETH, TSLA, AAPL, etc.")

def handle_update(update):
    if "message" in update and "text" in update["message"]:
        handle_command(update)

# Start alert checker
threading.Thread(target=check_alerts, daemon=True).start()
