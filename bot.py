import yfinance as yf
import pandas as pd
import numpy as np
import requests

# =========================
# TELEGRAM AYARLARI
# =========================
BOT_TOKEN = "TOKEN_BURAYA"
CHAT_ID = "CHAT_ID_BURAYA"

# =========================
# HİSSE LİSTESİ (temiz)
# =========================
symbols = [
    "ASELS.IS","BIMAS.IS","THYAO.IS","KCHOL.IS","EREGL.IS",
    "TUPRS.IS","PETKM.IS","KRDMD.IS","ENKAI.IS","SAHOL.IS",
    "AKBNK.IS","GARAN.IS","YKBNK.IS","ISCTR.IS","SISE.IS",
    "HEKTS.IS","ODAS.IS","METRO.IS","GLYHO.IS","CIMSA.IS"
]

# =========================
# RSI
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =========================
# BACKTEST
# =========================
def backtest(close):
    returns = close.pct_change()
    wins = returns[returns > 0]
    total = returns.dropna()

    if len(total) == 0:
        return 0

    return round((len(wins) / len(total)) * 100, 2)

# =========================
# ANALİZ
# =========================
def analyze(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df.empty or "Close" not in df:
            return None

        # 1D FIX
        close = df["Close"].squeeze()

        price = float(close.iloc[-1])
        rsi_val = float(rsi(close).iloc[-1])
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]

        high_50 = close.tail(50).max()
        low_50 = close.tail(50).min()

        winrate = backtest(close)

        # =========================
        # ENTRY / SL / TP
        # =========================
        entry = round(price * 0.98, 2)
        sl = round(price * 0.95, 2)
        tp = round(price * 1.10, 2)

        # breakout fix
        if price > entry:
            entry_text = f"{price} (breakout)"
        else:
            entry_text = f"{entry}"

        # =========================
        # KARAR MOTORU (YARI AGRESİF)
        # =========================
        signal = "🟡 İZLE"
        comment = "⚖️ Kararsız yapı"

        # 🟢 AL
        if (rsi_val > 50 and price > sma20 and price > sma50):
            signal = "🟢 AL"
            comment = "🚀 Trend güçlü, momentum yukarı"

        # 🔴 SAT (zirve)
        if price >= high_50 * 0.98:
            signal = "🔴 SAT (ZİRVE)"
            comment = "⚠️ Zirveye yakın → kar satışı riski"

        # 🔴 SAT (düşüş)
        if price < sma50 and rsi_val < 45:
            signal = "🔴 SAT"
            comment = "📉 Trend aşağı → zayıf yapı"

        # =========================
        # RAPOR
        # =========================
        text = f"""{signal} {symbol.replace('.IS','')}
💰 Fiyat: {round(price,2)}
📊 RSI: {round(rsi_val,2)}
🎯 Entry: {entry_text}
🛑 SL: {sl} | 🎯 TP: {tp}
📈 Win Rate: %{winrate}
{comment}"""

        return signal, text

    except:
        return None


# =========================
# TELEGRAM GÖNDER
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# =========================
# ANA ÇALIŞMA
# =========================
def run():
    buys = []
    sells = []
    watch = []

    for s in symbols:
        result = analyze(s)
        if result is None:
            continue

        signal, text = result

        if "🟢" in signal:
            buys.append(text)
        elif "🔴" in signal:
            sells.append(text)
        else:
            watch.append(text)

    report = "🔥 AKILLI TRADER BOT\n\n"

    if buys:
        report += "🟢 AL FIRSATLARI\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(buys)
        report += "\n\n"

    if sells:
        report += "🔴 SAT / KAR AL\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(sells)
        report += "\n\n"

    if watch:
        report += "🟡 İZLE\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(watch)

    if not buys and not sells:
        report = "⚠️ Bugün güçlü sinyal yok (piyasa yatay)"

    send_telegram(report)
    print(report)


# =========================
# ÇALIŞTIR
# =========================
if __name__ == "__main__":
    run()