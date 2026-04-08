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
# ANALİZ (YARI AGRESİF)
# ======================
def analyze(stock):
    df = get_data(stock)
    if df is None or len(df) < 60:
        return None

    close = df["Close"]
    volume = df["Volume"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    df = pd.DataFrame({
        "Close": close,
        "Volume": volume
    })

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
    except:
        return None

    # ======================
    # SKOR
    # ======================
    dip = 0
    top = 0

    # RSI (ESNETİLDİ)
    if rsi < 35:
        dip += 35
    elif rsi < 45:
        dip += 20
    elif rsi > 70:
        top += 40
    elif rsi > 60:
        top += 20

    # EMA (trend desteği)
    if ema20 < ema50:
        dip += 20
    else:
        top += 20

    # MACD
    if macd > 0:
        dip += 10
    else:
        top += 10

    # OBV (para girişi)
    if obv_now > obv_prev:
        dip += 20
    else:
        top += 20

    # Momentum bonus
    if rsi > 50 and rsi < 65:
        dip += 10

    return round(dip), round(top), round(rsi)

# ======================
# KARAR
# ======================
def decision(dip, top):
    if dip >= 55:
        return "🟢 AL (Fırsat)"
    elif dip >= 45:
        return "🟡 AL DÜŞÜN"
    elif top >= 60:
        return "🔴 SAT (Tepe)"
    elif top >= 45:
        return "🟡 SAT DÜŞÜN"
    else:
        return "⚪ BEKLE"

# ======================
# RUN
# ======================
def run():
    buy, mid, sell = [], [], []

    for stock in stocks:
        result = analyze(stock)
        if result is None:
            continue

        dip, top, rsi = result
        name = stock.replace(".IS", "")

        action = decision(dip, top)

        line = f"{name} | Dip:{dip} | Tepe:{top} | RSI:{round(rsi,1)}\n👉 {action}"

        if "AL" in action:
            buy.append("🟢 " + line)
        elif "SAT" in action:
            sell.append("🔴 " + line)
        else:
            mid.append("🟡 " + line)

        time.sleep(random.uniform(1,2))

    message = f"""
📊 <b>YARI AGRESİF DİP + TEPE AVCISI</b>
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}

🟢 <b>AL</b>
{chr(10).join(buy) if buy else "Yok"}

🟡 <b>AL DÜŞÜN / İZLE</b>
{chr(10).join(mid) if mid else "Yok"}

🔴 <b>SAT</b>
{chr(10).join(sell) if sell else "Yok"}

⚠️ Yatırım tavsiyesi değildir
"""

    send_message(message)

if __name__ == "__main__":
    run()
