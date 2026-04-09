import os
import requests
import pandas as pd
import numpy as np
import ta
from datetime import datetime

# =========================
# TELEGRAM
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
# DATA
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
# RSI
# =========================
def rsi(df):
    return ta.momentum.RSIIndicator(df["close"], window=14).rsi().iloc[-1]

# =========================
# WIN RATE (BASIC BACKTEST)
# =========================
def win_rate(df):
    wins = 0
    total = 0

    for i in range(20, len(df)-1):
        entry = df["close"].iloc[i]
        future = df["close"].iloc[i+1:i+6]

        tp = entry * 1.03
        sl = entry * 0.98

        if (future >= tp).any():
            wins += 1

        total += 1

    return (wins / total * 100) if total > 0 else 0

# =========================
# SCORE SYSTEM (EN ÖNEMLİ KISIM)
# =========================
def score_signal(rsi_val, win):
    score = 0

    if 40 < rsi_val < 70:
        score += 1

    if win > 45:
        score += 1

    if rsi_val < 60:
        score += 1

    return score

# =========================
# ANALYZE
# =========================
def analyze(symbol):
    df = get_data(symbol)
    if df is None or len(df) < 50:
        return None

    price = round(df["close"].iloc[-1], 2)
    rsi_val = round(rsi(df), 2)
    win = round(win_rate(df), 2)

    score = score_signal(rsi_val, win)

    # ❗ ZİRVE FİLTRESİ (çok önemli)
    if rsi_val > 72:
        return None

    if score < 2:
        return None

    sl = round(price * 0.97, 2)
    tp = round(price * 1.05, 2)

    return {
        "symbol": symbol,
        "price": price,
        "rsi": rsi_val,
        "sl": sl,
        "tp": tp,
        "win": win
    }

# =========================
# RAPOR
# =========================
def create_report(results):
    date = datetime.now().strftime("%Y-%m-%d")

    msg = f"🔥 AKILLI TRADER BOT - {date}\n\n"

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
📈 Win Rate:%{r['win']}

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
# RUN
# =========================
if __name__ == "__main__":
    main()