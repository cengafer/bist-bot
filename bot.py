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
    volume = df["Volume"]

    # Tek boyut garanti
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    # ======================
    # İNDİKATÖRLER
    # ======================
    try:
        df["EMA20"] = ta.trend.ema_indicator(close, 20)
        df["EMA50"] = ta.trend.ema_indicator(close, 50)
        df["RSI"] = ta.momentum.rsi(close, 14)
        df["MACD"] = ta.trend.macd_diff(close)
    except:
        return None

    # ======================
    # MANUEL OBV
    # ======================
    obv = [0]

    for i in range(1, len(df)):
        if close.iloc[i] > close.iloc[i - 1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i - 1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])

    df["OBV"] = obv

    last = df.iloc[-1]

    try:
        ema20 = float(last["EMA20"])
        ema50 = float(last["EMA50"])
        rsi = float(last["RSI"])
        macd = float(last["MACD"])
        obv_last = float(last["OBV"])
        obv_prev = float(df["OBV"].iloc[-2])
    except:
        return None

    # ======================
    # SKOR SİSTEMİ
    # ======================
    score = 0

    # Trend
    if ema20 > ema50:
        score += 25
    else:
        score -= 15

    # RSI
    if 50 < rsi < 65:
        score += 20
    elif rsi > 70:
        score -= 15

    # MACD
    if macd > 0:
        score += 15
    else:
        score -= 10

    # OBV (çok güçlü sinyal)
    if obv_last > obv_prev:
        score += 15
    else:
        score -= 10

    # Aşırı satım fırsatı
    if rsi < 30:
        score += 10

    return round(score, 2)

# ======================
# YORUM
# ======================
def comment(score):
    if score >= 70:
        return "🚀 Güçlü yükseliş"
    elif score >= 60:
        return "📈 Alım fırsatı"
    elif score >= 50:
        return "🟡 İzle"
    elif score >= 40:
        return "⚠️ Zayıf"
    else:
        return "📉 Düşüş"

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
        cmt = comment(score)

        line = f"🔹 {name} ({score}) - {cmt}"

        if score >= 65:
            buy.append("🟢 " + line)
        elif score <= 40:
            sell.append("🔴 " + line)
        else:
            wait.append("⚪ " + line)

        time.sleep(random.uniform(1.5, 3))

    # GENEL YORUM
    if len(buy) > len(sell):
        market_comment = "📈 Alım baskısı güçlü"
    elif len(sell) > len(buy):
        market_comment = "📉 Satış baskısı güçlü"
    else:
        market_comment = "⚖️ Piyasa kararsız"

    # MESAJ
    message = f"""
📊 <b>BIST PRO RAPOR</b>
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}

🧠 <b>PİYASA</b>
{market_comment}

🟢 <b>AL</b>
{chr(10).join(buy) if buy else "Yok"}

🔴 <b>SAT</b>
{chr(10).join(sell) if sell else "Yok"}

⚪ <b>BEKLE</b>
{chr(10).join(wait) if wait else "Yok"}

⚠️ <b>Yatırım tavsiyesi değildir</b>
"""

    send_message(message)

# ======================
# START
# ======================
if __name__ == "__main__":
    run()
