import requests
import yfinance as yf
import pandas as pd
import ta
import time
import random
import os
from datetime import datetime

# ======================
# TELEGRAM
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

# ======================
# HİSSELER
# ======================
stocks = [
    "THYAO.IS","SISE.IS","KCHOL.IS","ASELS.IS","BIMAS.IS",
    "EREGL.IS","GARAN.IS","AKBNK.IS","TUPRS.IS","FROTO.IS"
]

# ======================
# VERİ ÇEKME
# ======================
def download_data(stock):
    for _ in range(3):
        try:
            df = yf.download(
                stock,
                period="6mo",
                interval="1d",
                progress=False,
                threads=False
            )

            if df is not None and not df.empty:
                return df

        except:
            pass

        time.sleep(random.uniform(1.5, 3))

    return None

# ======================
# ANALİZ
# ======================
def analyze(stock):
    df = download_data(stock)

    if df is None or len(df) < 50:
        return None

    close = df["Close"]

    # 🔥 FIX: 2D → 1D dönüşüm
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    df["EMA20"] = ta.trend.ema_indicator(close, 20)
    df["EMA50"] = ta.trend.ema_indicator(close, 50)
    df["RSI"] = ta.momentum.rsi(close, 14)
    df["MACD"] = ta.trend.macd_diff(close)

    last = df.iloc[-1]

    score = 0

    if last["EMA20"] > last["EMA50"]:
        score += 25

    if 45 < last["RSI"] < 60:
        score += 15

    if last["MACD"] > 0:
        score += 15

    return round(score, 2)

# ======================
# RAPOR
# ======================
def run():
    buy = []
    sell = []
    wait = []

    for stock in stocks:
        score = analyze(stock)

        if score is None:
            continue

        name = stock.replace(".IS", "")

        if score >= 65:
            buy.append(f"🟢 {name} ({score})")
        elif score <= 40:
            sell.append(f"🔴 {name} ({score})")
        else:
            wait.append(f"⚪ {name} ({score})")

        time.sleep(random.uniform(1.5, 3))

    message = f"📊 <b>BIST RAPOR</b>\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    message += "🟢 AL\n" + ("\n".join(buy) if buy else "Yok") + "\n\n"
    message += "🔴 SAT\n" + ("\n".join(sell) if sell else "Yok") + "\n\n"
    message += "⚪ BEKLE\n" + ("\n".join(wait) if wait else "Yok")

    send_message(message)

# ======================
# ÇALIŞTIR
# ======================
if __name__ == "__main__":
    run()
