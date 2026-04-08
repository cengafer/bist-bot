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
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except:
        pass

# ======================
# BIST 100 (TEMEL LİSTE)
# ======================
stocks = [
    "THYAO.IS","SISE.IS","KCHOL.IS","ASELS.IS","BIMAS.IS","EREGL.IS",
    "GARAN.IS","AKBNK.IS","TUPRS.IS","FROTO.IS",
    "PETKM.IS","TOASO.IS","SAHOL.IS","KOZAL.IS","ISCTR.IS",
    "YKBNK.IS","VESTL.IS","ULKER.IS","MGROS.IS","ENKAI.IS"
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
# OBV
# ======================
def calc_obv(df):
    close = df["Close"]
    volume = df["Volume"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    obv = [0]

    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])

    return obv

# ======================
# PROFESYONEL ANALİZ
# ======================
def analyze(stock):
    df = get_data(stock)
    if df is None or len(df) < 80:
        return None

    close = df["Close"]
    volume = df["Volume"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    df = pd.DataFrame({"Close": close, "Volume": volume})

    # İNDİKATÖRLER
    df["EMA20"] = ta.trend.ema_indicator(df["Close"], 20)
    df["EMA50"] = ta.trend.ema_indicator(df["Close"], 50)
    df["RSI"] = ta.momentum.rsi(df["Close"], 14)
    df["MACD"] = ta.trend.macd_diff(df["Close"])
    df["OBV"] = calc_obv(df)

    last = df.iloc[-1]

    try:
        ema20 = float(last["EMA20"])
        ema50 = float(last["EMA50"])
        rsi = float(last["RSI"])
        macd = float(last["MACD"])
        obv_now = float(df["OBV"].iloc[-1])
        obv_prev = float(df["OBV"].iloc[-2])
        price = float(df["Close"].iloc[-1])
    except:
        return None

    # ======================
    # GİRİŞ SKORU (DİP)
    # ======================
    entry = 0

    if rsi < 35:
        entry += 30
    elif rsi < 45:
        entry += 15

    if ema20 < ema50:
        entry += 20
    else:
        entry += 10

    if obv_now > obv_prev:
        entry += 20

    if macd > 0:
        entry += 10

    # ======================
    # ÇIKIŞ SKORU (TEPE)
    # ======================
    exit_score = 0

    if rsi > 70:
        exit_score += 40
    elif rsi > 60:
        exit_score += 20

    if ema20 > ema50:
        exit_score += 15

    if obv_now < obv_prev:
        exit_score += 20

    if macd < 0:
        exit_score += 10

    # ======================
    # STOP LOSS / TP
    # ======================
    stop_loss = round(price * 0.95, 2)
    take_profit = round(price * 1.10, 2)

    return round(entry), round(exit_score), rsi, price, stop_loss, take_profit

# ======================
# KARAR
# ======================
def decision(entry, exit_score):
    if entry > 55:
        return "🟢 GİRİŞ"
    elif entry > 45:
        return "🟡 DÜŞÜN"
    elif exit_score > 60:
        return "🔴 SAT"
    elif exit_score > 40:
        return "🟠 SAT DÜŞÜN"
    else:
        return "⚪ BEKLE"

# ======================
# RUN
# ======================
def run():
    buy, watch, sell = [], [], []

    for stock in stocks:
        result = analyze(stock)
        if result is None:
            continue

        entry, exit_score, rsi, price, sl, tp = result
        name = stock.replace(".IS", "")

        action = decision(entry, exit_score)

        text = f"""{name}
💰 Fiyat: {price}
📊 Entry: {entry} | Exit: {exit_score} | RSI: {round(rsi,1)}
🎯 SL: {sl} | TP: {tp}
👉 {action}"""

        if "GİRİŞ" in action:
            buy.append("🟢 " + text)
        elif "SAT" in action:
            sell.append("🔴 " + text)
        else:
            watch.append("🟡 " + text)

        time.sleep(random.uniform(1,2))

    message = f"""
📊 <b>BIST 100 PRO RAPOR</b>
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}

🟢 <b>GİRİŞ</b>
{chr(10).join(buy) if buy else "Yok"}

🟡 <b>İZLE</b>
{chr(10).join(watch) if watch else "Yok"}

🔴 <b>ÇIKIŞ</b>
{chr(10).join(sell) if sell else "Yok"}

⚠️ Bu sistem profesyonel analiz içindir, yatırım tavsiyesi değildir.
"""

    send_message(message)

if __name__ == "__main__":
    run()
