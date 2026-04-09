import yfinance as yf
import pandas as pd
import requests

# =========================
# TELEGRAM
# =========================
BOT_TOKEN = "TOKEN"
CHAT_ID = "CHAT_ID"

# =========================
# TXT OKU
# =========================
def load_symbols():
    with open("bist100.txt", "r") as f:
        lines = f.read().splitlines()

    # .IS ekle
    return [x.strip() + ".IS" for x in lines if x.strip()]

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
    returns = close.pct_change().dropna()
    wins = returns[returns > 0]
    if len(returns) == 0:
        return 0
    return round((len(wins) / len(returns)) * 100, 2)

# =========================
# ANALİZ
# =========================
def analyze(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df.empty or "Close" not in df:
            return None

        close = df["Close"].squeeze()

        price = float(close.iloc[-1])
        rsi_val = float(rsi(close).iloc[-1])
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]

        high_50 = close.tail(50).max()

        winrate = backtest(close)

        # ENTRY FIX
        entry = round(price * 0.98, 2)
        sl = round(price * 0.95, 2)
        tp = round(price * 1.10, 2)

        if price > entry:
            entry_text = f"{price} (breakout)"
        else:
            entry_text = f"{entry}"

        # =========================
        # SİNYAL MOTORU
        # =========================
        signal = "🟡 İZLE"
        comment = "⚖️ Kararsız"

        if (rsi_val > 50 and price > sma20 and price > sma50):
            signal = "🟢 AL"
            comment = "🚀 Güçlü trend"

        if price >= high_50 * 0.98:
            signal = "🔴 SAT (ZİRVE)"
            comment = "⚠️ Zirve → kar satışı"

        if price < sma50 and rsi_val < 45:
            signal = "🔴 SAT"
            comment = "📉 Düşüş trendi"

        text = f"""{signal} {symbol.replace('.IS','')}
💰 {round(price,2)}
📊 RSI: {round(rsi_val,2)}
🎯 Entry: {entry_text}
🛑 SL: {sl} | 🎯 TP: {tp}
📈 Win Rate: %{winrate}
{comment}"""

        return signal, text

    except:
        return None

# =========================
# TELEGRAM
# =========================
def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# RUN
# =========================
def run():
    symbols = load_symbols()

    buys, sells, watch = [], [], []

    for s in symbols:
        r = analyze(s)
        if r is None:
            continue

        signal, text = r

        if "🟢" in signal:
            buys.append(text)
        elif "🔴" in signal:
            sells.append(text)
        else:
            watch.append(text)

    report = "🔥 AKILLI TRADER BOT\n\n"

    if buys:
        report += "🟢 AL\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(buys) + "\n\n"

    if sells:
        report += "🔴 SAT\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(sells) + "\n\n"

    if watch:
        report += "🟡 İZLE\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(watch)

    if not buys and not sells:
        report = "⚠️ Sinyal yok (piyasa yatay)"

    send(report)
    print(report)

# =========================
# START
# =========================
if __name__ == "__main__":
    run()