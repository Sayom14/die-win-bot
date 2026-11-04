import ccxt
import time
import requests
from flask import Flask
import threading
import os

# --- Render-er jonno Server ---
app = Flask(__name__)
@app.route('/')
def home():
    return "DIE WIN BOT IS RUNNING V2!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_server).start()
# --------------------------------

FIREBASE_URL = "https://die-win-trader-default-rtdb.firebaseio.com"

# Niche apnar KuCoin API data bosan
API_KEY = "6ae9f4c10065990001dd66a7"
SECRET_KEY = "bc471e6c-9b88-47cd-a983-aa801d08dc03"
API_PASSPHRASE = "SaYom@0099"

exchange = ccxt.kucoin({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
})

SYMBOL = 'BTC/USDT'

# --- Notun Average (DCA) Trading Logic ---

TAKE_PROFIT_PCT = 1.0  # 1% lav hole sob sell korbe
PRICE_DROP_PCT = 2.0   # Dam 2% komle average korar jonno abar kinbe
TRADE_USDT = 1         # Protibar koto dollarer kinbe (1 dollar)

total_coins = 0
total_spent = 0
average_price = 0

print("🚀 DIE WIN V2 - FAST AVERAGE (DCA) ENGINE STARTED...")

while True:
    try:
        # Firebase theke balance update kora
        balance_data = exchange.fetch_balance({'type': 'trade'})
        usdt_balance = balance_data['total'].get('USDT', 0.0)
        requests.patch(f"{FIREBASE_URL}/botData.json", json={"balance": usdt_balance})

        # Bortoman dam check kora
        ticker = exchange.fetch_ticker(SYMBOL)
        current_price = ticker['last']
        
        print(f"Bortoman dam: ${current_price}")

        if total_coins == 0:
            # 1. Jodi kono coin kena na thake, tahole prothom trade nibe
            print(f"Notun trade shuru hocche... {TRADE_USDT} dollarer kena hocche.")
            # exchange.create_market_buy_order(SYMBOL, TRADE_USDT / current_price)
            
            total_spent = TRADE_USDT
            total_coins = TRADE_USDT / current_price
            average_price = current_price
            print(f"✅ Kena somponno! Average dam: ${average_price}")

        else:
            # 2. Profit hiseb kora (bortoman dam average damer cheye koto % upore ba niche ache)
            price_change_pct = ((current_price - average_price) / average_price) * 100
            
            if price_change_pct >= TAKE_PROFIT_PCT:
                # 3. Lav hole sob sell kore dewa (Average System)
                print(f"🎯 Profit target hit! {price_change_pct:.2f}% lave sob sell kora hocche...")
                # exchange.create_market_sell_order(SYMBOL, total_coins)
                
                total_coins = 0
                total_spent = 0
                average_price = 0
                print("✅ Sob sell somponno! Notun trade-er jonno prostut.")
                
            elif price_change_pct <= -PRICE_DROP_PCT:
                # 4. Dam kome gele abar kena (Average komanor jonno)
                print(f"📉 Dam {price_change_pct:.2f}% komeche! Average komanor jonno abar kena hocche...")
                # exchange.create_market_buy_order(SYMBOL, TRADE_USDT / current_price)
                
                # Notun average hiseb kora
                total_spent += TRADE_USDT
                total_coins += (TRADE_USDT / current_price)
                average_price = total_spent / total_coins
                print(f"✅ Abar kena somponno! Apnar notun komano average dam: ${average_price}")

        # Firebase-e data pathano
        bot_data = {
            "price": f"{current_price:.2f}",
            "rsi": "N/A", # Ekhon ar RSI nai
            "balance": f"{usdt_balance:.2f}",
            "active_trade": f"{total_spent:.2f}"
        }
        requests.patch(f"{FIREBASE_URL}/botData.json", json=bot_data)

        time.sleep(10) # Proti 10 second por por market check korbe

    except Exception as e:
        print("System Error:", e)
        time.sleep(10)
