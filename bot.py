import os
import requests
import pandas as pd
import numpy as np
import ta
import time
from datetime import datetime

# =========================
# TELEGRAM AYARLARI
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# HİSSE LİSTESİ
# =========================
def load_symbols():
    with open("bist100.txt", "r") as f:
        return [x.strip() for x in f.readlines() if x.strip()]

# =========================
# VERİ ÇEKME (ÖRNEK YAHOO)
# =========================
def get_data(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.IS"
    r = requests.get(url).json()

    try:
        closes = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        df = pd.DataFrame({"close": closes})
        return df.dropna()
    except:
        return None

# =========================
# RSI HESAPLA
# =========================
def calculate_rsi(df):
    return ta.momentum.RSIIndicator(df["close"], window=14).rsi().iloc[-1]

# =========================
# SQUEEZE MOMENTUM
# =========================
def squeeze_momentum(df):
    bb = ta.volatility.BollingerBands(df["close"])
    width = bb.bollinger_hband() - bb.bollinger_lband()
    return width.iloc[-1]

# =========================
# WIN RATE BACKTEST
# =========================
def backtest(df):
    win = 0
    total = 0

    for i in range(20, len(df)-1):
        entry = df["close"].iloc[i]
        future = df["close"].iloc[i+1:i+6]

        tp = entry * 1.03
        sl = entry * 0.98

        if (future >= tp).any():
            win += 1
        elif (future <= sl).any():
            pass

        total += 1

    if total == 0:
        return 0

    return (win / total) * 100

# =========================
# SİNYAL ÜRET
# =========================
def analyze(symbol):
    df = get_data(symbol)
    if df is None or len(df) < 50:
        return None

    price = round(df["close"].iloc[-1], 2)
    rsi = round(calculate_rsi(df), 2)
    winrate = round(backtest(df), 2)
    squeeze = squeeze_momentum(df)

    # ❌ FİLTRELER
    if rsi > 68:
        return None

    if squeeze < 0.5:
        return None

    if winrate < 50:
        return None

    # 🎯 LEVELS
    sl = round(price * 0.97, 2)
    tp = round(price * 1.05, 2)

    return {
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "sl": sl,
        "tp": tp,
        "winrate": winrate
    }

# =========================
# RAPOR OLUŞTUR
# =========================
def create_report(results):
    today = datetime.now().strftime("%Y-%m-%d")

    msg = f"🔥 AKILLI TRADER BOT - {today}\n\n"

    if not results:
        msg += "❌ SİNYAL YOK\n"
        return msg

    msg += "🟢 AL SİNYALLERİ\n━━━━━━━━━━━━━━\n"

    for r in results:
        msg += f"""
🟢 AL {r['symbol']}

💰 Fiyat:{r['price']}
📊 RSI:{r['rsi']}
🎯 Entry:{r['price']}
🛑 SL:{r['sl']}
🎯 TP:{r['tp']}
📈 Win Rate:%{r['winrate']}

"""

    return msg

# =========================
# MAIN
# =========================
def main():
    symbols = load_symbols()
    results = []

    for s in symbols:
        try:
            res = analyze(s)
            if res:
                results.append(res)
        except:
            continue

    msg = create_report(results)
    send_telegram(msg)

# =========================
# ÇALIŞTIR
# =========================
if __name__ == "__main__":
    main()