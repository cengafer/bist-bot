import os
import requests
import pandas as pd
import numpy as np
import ta
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# HİSSELER
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
# INDICATORS
# =========================
def indicators(df):
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["ema200"] = ta.trend.ema_indicator(df["close"], window=200)

    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    df["atr"] = ta.volatility.AverageTrueRange(
        high=df["close"], low=df["close"], close=df["close"]
    ).average_true_range()

    return df

# =========================
# WIN RATE
# =========================
def win_rate(df):
    wins = 0
    total = 0

    for i in range(50, len(df)-1):
        entry = df["close"].iloc[i]
        future = df["close"].iloc[i+1:i+6]

        tp = entry * 1.03
        sl = entry * 0.98

        if (future >= tp).any():
            wins += 1

        total += 1

    return (wins / total * 100) if total > 0 else 0

# =========================
# SCORE SYSTEM
# =========================
def score(row):
    s = 0

    # Trend
    if row["close"] > row["ema50"]:
        s += 2
    if row["ema50"] > row["ema200"]:
        s += 1

    # RSI
    if 45 < row["rsi"] < 65:
        s += 2

    # MACD
    if row["macd"] > row["macd_signal"]:
        s += 1

    return s

# =========================
# ANALYZE
# =========================
def analyze(symbol):
    df = get_data(symbol)
    if df is None or len(df) < 100:
        return None

    df = indicators(df)

    last = df.iloc[-1]

    price = round(last["close"], 2)
    rsi_val = round(last["rsi"], 2)
    win = round(win_rate(df), 2)

    s = score(last)

    # ❗ EXTREME OVERBOUGHT FILTER
    if rsi_val > 75:
        return None

    # ❗ WEAK SCORE FILTER
    if s < 3:
        return None

    return {
        "symbol": symbol,
        "price": price,
        "rsi": rsi_val,
        "win": win,
        "score": s
    }

# =========================
# REPORT
# =========================
def create_report(results):
    date = datetime.now().strftime("%Y-%m-%d")

    msg = f"🔥 PRO AKILLI TRADER BOT - {date}\n\n"

    if not results:
        return "❌ SİNYAL YOK (market zayıf olabilir)"

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    msg += "🟢 EN GÜÇLÜ SİNYALLER\n━━━━━━━━━━━━━━\n"

    for r in results[:20]:

        entry = r["price"]
        sl = round(entry * 0.97, 2)
        tp = round(entry * 1.05, 2)

        msg += f"""
🟢 {r['symbol']}

💰 Fiyat:{entry}
📊 RSI:{r['rsi']}
🎯 Entry:{entry}
🛑 SL:{sl}
🎯 TP:{tp}
📈 Win Rate:%{r['win']}
⭐ Skor:{r['score']}

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

if __name__ == "__main__":
    main()