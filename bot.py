import requests
import yfinance as yf
import ta
import time
import random
from datetime import datetime

BOT_TOKEN = "BURAYA_TOKEN"
CHAT_ID = "BURAYA_CHAT_ID"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

stocks = ["THYAO.IS","SISE.IS","KCHOL.IS","ASELS.IS","BIMAS.IS"]

def download_data(stock):
    for _ in range(3):
        try:
            df = yf.download(stock, period="6mo", interval="1d", progress=False)
            if df is not None and not df.empty:
                return df
        except:
            pass
        time.sleep(random.uniform(1,3))
    return None

def analyze(stock):
    df = download_data(stock)

    if df is None or len(df) < 50:
        return None

    df["EMA20"] = ta.trend.ema_indicator(df["Close"], 20)
    df["EMA50"] = ta.trend.ema_indicator(df["Close"], 50)
    df["RSI"] = ta.momentum.rsi(df["Close"], 14)

    last = df.iloc[-1]

    score = 0

    if last["EMA20"] > last["EMA50"]:
        score += 25

    if 45 < last["RSI"] < 60:
        score += 15

    return score

def run():
    results = []

    for s in stocks:
        score = analyze(s)
        if score:
            results.append((s, score))
        time.sleep(2)

    message = "📊 GÜNLÜK RAPOR\n\n"

    for r in results:
        message += f"{r[0]} → {r[1]}\n"

    send_message(message)

if __name__ == "__main__":
    run()
