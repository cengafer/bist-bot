import os
import yfinance as yf
import requests
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# =========================
# RSI (WILDER - DOĞRU)
# =========================
def rsi(series, period=14):
    delta = series.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# =========================
# WIN RATE
# =========================
def calculate_win_rate(df):
    closes = df["Close"].dropna().values

    wins = 0
    total = 0

    for i in range(len(closes) - 15):
        entry = closes[i]
        future = closes[i+1:i+15]

        tp = entry * 1.05
        sl = entry * 0.97

        for f in future:
            if f >= tp:
                wins += 1
                break
            if f <= sl:
                break

        total += 1

    return (wins / total) * 100 if total > 0 else 0


# =========================
# SYMBOLS
# =========================
def load_symbols():
    with open("bist100.txt") as f:
        return [x.strip().upper() + ".IS" for x in f if x.strip()]


# =========================
# ANALYZE
# =========================
def analyze(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df is None or df.empty or len(df) < 50:
            return None

        close = df["Close"].dropna()

        price = float(close.iloc[-1])
        rsi_val = float(rsi(close).iloc[-1])
        win_rate = calculate_win_rate(df)

        high_50 = float(close.tail(50).max())

        # =========================
        # SIGNAL (BEKLE YOK)
        # =========================
        if price >= high_50 * 0.98:
            signal = "🔴 SAT (ZİRVE)"
        elif rsi_val < 40:
            signal = "🔴 SAT"
        else:
            signal = "🟢 AL"

        # =========================
        # FORMAT
        # =========================
        price_f = f"{price:.2f}"
        rsi_f = f"{rsi_val:.2f}"
        entry = f"{price:.2f}"
        sl = f"{price*0.97:.2f}"
        tp = f"{price*1.05:.2f}"

        text = f"""{signal} {symbol.replace('.IS','')}

💰 Fiyat: {price_f}
📊 RSI:{rsi_f}
🎯 Entry: {entry}
🛑 SL: {sl}
🎯 TP: {tp}
📈 Win Rate: %{win_rate:.2f}
"""

        return signal, text

    except:
        return None


# =========================
# TELEGRAM
# =========================
def send_message(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for i in range(0, len(msg), 3500):
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg[i:i+3500]
        })


# =========================
# MAIN
# =========================
def main():
    symbols = load_symbols()

    al, sat = [], []

    for s in symbols:
        res = analyze(s)
        if res is None:
            continue

        signal, text = res

        if "AL" in signal:
            al.append(text)
        elif "SAT" in signal:
            sat.append(text)

    today = datetime.now().strftime("%d.%m.%Y")

    report = f"🔥 AKILLI TRADER BOT - {today}\n"

    if al:
        report += "\n🟢 AL\n━━━━━━━━━━━━━━\n"
        report += "\n".join(al)

    if sat:
        report += "\n🔴 SAT\n━━━━━━━━━━━━━━\n"
        report += "\n".join(sat)

    if not al and not sat:
        report = "⚠️ Sinyal yok"

    send_message(report)
    print(report)


if __name__ == "__main__":
    main()