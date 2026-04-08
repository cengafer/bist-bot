import os
import requests
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import warnings

warnings.filterwarnings("ignore")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# 📂 HİSSELER
def load_stocks():
    with open("bist100.txt", "r") as f:
        return [x.strip().upper() for x in f.readlines() if x.strip()]


# 📊 VERİ
def get_data(stock):
    try:
        df = yf.download(f"{stock}.IS", period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df[["Close"]].dropna()
        df["Close"] = df["Close"].astype(float)

        if len(df) < 60:
            return None

        return df

    except:
        return None


# 🧠 ANALİZ
def analyze(stock):

    df = get_data(stock)
    if df is None:
        return None

    close = pd.Series(df["Close"].values)

    price = close.iloc[-1]

    rsi = RSIIndicator(close).rsi().iloc[-1]
    ema20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
    ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1]

    score = 0

    # RSI
    if rsi < 30:
        score += 50
    elif rsi < 40:
        score += 25
    elif rsi > 75:
        score -= 40
    elif rsi > 65:
        score -= 20

    # TREND
    if price > ema20 > ema50:
        score += 40
    elif price < ema20 < ema50:
        score -= 35

    # MOMENTUM
    if price > close.iloc[-3]:
        score += 20
    else:
        score -= 15

    return {
        "stock": stock,
        "price": price,
        "rsi": rsi,
        "score": score,
        "df": df
    }


# 🎯 SİNYAL (AGRESİF)
def signal(score):

    if score >= 60:
        return "🟢 AL"
    elif score >= 40:
        return "🟡 AL DÜŞÜN"
    elif score >= 20:
        return "⚪ BEKLE"
    elif score >= 0:
        return "🟠 SAT DÜŞÜN"
    else:
        return "🔴 SAT"


# 🧠 AI YORUM
def ai_comment(rsi, score):

    if rsi < 30:
        return "📉 DIP fırsatı"
    elif rsi > 75:
        return "⚠️ TEPE → satış riski"
    elif score > 50:
        return "🚀 güçlü trend"
    elif score > 20:
        return "⚖️ kararsız"
    else:
        return "📉 zayıf yapı"


# 📉 BACKTEST (basit)
def backtest(df):

    close = df["Close"].values

    wins = 0
    total = 0

    for i in range(len(close) - 5):
        if close[i + 5] > close[i]:
            wins += 1
        total += 1

    return round((wins / total) * 100, 2) if total > 0 else 0


# 🎯 SL TP
def risk(price):

    entry = round(price * 0.97, 2)
    exit_p = round(price * 1.03, 2)
    sl = round(price * 0.94, 2)
    tp = round(price * 1.08, 2)

    return entry, exit_p, sl, tp


# 🔗 TRADINGVIEW
def tv(stock):
    return f"https://www.tradingview.com/symbols/BIST-{stock}/"


# 📊 RAPOR
def build_report(results):

    report = "🔥 DİNAMİK TRADER BOT\n\n"

    for r in results:

        s = signal(r["score"])
        ai = ai_comment(r["rsi"], r["score"])
        win = backtest(r["df"])

        entry, exit_p, sl, tp = risk(r["price"])

        report += f"{s} {r['stock']}\n"
        report += f"💰 Fiyat: {round(r['price'],2)}\n"
        report += f"📊 Entry: {entry} | Exit: {exit_p} | RSI: {round(r['rsi'],2)}\n"
        report += f"🎯 SL: {sl} | TP: {tp}\n"
        report += f"📈 Win Rate: %{win}\n"
        report += f"{ai}\n"
        report += f"🔗 {tv(r['stock'])}\n\n"
        report += "━━━━━━━━━━━━━━\n\n"

    report += "⚠️ Yatırım tavsiyesi değildir."

    return report


# 📲 TELEGRAM
def send(msg):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    })


# 🚀 RUN
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

    # 🔥 EN İYİ 12 HİSSE
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:12]

    report = build_report(results)

    send(report)


if __name__ == "__main__":
    run()
