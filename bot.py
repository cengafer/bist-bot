import os
import requests
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import warnings

warnings.filterwarnings("ignore")

# 🔐 ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ⚙️ AYARLAR
RSI_PERIOD = 14


# 📂 HİSSE LİSTESİ
def load_stocks():
    with open("bist100.txt", "r") as f:
        return [x.strip().upper() for x in f.readlines() if x.strip()]


# 📊 VERİ ÇEK
def get_data(stock):
    symbol = f"{stock}.IS"

    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        # multi-index fix
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if "Close" not in df.columns:
            return None

        df = df[["Close"]].copy()
        df["Close"] = df["Close"].astype(float)

        df = df.dropna()

        if len(df) < 50:
            return None

        return df

    except:
        return None


# 🧠 ANALİZ
def analyze(stock):
    df = get_data(stock)

    if df is None:
        return None

    try:
        close = pd.Series(df["Close"].values)

        # indikatörler
        rsi = RSIIndicator(close, window=RSI_PERIOD).rsi().iloc[-1]
        ema20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1]

        price = close.iloc[-1]

        score = 0

        # RSI
        if rsi < 30:
            score += 45
        elif rsi < 40:
            score += 30
        elif rsi > 70:
            score -= 30

        # Trend
        if price > ema20 > ema50:
            score += 30
        elif price < ema20 < ema50:
            score -= 20

        # Momentum
        if len(close) > 5:
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

    except:
        return None


# 🎯 SINIFLANDIRMA
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
    report = "📊 BIST 100 PRO BOT\n\n"

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
        print("❌ BOT_TOKEN veya CHAT_ID eksik")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"❌ TELEGRAM ERROR: {e}")


# 🚀 RUN
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

    # en iyi sinyaller
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    # sadece güçlü sinyaller
    strong = [r for r in results if r["score"] >= 40]

    # rapor
    report = build_report(strong[:15])

    send_telegram(report)


if __name__ == "__main__":
    run()
