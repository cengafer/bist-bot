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


# 📊 VERİ ÇEK
def get_data(stock):
    try:
        df = yf.download(f"{stock}.IS", period="1y", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        if "Close" not in df.columns:
            return None

        df = df[["Close"]].dropna()
        df["Close"] = df["Close"].astype(float)

        if len(df) < 100:
            return None

        return df

    except:
        return None


# 🧠 ANALİZ (1D FIX)
def analyze(stock):
    df = get_data(stock)
    if df is None:
        return None

    try:
        close = df["Close"]

        # 🔥 1D FIX
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = pd.Series(close.values)

        price = close.iloc[-1]

        rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
        ema20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(close, window=50).ema_indicator().iloc[-1]

        score = 0

        # RSI
        if rsi < 30:
            score += 45
        elif rsi < 40:
            score += 25
        elif rsi > 70:
            score -= 30

        # Trend
        if price > ema20 > ema50:
            score += 30
        elif price < ema20 < ema50:
            score -= 20

        # Momentum
        if price > close.iloc[-5]:
            score += 15
        else:
            score -= 10

        return {
            "stock": stock,
            "price": price,
            "rsi": rsi,
            "score": score,
            "df": df
        }

    except Exception as e:
        print(f"❌ ANALYSIS ERROR {stock}: {e}")
        return None


# 🎯 SİNYAL
def signal(score):
    if score >= 60:
        return "🟢 AL (Fırsat)"
    elif score >= 40:
        return "🟡 İZLE"
    else:
        return "🔴 SAT"


# 🧠 AI YORUM
def ai_comment(rsi, score):
    if rsi > 75:
        return "⚠️ AŞIRI ALIM → TEPE RİSKİ!"
    elif rsi < 30:
        return "🧠 DIP BÖLGESİ → TOPLAMA FIRSATI"
    elif score > 60:
        return "🚀 Güçlü trend → yükseliş devam edebilir"
    elif score > 40:
        return "⚖️ Kararsız yapı"
    else:
        return "📉 Zayıf trend → satış baskısı"


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
def risk_levels(price):
    sl = round(price * 0.95, 2)
    tp = round(price * 1.10, 2)
    entry = round(price * 0.97, 2)
    exit_price = round(price * 1.03, 2)

    return entry, exit_price, sl, tp


# 🔗 TRADINGVIEW
def tv_link(stock):
    return f"https://www.tradingview.com/chart/?symbol=BIST:{stock}"


# 📊 RAPOR
def build_report(results):
    report = "🔥 DİNAMİK TRADER BOT PRO\n\n"

    for r in results:

        s = signal(r["score"])
        ai = ai_comment(r["rsi"], r["score"])
        winrate = backtest(r["df"])

        entry, exit_price, sl, tp = risk_levels(r["price"])

        # ⚠️ TEPE UYARISI
        top_warning = ""
        if r["rsi"] > 75:
            top_warning = "⚠️ DİKKAT: TEPEYE YAKIN → SAT DÜŞÜN"

        report += f"{s} [{r['stock']}]({tv_link(r['stock'])})\n"
        report += f"💰 Fiyat: {round(r['price'],2)}\n"
        report += f"📊 Entry: {entry} | Exit: {exit_price} | RSI: {round(r['rsi'],2)}\n"
        report += f"🎯 SL: {sl} | TP: {tp}\n"
        report += f"📈 Win Rate: %{winrate}\n"
        report += f"{ai}\n"

        if top_warning:
            report += f"{top_warning}\n"

        report += "\n━━━━━━━━━━━━━━\n\n"

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

    filtered = [r for r in results if r["score"] >= 35]

    if not filtered:
        send("❌ Uygun sinyal yok")
        return

    report = build_report(filtered[:10])

    send(report)


if __name__ == "__main__":
    run()
