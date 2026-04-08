import os
import requests
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

# 🔐 ENV (GitHub Secrets)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📊 AYARLAR
RSI_PERIOD = 14


# 📌 TradingView link
def tv_link(stock):
    return f"https://www.tradingview.com/chart/?symbol=BIST:{stock}"


# 📌 BIST listesi
def load_stocks():
    with open("bist100.txt", "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]


# 📊 Veri çek
def get_data(stock):
    df = yf.download(f"{stock}.IS", period="6mo", interval="1d")

    if df.empty:
        return None

    df.dropna(inplace=True)
    return df


# 🧠 ANALİZ
def analyze(stock):
    df = get_data(stock)

    if df is None or len(df) < 20:
        return None

    close = df["Close"]

    # RSI
    rsi = RSIIndicator(close, window=RSI_PERIOD).rsi().iloc[-1]

    # EMA
    ema = EMAIndicator(close, window=20).ema_indicator()
    trend_up = close.iloc[-1] > ema.iloc[-1]

    # skor sistemi
    score = 0

    # RSI katkısı
    if rsi < 35:
        score += 40
    elif rsi < 45:
        score += 30
    elif rsi < 55:
        score += 10
    elif rsi > 65:
        score -= 30

    # trend katkısı
    if trend_up:
        score += 30
    else:
        score -= 20

    # momentum
    if close.iloc[-1] > close.iloc[-5]:
        score += 20
    else:
        score -= 10

    return {
        "stock": stock,
        "score": score,
        "rsi": round(rsi, 2),
        "price": round(close.iloc[-1], 2)
    }


# 🧠 SINIFLANDIR
def classify(score):
    if score >= 60:
        return "🟢 AL"
    elif score >= 40:
        return "🟡 İZLE"
    else:
        return "🔴 SAT"


# 📊 RAPOR
def build_report(results):
    report = "📊 BIST 100 RAPOR\n\n"

    for r in results:
        stock = r["stock"]
        score = r["score"]
        rsi = r["rsi"]
        price = r["price"]

        signal = classify(score)
        link = tv_link(stock)

        report += f"{signal} [{stock}]({link})\n"
        report += f"💰 {price} | RSI: {rsi} | Score: {score}\n\n"

    return report


# 📲 TELEGRAM
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    requests.post(url, data=data)


# 🚀 MAIN
def run():
    stocks = load_stocks()
    results = []

    for stock in stocks:
        try:
            res = analyze(stock)
            if res:
                results.append(res)
        except:
            continue

    if not results:
        send_telegram("❌ Veri alınamadı")
        return

    # skor sıralama
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    report = build_report(results[:15])  # en iyi 15

    send_telegram(report)


if __name__ == "__main__":
    run()
