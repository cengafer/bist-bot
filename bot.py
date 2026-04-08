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
# VERİ
# ======================
def get_data(stock):
    for _ in range(3):
        try:
            df = yf.download(stock, period="6mo", interval="1d", progress=False)
            if df is not None and not df.empty:
                return df
        except:
            pass
        time.sleep(random.uniform(1,2))
    return None

# ======================
# OBV (manuel)
# ======================
def calc_obv(df):
    obv = [0]
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["Close"].iloc[i-1]:
            obv.append(obv[-1] + df["Volume"].iloc[i])
        elif df["Close"].iloc[i] < df["Close"].iloc[i-1]:
            obv.append(obv[-1] - df["Volume"].iloc[i])
        else:
            obv.append(obv[-1])
    return obv

# ======================
# ANALİZ
# ======================
def analyze(stock):
    df = get_data(stock)
    if df is None or len(df) < 60:
        return None

    close = df["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    df["EMA20"] = ta.trend.ema_indicator(close, 20)
    df["EMA50"] = ta.trend.ema_indicator(close, 50)
    df["RSI"] = ta.momentum.rsi(close, 14)
    df["MACD"] = ta.trend.macd_diff(close)

    df["OBV"] = calc_obv(df)

    last = df.iloc[-1]

    ema20 = float(last["EMA20"])
    ema50 = float(last["EMA50"])
    rsi = float(last["RSI"])
    macd = float(last["MACD"])
    obv_now = float(df["OBV"].iloc[-1])
    obv_prev = float(df["OBV"].iloc[-2])

    dip_score = 0
    top_score = 0

    # ======================
    # DIP SKORU (AL)
    # ======================
    if rsi < 30:
        dip_score += 40
    elif rsi < 40:
        dip_score += 20

    if ema20 < ema50:
        dip_score += 20

    if obv_now > obv_prev:
        dip_score += 20

    if macd > 0:
        dip_score += 10

    # ======================
    # TEPE SKORU (SAT)
    # ======================
    if rsi > 70:
        top_score += 40
    elif rsi > 65:
        top_score += 25

    if ema20 > ema50:
        top_score += 15

    if obv_now < obv_prev:
        top_score += 20

    if macd < 0:
        top_score += 10

    return round(dip_score), round(top_score), round(rsi)

# ======================
# RİSK YORUMU
# ======================
def decision(dip, top):
    if dip > 60:
        return "🟢 DİP FIRSATI - AL"
    elif top > 60:
        return "🔴 TEPE - SAT"
    elif dip > top:
        return "🟡 DİBE YAKIN - TAKİP"
    else:
        return "⚪ KARARSIZ"

# ======================
# RUN
# ======================
def run():
    buy, sell, wait = [], [], []

    for stock in stocks:
        result = analyze(stock)
        if result is None:
            continue

        dip, top, rsi = result
        name = stock.replace(".IS", "")

        action = decision(dip, top)

        line = f"{name} | Dip:{dip} | Tepe:{top} | RSI:{rsi}\n👉 {action}"

        if "AL" in action:
            buy.append("🟢 " + line)
        elif "SAT" in action:
            sell.append("🔴 " + line)
        else:
            wait.append("🟡 " + line)

        time.sleep(random.uniform(1,2))

    message = f"""
📊 <b>DİP + TEPE AVCISI RAPOR</b>
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}

🟢 <b>AL (Dip)</b>
{chr(10).join(buy) if buy else "Yok"}

🟡 <b>İZLE</b>
{chr(10).join(wait) if wait else "Yok"}

🔴 <b>SAT (Tepe)</b>
{chr(10).join(sell) if sell else "Yok"}

⚠️ Yatırım tavsiyesi değildir
"""

    send_message(message)

if __name__ == "__main__":
    run()
