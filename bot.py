import ccxt
import time
import requests

# Firebase URL
FIREBASE_URL = "https://die-win-trader-default-rtdb.firebaseio.com"

# আপনার KuCoin API ডেটা এখানে বসান
API_KEY = "6ae9a5480065990001dd650e"
SECRET_KEY = "010d1379-f111-419a-8e84-89d53353f1bf"
API_PASSPHRASE = "sayom@0099"

# KuCoin Connection
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
        # ১. KuCoin থেকে লাইভ ডেটা আনা
        klines = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=15)
        closing_prices = [candle[4] for candle in klines]
        live_price = closing_prices[-1]
        current_rsi = calculate_rsi(closing_prices)

        # ২. Hopweb অ্যাপ থেকে আপনার দেওয়া কমান্ড চেক করা
        app_req = requests.get(f"{FIREBASE_URL}/appData.json").json()
        command = app_req.get('command', 'STOP') if app_req else 'STOP'
        target_usdt = app_req.get('targetUsdt', 0) if app_req else 0

        signal = "HOLD"

        # ৩. AUTO BUY লজিক (RSI < 30 হলে)
        if command == "START" and target_usdt >= 1 and current_rsi < 30 and not in_position:
            signal = "BUY"
            buy_amount_btc = target_usdt / live_price
            print(f"\n[!] RSI IS {current_rsi:.1f}! EXECUTING REAL BUY ORDER OF ${target_usdt}...")
            
            # KuCoin রিয়েল অর্ডার কমান্ড
            order = exchange.create_market_buy_order(SYMBOL, buy_amount_btc)
            in_position = True
            print(f"[+] BOUGHT {buy_amount_btc:.5f} BTC SUCCESSFULLY!\n")

        # ৪. AUTO SELL লজিক (RSI > 70 হলে)
        elif in_position and current_rsi > 70:
            signal = "SELL"
            print(f"\n[!] RSI IS {current_rsi:.1f}! EXECUTING REAL SELL ORDER TO SECURE PROFIT...")
            
            # KuCoin রিয়েল সেল কমান্ড
            order = exchange.create_market_sell_order(SYMBOL, buy_amount_btc)
            in_position = False
            
            # অ্যাপে সফলতার মেসেজ পাঠানো
            requests.patch(f"{FIREBASE_URL}/appData.json", json={"tradeCompleted": True, "command": "STOP"})
            print("[+] SOLD SUCCESSFULLY! Profit secured. App Notified.\n")

        # ৫. অ্যাপে লাইভ প্রাইস এবং RSI পাঠানো
        bot_data = {
            "price": f"{live_price:,.2f}",
            "rsi": f"{current_rsi:.1f}"
        }
        requests.put(f"{FIREBASE_URL}/botData.json", json=bot_data)
        
        # টার্মিনালে স্ট্যাটাস দেখানো
        status_msg = f"Holding BTC" if in_position else f"Target: ${target_usdt}" if command == "START" else "Standby"
        print(f"Live >> Price: ${live_price:,.2f} | RSI: {current_rsi:.1f} | Status: {status_msg}")

    except Exception as e:
        print(f"System Error: {e}")
    
    time.sleep(3)
