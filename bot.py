import os
import requests
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

# 🔐 ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ⚙️ AYAR
RSI_PERIOD = 14


# 📊 BIST LISTESI
def load_stocks():
    with open("bist100.txt", "r") as f:
        return [x.strip().upper() for x in f.readlines() if x.strip()]


# 📈 DATA ÇEK
def get_data(stock):
    symbol = f"{stock}.IS"

    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df.dropna()

        # güvenlik: tek kolon vs bug fix
        if isinstance(df, pd.DataFrame) and len(df.columns) > 1:
            df = df.copy()

        return df

    except Exception as e:
        print(f"❌ DATA ERROR {stock}: {e}")
        return None


# 🧠 ANALİZ
def analyze(stock):
    df = get_data(stock)

    if df is None or len(df) < 30:
        return None

    close = df["Close"]

    try:
        # RSI
        rsi = RSIIndicator(close, window=RSI_PERIOD).rsi().iloc[-1]

        # EMA
        ema20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1]

        price = close.iloc[-1]

        # skor sistemi
        score = 0

        # RSI
        if rsi < 35:
            score += 40
        elif rsi < 45:
            score += 25
        elif rsi > 65:
            score -= 25

        # trend
        if price > ema20 > ema50:
            score += 30
        elif price < ema20 < ema50:
            score -= 20

        # momentum
        if price > close.iloc[-5]:
            score += 15
        else:
            score -= 10

        return {
            "stock": stock,
            "score": int(score),
            "rsi": round(rsi, 2),
            "price": round(price, 2)
        }

    except Exception as e:
        print(f"❌ ANALYSIS ERROR {stock}: {e}")
        return None


# 🎯 SINIF
def classify(score):
    if score >= 60:
        return "🟢 AL"
    elif score >= 40:
        return "🟡 İZLE"
    else:
        return "🔴 SAT"


# 🔗 TRADINGVIEW
def tv_link(stock):
    return f"https://www.tradingview.com/chart/?symbol=BIST:{stock}"


# 📊 RAPOR
def build_report(results):
    report = "📊 BIST 100 PRO RAPOR\n\n"

    for r in results:
        stock = r["stock"]
        score = r["score"]
        rsi = r["rsi"]
        price = r["price"]

        signal = classify(score)
        link = tv_link(stock)

        report += f"{signal} [{stock}]({link})\n"
        report += f"💰 {price} | RSI: {rsi} | Skor: {score}\n\n"

    report += "⚠️ Yatırım tavsiyesi değildir."

    return report


# 📲 TELEGRAM
def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ TOKEN veya CHAT_ID eksik")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ TELEGRAM ERROR: {e}")


# 🚀 MAIN
def run():
    stocks = load_stocks()

    results = []

    for stock in stocks:
        res = analyze(stock)
        if res:
            results.append(res)

    if not results:
        send_telegram("❌ Veri bulunamadı")
        return

    # sıralama
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    # en iyi 15
    report = build_report(results[:15])

    send_telegram(report)


if __name__ == "__main__":
    run()
