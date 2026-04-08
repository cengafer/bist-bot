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

# ⚙️ AYAR
RSI_PERIOD = 14


# 📂 HİSSELER
def load_stocks():
    with open("bist100.txt", "r") as f:
        return [x.strip().upper() for x in f.readlines() if x.strip()]


# 📊 VERİ
def get_data(stock):
    try:
        df = yf.download(f"{stock}.IS", period="1y", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df[["Close"]].dropna()
        df["Close"] = df["Close"].astype(float)

        if len(df) < 100:
            return None

        return df

    except:
        return None


# 🧠 ANALİZ (YARI AGRESİF)
def analyze(stock):
    df = get_data(stock)
    if df is None:
        return None

    try:
        close = pd.Series(df["Close"].values)

        price = close.iloc[-1]

        rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
        ema20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1]

        score = 0

        # RSI (daha hassas)
        if rsi < 30:
            score += 50
        elif rsi < 40:
            score += 30
        elif rsi < 50:
            score += 10
        elif rsi > 75:
            score -= 50
        elif rsi > 65:
            score -= 25

        # Trend
        if price > ema20 > ema50:
            score += 40
        elif price < ema20 < ema50:
            score -= 35

        # Momentum
        if price > close.iloc[-3]:
            score += 25
        else:
            score -= 20

        return {
            "stock": stock,
            "price": price,
            "rsi": rsi,
            "score": score,
            "df": df
        }

    except:
        return None


# 🎯 YARI AGRESİF SİNYAL
def signal(score):

    if score >= 70:
        return "🟢 GÜÇLÜ AL"
    elif score >= 55:
        return "🟢 AL"
    elif score >= 40:
        return "🟡 AL DÜŞÜN"
    elif score >= 25:
        return "🟠 ZAYIF SAT"
    else:
        return "🔴 SAT"


# 🧠 AI YORUM
def ai_comment(rsi, score):

    if rsi < 30:
        return "🧠 DIP bölgesi → güçlü tepki ihtimali"
    elif rsi > 75:
        return "⚠️ Aşırı alım → düzeltme riski"
    elif score > 65:
        return "🚀 Güçlü trend → momentum devam"
    elif score > 45:
        return "⚖️ Orta güçte yapı"
    else:
        return "📉 Zayıf trend"


# 📉 BACKTEST
def backtest(df):
    close = df["Close"].values

    wins = 0
    trades = 0

    for i in range(50, len(close) - 5):
        if close[i] < close[i + 5]:
            wins += 1
        trades += 1

    if trades == 0:
        return 0

    return round((wins / trades) * 100, 2)


# 🎯 SL / TP
def risk(price):
    sl = round(price * 0.94, 2)
    tp = round(price * 1.08, 2)
    entry = round(price * 0.96, 2)
    exit_p = round(price * 1.02, 2)

    return entry, exit_p, sl, tp


# 🔗 TRADINGVIEW
def tv_link(stock):
    return f"https://www.tradingview.com/chart/?symbol=BIST:{stock}"


# 📊 RAPOR
def build_report(results):

    report = "🔥 YARI AGRESİF TRADER BOT\n\n"

    for r in results:

        s = signal(r["score"])
        ai = ai_comment(r["rsi"], r["score"])
        winrate = backtest(r["df"])

        entry, exit_p, sl, tp = risk(r["price"])

        report += f"{s} [{r['stock']}]({tv_link(r['stock'])})\n"
        report += f"💰 Fiyat: {round(r['price'],2)}\n"
        report += f"📊 Entry: {entry} | Exit: {exit_p} | RSI: {round(r['rsi'],2)}\n"
        report += f"🎯 SL: {sl} | TP: {tp}\n"
        report += f"📈 Win Rate: %{winrate}\n"
        report += f"{ai}\n\n"

        report += "━━━━━━━━━━━━━━\n\n"

    report += "⚠️ Yatırım tavsiyesi değildir."

    return report


# 📲 TELEGRAM
def send(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
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

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    # 🔥 YARI AGRESİF: filtre hafif
    filtered = results[:12]

    if not filtered:
        send("❌ Sinyal yok")
        return

    report = build_report(filtered)

    send(report)


if __name__ == "__main__":
    run()
