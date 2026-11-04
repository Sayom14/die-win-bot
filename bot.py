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

SYMBOL = 'PEPE/USDT'

total_coins = 0
total_spent = 0
average_price = 0

print("🚀 DIE WIN V2 - FULL AUTO ENGINE STARTED...")

while True:
    try:
        app_req = requests.get(f"{FIREBASE_URL}/appData.json").json()
        if not app_req:
            app_req = {}
            
        command = app_req.get('command', 'STOP')
        
        if command == "START":
            TAKE_PROFIT_PCT = float(app_req.get('take_profit', 0.5))
            PRICE_DROP_PCT = float(app_req.get('drop_percent', 2.0))
            TRADE_USDT = float(app_req.get('target_usdt', 1.0))

            ticker = exchange.fetch_ticker(SYMBOL)
            current_price = ticker['last']
            
            print(f"Live Price: ${current_price} | Target: {TRADE_USDT}$ | Profit: {TAKE_PROFIT_PCT}% | Drop: {PRICE_DROP_PCT}%")

            if total_coins == 0:
                print(f"Notun trade shuru hocche... {TRADE_USDT} dollarer kena hocche.")
                exchange.create_market_buy_order(SYMBOL, TRADE_USDT / current_price)
                
                total_spent = TRADE_USDT
                total_coins = TRADE_USDT / current_price
                average_price = current_price
                print(f"✅ Kena somponno! Average dam: ${average_price}")

            else:
                price_change_pct = ((current_price - average_price) / average_price) * 100
                
                if price_change_pct >= TAKE_PROFIT_PCT:
                    # Profit koto holo seta hiseb kora
                    profit_usdt = (total_coins * current_price) - total_spent
                    print(f"🎯 Profit target hit! {profit_usdt:.4f}$ lav e sell kora hocche...")
                    exchange.create_market_sell_order(SYMBOL, total_coins)
                    
                    # Firebase theke ager mot profit tene ene notun ta jog kora
                    bot_db = requests.get(f"{FIREBASE_URL}/botData.json").json() or {}
                    ager_profit = float(bot_db.get('total_profit_earned', 0.0))
                    notun_total_profit = ager_profit + profit_usdt
                    requests.patch(f"{FIREBASE_URL}/botData.json", json={"total_profit_earned": notun_total_profit})
                    
                    total_coins = 0
                    total_spent = 0
                    average_price = 0
                    print("✅ Sob sell somponno! Bot auto abar notun trade nibe...")
                    # Ekhon ar STOP hobe na, porer line-e giye abar auto kinbe!
                    
                elif price_change_pct <= -PRICE_DROP_PCT:
                    print(f"📉 Dam {price_change_pct:.2f}% komeche! Average komanor jonno abar kena hocche...")
                    exchange.create_market_buy_order(SYMBOL, TRADE_USDT / current_price)
                    
                    total_spent += TRADE_USDT
                    total_coins += (TRADE_USDT / current_price)
                    average_price = total_spent / total_coins
                    print(f"✅ Abar kena somponno! Apnar notun komano average dam: ${average_price}")

            balance_data = exchange.fetch_balance({'type': 'trade'})
            usdt_balance = balance_data['total'].get('USDT', 0.0)
            
            bot_data = {
                "price": f"{current_price:.8f}",
                "average_price": f"{average_price:.8f}",
                "balance": f"{usdt_balance:.2f}",
                "active_trade": f"{total_spent:.2f}"
            }
            requests.patch(f"{FIREBASE_URL}/botData.json", json=bot_data)
            
        else:
            print("Bot is STOPPED. App theke START korun...")

        time.sleep(10)

    except Exception as e:
        print("System Error:", e)
        time.sleep(10)
