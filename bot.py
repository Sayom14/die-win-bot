import ccxt
import time
import requests
from flask import Flask
import threading
import os

# --- Render-এ ফ্রিতে চালানোর জন্য ফেক সার্ভার ---
app = Flask(__name__)
@app.route('/')
def home():
    return "DIE WIN BOT IS RUNNING 24/7!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_server).start()
# -----------------------------------------------

# Firebase URL
FIREBASE_URL = "https://die-win-trader-default-rtdb.firebaseio.com"

# আপনার KuCoin API ডেটা এখানে বসান (আগের মতোই)
API_KEY = "6ae9a5480065990001dd650e"
SECRET_KEY = "6ae9a5480065990001dd650e"
API_PASSPHRASE = "sayom@0099"

exchange = ccxt.kucoin({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
})

SYMBOL = 'BTC/USDT'
in_position = False
buy_amount_btc = 0

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change); losses.append(0)
        else:
            gains.append(0); losses.append(abs(change))
            
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

print("🚀 DIE WIN - KUCOIN REAL TRADING ENGINE STARTED...")

while True:
    try:
        klines = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=15)
        closing_prices = [candle[4] for candle in klines]
        live_price = closing_prices[-1]
        current_rsi = calculate_rsi(closing_prices)

        app_req = requests.get(f"{FIREBASE_URL}/appData.json").json()
        command = app_req.get('command', 'STOP') if app_req else 'STOP'
        target_usdt = app_req.get('targetUsdt', 0) if app_req else 0

        signal = "HOLD"

        if command == "START" and target_usdt >= 1 and current_rsi < 30 and not in_position:
            signal = "BUY"
            buy_amount_btc = target_usdt / live_price
            print(f"\n[!] RSI IS {current_rsi:.1f}! EXECUTING REAL BUY ORDER OF ${target_usdt}...")
            
            order = exchange.create_market_buy_order(SYMBOL, buy_amount_btc)
            in_position = True
            print(f"[+] BOUGHT {buy_amount_btc:.5f} BTC SUCCESSFULLY!\n")

        elif in_position and current_rsi > 70:
            signal = "SELL"
            print(f"\n[!] RSI IS {current_rsi:.1f}! EXECUTING REAL SELL ORDER TO SECURE PROFIT...")
            
            order = exchange.create_market_sell_order(SYMBOL, buy_amount_btc)
            in_position = False
            
            requests.patch(f"{FIREBASE_URL}/appData.json", json={"tradeCompleted": True, "command": "STOP"})
            print("[+] SOLD SUCCESSFULLY! Profit secured. App Notified.\n")

        bot_data = {
            "price": f"{live_price:,.2f}",
            "rsi": f"{current_rsi:.1f}"
        }
        requests.put(f"{FIREBASE_URL}/botData.json", json=bot_data)
        
        status_msg = f"Holding BTC" if in_position else f"Target: ${target_usdt}" if command == "START" else "Standby"
        print(f"Live >> Price: ${live_price:,.2f} | RSI: {current_rsi:.1f} | Status: {status_msg}")

    except Exception as e:
        print(f"System Error: {e}")
    
    time.sleep(3)
