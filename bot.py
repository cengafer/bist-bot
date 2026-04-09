import os
import requests
import pandas as pd
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
# VERİ ÇEK
# =========================
def get_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.IS"
        r = requests.get(url, timeout=10).json()

        closes = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        df = pd.DataFrame({"close": closes})

        df = df.dropna()

        # minimum veri kontrolü
        if len(df) < 20:
            return None

        return df

    except:
        return None

# =========================
# RSI
# =========================
def get_rsi(df):
    try:
        return ta.momentum.RSIIndicator(df["close"], window=14).rsi().iloc[-1]
    except:
        return 50

# =========================
# EMA
# =========================
def get_ema(df):
    try:
        window = min(50, len(df)-1)
        return ta.trend.ema_indicator(df["close"], window=window).iloc[-1]
    except:
        return df["close"].iloc[-1]

# =========================
# WIN RATE (basit)
# =========================
def get_winrate(df):
    wins = 0
    total = 0

    for i in range(10, len(df)-1):
        entry = df["close"].iloc[i]
        future = df["close"].iloc[i+1:i+5]

        if (future >= entry * 1.02).any():
            wins += 1

        total += 1

    return round((wins / total) * 100, 2) if total > 0 else 50

# =========================
# SKOR SİSTEMİ
# =========================
def calculate_score(price, rsi, ema, win):
    score = 0

    # trend
    if price > ema:
        score += 1

    # RSI
    if 40 < rsi < 70:
        score += 2

    if rsi < 60:
        score += 1

    # winrate
    if win > 50:
        score += 1

    return score

# =========================
# ANALYZE
# =========================
def analyze(symbol):
    df = get_data(symbol)

    if df is None:
        return None

    price = round(df["close"].iloc[-1], 2)
    rsi = round(get_rsi(df), 2)
    ema = get_ema(df)
    win = get_winrate(df)

    score = calculate_score(price, rsi, ema, win)

    # ekstrem koruma
    if rsi > 80:
        score -= 1

    return {
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "win": win,
        "score": score
    }

# =========================
# RAPOR
# =========================
def create_report(results):
    date = datetime.now().strftime("%Y-%m-%d")

    msg = f"🔥 FINAL TRADER BOT - {date}\n\n"
    msg += "🟢 EN İYİ SİNYALLER\n━━━━━━━━━━━━━━\n"

    results = sorted(results, key=lambda x: x["score"], reverse=True)

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
        res = analyze(s)
        if res:
            results.append(res)

    msg = create_report(results)

    print(msg)  # debug için
    send_telegram(msg)

# =========================
if __name__ == "__main__":
    main()