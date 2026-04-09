import os
import requests
import pandas as pd
import ta
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def load_symbols():
    with open("bist100.txt", "r") as f:
        return [x.strip() for x in f.readlines() if x.strip()]

def get_data(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.IS"
    r = requests.get(url).json()

    try:
        closes = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        df = pd.DataFrame({"close": closes})
        return df.dropna()
    except:
        return None

def indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    return df

def win_rate(df):
    wins = 0
    total = 0

    for i in range(30, len(df)-1):
        entry = df["close"].iloc[i]
        future = df["close"].iloc[i+1:i+6]

        if (future >= entry * 1.03).any():
            wins += 1

        total += 1

    return (wins / total * 100) if total > 0 else 0

# =========================
# SKOR SİSTEMİ (YUMUŞAK)
# =========================
def score(row):
    s = 0

    if row["close"] > row["ema50"]:
        s += 2
    if 45 < row["rsi"] < 70:
        s += 2
    if row["rsi"] < 60:
        s += 1

    return s

def analyze(symbol):
    df = get_data(symbol)
    if df is None or len(df) < 60:
        return None

    df = indicators(df)

    last = df.iloc[-1]

    price = round(last["close"], 2)
    rsi_val = round(last["rsi"], 2)
    wr = round(win_rate(df), 2)

    s = score(last)

    return {
        "symbol": symbol,
        "price": price,
        "rsi": rsi_val,
        "win": wr,
        "score": s
    }

def create_report(results):
    date = datetime.now().strftime("%Y-%m-%d")

    msg = f"🔥 AKILLI TRADER BOT - {date}\n\n"
    msg += "🟢 EN İYİ FIRSATLAR\n━━━━━━━━━━━━━━\n"

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    for r in results[:15]:

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

def main():
    symbols = load_symbols()
    results = []

    for s in symbols:
        try:
            r = analyze(s)
            if r:
                results.append(r)
        except:
            continue

    msg = create_report(results)
    send_telegram(msg)

if __name__ == "__main__":
    main()