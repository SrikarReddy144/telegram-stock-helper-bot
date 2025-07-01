import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# In-memory alerts
alerts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Ask me for any stock or crypto price.\nTry:\n- `btc`\n- `show apple`\n- `set alert btc 30000`",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()
    user_id = update.message.chat_id

    if msg.startswith("set alert"):
        parts = msg.split()
        if len(parts) == 4:
            symbol = parts[2].upper()
            try:
                target = float(parts[3])
                alerts[user_id] = {'symbol': symbol, 'target': target}
                await update.message.reply_text(f"📈 Alert set for {symbol} at {target}")
                return
            except ValueError:
                pass
        await update.message.reply_text("❗ Usage: set alert btc 30000")
        return

    symbol = msg.replace("show", "").strip().upper()
    price = get_price(symbol)
    if price:
        await update.message.reply_text(f"💹 {symbol} price: {price}")
    else:
        await update.message.reply_text("❓ Sorry, I couldn't find anything for that. Try BTC, ETH, TSLA, AAPL, etc.")

def get_price(symbol):
    try:
        if symbol in ['BTC', 'ETH']:
            res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd")
            return res.json()[symbol.lower()]["usd"]
        else:
            res = requests.get(f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}")
            return res.json()["quoteResponse"]["result"][0]["regularMarketPrice"]
    except:
        return None

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    for user_id, data in alerts.items():
        price = get_price(data['symbol'])
        if price and ((price >= data['target']) if price < data['target'] else (price <= data['target'])):
            await context.bot.send_message(chat_id=user_id, text=f"🚨 {data['symbol']} reached {price}!")
            del alerts[user_id]
            break

def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(check_alerts, interval=60)

    app.run_polling()

if __name__ == "__main__":
    main()
