import requests
from fuzzywuzzy import fuzz, process

# Predefined popular crypto IDs
CRYPTO_IDS = {
    'bitcoin': 'bitcoin',
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'ethereum': 'ethereum',
    'sol': 'solana',
    'xrp': 'ripple',
    'doge': 'dogecoin',
    'ada': 'cardano',
    'matic': 'polygon',
    'bnb': 'binancecoin',
    'ltc': 'litecoin',
}

def fetch_crypto_price(name):
    coin_id = CRYPTO_IDS.get(name.lower())
    if not coin_id:
        return f"❓ Unknown crypto '{name}'"
    
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if coin_id in data:
            price = data[coin_id]['usd']
            return f"💰 {coin_id.title()} price: ${price:,}"
    except Exception as e:
        print("Crypto error:", e)
    return f"❌ Error fetching crypto price for '{name}'"

def fetch_stock_price(symbol):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}'
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return f"📈 {symbol.upper()} stock price: ${price:,}"
    except Exception:
        return f"❌ Stock '{symbol.upper()}' not found."

# Fuzzy lookup for common tickers
# A small pre-fetched list (you can expand)
COMMON_TICKERS = [
    "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "NFLX", "META", "NVDA", "INTC", "AMD",
    "BA", "T", "V", "PYPL", "PEP", "KO", "JPM", "XOM", "CVX", "WMT", "NKE"
]

def find_closest_ticker(query):
    result, score = process.extractOne(query.upper(), COMMON_TICKERS)
    if score >= 80:
        return result
    return query.upper()

def handle_user_input(msg):
    msg = msg.strip().lower()

    if msg.startswith("show "):
        name = msg[5:].strip()
        if name in CRYPTO_IDS:
            return fetch_crypto_price(name)
        else:
            symbol = find_closest_ticker(name)
            return fetch_stock_price(symbol)

    elif msg in CRYPTO_IDS:
        return fetch_crypto_price(msg)

    elif msg.isalpha() or len(msg) <= 5:
        symbol = find_closest_ticker(msg)
        return fetch_stock_price(symbol)

    else:
        return "❓ Sorry, I couldn't understand. Try `btc`, `eth`, `show apple`, `show tsla`, etc."

# ✅ Local test
if __name__ == "__main__":
    print("💹 MoneyMaster Smart Bot (Test Mode)")
    while True:
        user = input("You: ")
        print("Bot:", handle_user_input(user))
