import os
import requests
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def load_stocks():
    with open("bist100.txt") as f:
        return [x.strip().upper() for x in f.readlines() if x.strip()]


# 📊 DAHA GÜNCEL VERİ
def get_data(stock):
    try:
        ticker = yf.Ticker(f"{stock}.IS")
        df = ticker.history(period="6mo", interval="1d")

        if df is None or df.empty:
            return None

        df = df[["Close"]].dropna()
        return df

    except:
        return None


# 🧠 GERÇEK ANALİZ
def analyze(stock):

    df = get_data(stock)
    if df is None:
        return None

    try:
        close = df["Close"]

        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = close.astype(float)

        price = close.iloc[-1]

        rsi = RSIIndicator(close).rsi().iloc[-1]
        ema20 = EMAIndicator(close, 20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(close, 50).ema_indicator().iloc[-1]

        # 🔥 ZİRVE KONTROLÜ
        high_90 = close[-90:].max()
        near_top = price >= high_90 * 0.97

        score = 0

        if rsi < 35:
            score += 40
        elif rsi > 70:
            score -= 30

        if price > ema20 > ema50:
            score += 40
        elif price < ema20 < ema50:
            score -= 40

        if price > close.iloc[-3]:
            score += 20
        else:
            score -= 10

        return {
            "stock": stock,
            "price": float(price),
            "rsi": float(rsi),
            "score": score,
            "near_top": near_top,
            "high_90": high_90,
            "df": df
        }

    except:
        return None


# 🎯 GERÇEK SİNYAL
def signal(r):

    if r["near_top"]:
        return "🔴 SAT (ZİRVE)"

    if r["score"] >= 60:
        return "🟢 AL"
    elif r["score"] >= 30:
        return "🟡 TAKİP"
    elif r["score"] >= 0:
        return "⚪ BEKLE"
    else:
        return "🔴 SAT"


# 🎯 AKILLI ENTRY
def entry_exit(r):

    price = r["price"]

    if r["near_top"]:
        return "-", "-", price * 0.95, price * 0.90

    entry = round(price * 0.98, 2)
    exit_p = round(price * 1.04, 2)

    sl = round(price * 0.95, 2)
    tp = round(price * 1.10, 2)

    return entry, exit_p, sl, tp


# 📊 RAPOR
def build(results):

    txt = "🔥 AKILLI TRADER BOT\n\n"

    for r in results:

        s = signal(r)
        entry, exit_p, sl, tp = entry_exit(r)

        txt += f"{s} {r['stock']}\n"
        txt += f"💰 Fiyat: {round(r['price'],2)}\n"
        txt += f"📊 RSI: {round(r['rsi'],2)}\n"
        txt += f"🎯 Entry: {entry} | Exit: {exit_p}\n"
        txt += f"🛑 SL: {round(sl,2)} | 🎯 TP: {round(tp,2)}\n"

        if r["near_top"]:
            txt += "⚠️ Tarihi zirveye yakın → kar satışı riski\n"

        txt += "\n━━━━━━━━━━━━━━\n\n"

    return txt


def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def run():

    stocks = load_stocks()

    results = []

    for s in stocks:
        r = analyze(s)
        if r:
            results.append(r)

    if not results:
        send("❌ Veri yok")
        return

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:10]

    send(build(results))


if __name__ == "__main__":
    run()