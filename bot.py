import requests
from fuzzywuzzy import process

CRYPTO_IDS = {
    'btc': 'bitcoin', 'bitcoin': 'bitcoin',
    'eth': 'ethereum', 'ethereum': 'ethereum',
    'sol': 'solana', 'xrp': 'ripple',
    'doge': 'dogecoin', 'ada': 'cardano',
    'matic': 'polygon', 'bnb': 'binancecoin',
    'ltc': 'litecoin',
}

COMMON_TICKERS = [
    "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "NFLX", "META", "NVDA",
    "INTC", "AMD", "BA", "T", "V", "PYPL", "PEP", "KO", "JPM", "XOM", "CVX", "WMT", "NKE"
]

def fetch_crypto_price(name):
    coin_id = CRYPTO_IDS.get(name.lower())
    if not coin_id:
        return f"❓ Unknown crypto '{name}'"
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        price = data[coin_id]['usd']
        return f"💰 {coin_id.title()} price: ${price:,}"
    except:
        return f"❌ Error fetching price for '{name}'"

def fetch_stock_price(symbol):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}'
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return f"📈 {symbol.upper()} stock price: ${price:,}"
    except:
        return f"❌ Stock '{symbol.upper()}' not found."

def find_closest_ticker(query):
    result, score = process.extractOne(query.upper(), COMMON_TICKERS)
    return result if score >= 80 else query.upper()

def handle_message(msg):
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

    elif msg.isalpha() and len(msg) <= 5:
        symbol = find_closest_ticker(msg)
        return fetch_stock_price(symbol)

    else:
        return "❓ Try something like:\n- `btc`\n- `eth`\n- `show apple`\n- `tsla`"
