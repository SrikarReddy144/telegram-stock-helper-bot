import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def handle_message(data):
    message = data.get("message", {})
    text = message.get("text", "").lower()
    chat_id = message.get("chat", {}).get("id")

    if not text or not chat_id:
        return

    if "btc" in text:
        send_message(chat_id, "BTC price is around $60,000.")
    elif "eth" in text:
        send_message(chat_id, "ETH price is around $3,000.")
    elif "top10" in text:
        send_message(chat_id, "Top 10 crypto: BTC, ETH, BNB, SOL, ADA, XRP, DOGE, DOT, MATIC, LTC")
    elif "stock" in text:
        send_message(chat_id, "Example stock: AAPL - $190.00")
    elif "product" in text:
        send_message(chat_id, "Example product: iPhone 14 - ₹79,999 on Amazon India")
    else:
        send_message(chat_id, "Hi! I can help you with crypto, stocks, or product prices. Try /btc or /stock.")