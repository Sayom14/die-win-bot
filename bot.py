import ccxt
import time
import requests
from flask import Flask
import threading
import os

# --- Render-er jonno Fake Server ---
app = Flask(__name__)
@app.route('/')
def home():
    return "DIE WIN BOT IS RUNNING V2!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_server).start()
# -----------------------------------

FIREBASE_URL = "https://die-win-trader-default-rtdb.firebaseio.com"

# Ekhane apnar KuCoin API data boshan
API_KEY = "6ae9a5480065990001dd650e"
SECRET_KEY = "010d1379-f111-419a-8e84-89d53353f1bf"
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
active_trade_usdt = 0 # Koto dollar-er trade cholche tar hisab

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

print("🚀 DIE WIN V2 - ADVANCED TRADING ENGINE STARTED...")

while True:
    try:
        # Original Trading Balance check kora
        balance_data = exchange.fetch_balance()
        usdt_balance = balance_data['free'].get('USDT', 0.0)

        klines = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=15)
        closing_prices = [candle[4] for candle in klines]
        live_price = closing_prices[-1]
        current_rsi = calculate_rsi(closing_prices)

        app_req = requests.get(f"{FIREBASE_URL}/appData.json").json()
        command = app_req.get('command', 'STOP') if app_req else 'STOP'
        target_usdt = app_req.get('targetUsdt', 0) if app_req else 0

        # RSI 40 er kom asle Buy korbe (Updated)
        if command == "START" and target_usdt >= 1 and current_rsi < 40 and not in_position:
            if usdt_balance >= target_usdt:
                buy_amount_btc = target_usdt / live_price
                active_trade_usdt = target_usdt
                print(f"\n[!] RSI IS {current_rsi:.1f} (< 40)! EXECUTING BUY OF ${target_usdt}...")
                
                exchange.create_market_buy_order(SYMBOL, buy_amount_btc)
                in_position = True
            else:
                print(f"[X] Insufficient Balance! You need ${target_usdt} but have ${usdt_balance}")

        elif in_position and current_rsi > 70:
            print(f"\n[!] RSI IS {current_rsi:.1f}! SELLING TO SECURE PROFIT...")
            exchange.create_market_sell_order(SYMBOL, buy_amount_btc)
            in_position = False
            active_trade_usdt = 0
            
            requests.patch(f"{FIREBASE_URL}/appData.json", json={"tradeCompleted": True, "command": "STOP"})

        # Firebase-e notun data pathano (Balance & Active Trade)
        bot_data = {
            "price": f"{live_price:,.2f}",
            "rsi": f"{current_rsi:.1f}",
            "balance": f"{usdt_balance:.2f}",
            "active_trade": f"{active_trade_usdt:.2f}"
        }
        requests.put(f"{FIREBASE_URL}/botData.json", json=bot_data)

    except Exception as e:
        print(f"System Error: {e}")
    
    time.sleep(3)
