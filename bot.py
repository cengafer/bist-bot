import yfinance as yf
import pandas as pd
import requests

BOT_TOKEN = "TOKEN"
CHAT_ID = "CHAT_ID"

# =========================
# TXT OKU
# =========================
def load_symbols():
    with open("bist100.txt", "r") as f:
        return [x.strip() + ".IS" for x in f if x.strip()]

# =========================
# RSI
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(period).mean() / loss.rolling(period).mean()
    return 100 - (100 / (1 + rs))

# =========================
# BACKTEST
# =========================
def backtest(close):
    returns = close.pct_change().dropna()
    wins = returns[returns > 0]
    return round((len(wins) / len(returns)) * 100, 2) if len(returns) else 0

# =========================
# ANALİZ
# =========================
def analyze(symbol):
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)

        if df.empty or "Close" not in df:
            return None

        close = df["Close"].squeeze().dropna()

        if len(close) < 50:
            return None

        price = float(close.iloc[-1])
        rsi_val = float(rsi(close).iloc[-1])
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        high_50 = close.tail(50).max()
        low_50 = close.tail(50).min()

        winrate = backtest(close)

        # =========================
        # ENTRY (GEÇMİŞ YOK!)
        # =========================
        entry = price  # direkt current
        sl = round(price * 0.95, 2)
        tp = round(price * 1.10, 2)

        # =========================
        # SİNYAL MOTORU (YARI AGRESİF)
        # =========================
        signal = "🟡 İZLE"
        comment = "⚖️ Nötr"

        # 🚀 AL
        if rsi_val > 52 and price > sma20:
            signal = "🟢 AL"
            comment = "🚀 Momentum başladı"

        # 💥 GÜÇLÜ AL
        if rsi_val > 60 and price > sma20 and price > sma50:
            signal = "🔥 GÜÇLÜ AL"
            comment = "📈 Trend güçlü"

        # 🔴 ZİRVE SAT
        if price >= high_50 * 0.97:
            signal = "🔴 SAT (ZİRVE)"
            comment = "⚠️ Tepeden satılabilir"

        # 📉 DÜŞÜŞ
        if price < sma50 and rsi_val < 45:
            signal = "🔴 SAT"
            comment = "📉 Trend aşağı"

        text = f"""{signal} {symbol.replace('.IS','')}
💰 {round(price,2)}
📊 RSI: {round(rsi_val,2)}
🎯 Entry: {round(entry,2)}
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

    buys, strong, sells, watch = [], [], [], []

    for s in symbols:
        r = analyze(s)
        if r is None:
            continue

        signal, text = r

        if "🔥" in signal:
            strong.append(text)
        elif "🟢" in signal:
            buys.append(text)
        elif "🔴" in signal:
            sells.append(text)
        else:
            watch.append(text)

    report = "🔥 AKILLI TRADER BOT\n\n"

    if strong:
        report += "🔥 GÜÇLÜ AL\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(strong) + "\n\n"

    if buys:
        report += "🟢 AL\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(buys) + "\n\n"

    if sells:
        report += "🔴 SAT\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(sells) + "\n\n"

    if watch:
        report += "🟡 İZLE\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(watch)

    if not strong and not buys and not sells:
        report = "⚠️ Bugün güçlü sinyal yok"

    send(report)
    print(report)

# =========================
# START
# =========================
if __name__ == "__main__":
    run()