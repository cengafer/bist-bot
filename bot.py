import os
import yfinance as yf
import requests
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


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
        # SIGNAL
        # =========================
        if price >= high_50 * 0.98:
            signal = "🔴 SAT (ZİRVE)"
        elif rsi_val < 40:
            signal = "🔴 SAT"
        elif rsi_val > 60:
            signal = "🟢 AL"
        else:
            signal = "🟡 BEKLE"

        # =========================
        # ENTRY (CLEAN)
        # =========================
        entry = round(price, 2)
        sl = round(price * 0.97, 2)
        tp = round(price * 1.05, 2)

        # =========================
        # FORMAT (GÖZ YORMAZ)
        # =========================
        text = f"""{signal} {symbol.replace('.IS','')}

💰 Fiyat: {price}
📊 RSI: {round(rsi_val,2)}
🎯 Entry: {entry}
🛑 SL: {sl}
🎯 TP: {tp}
📈 Win Rate: %{round(win_rate,2)}
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

    al = []
    sat = []
    bekle = []

    for s in symbols:
        res = analyze(s)

        if res is None:
            continue

        signal, text = res

        if "AL" in signal:
            al.append(text)
        elif "SAT" in signal:
            sat.append(text)
        else:
            bekle.append(text)

    # =========================
    # DATE HEADER
    # =========================
    today = datetime.now().strftime("%d.%m.%Y")

    report = f"🔥 AKILLI TRADER BOT - {today}\n"

    # =========================
    # AL
    # =========================
    if al:
        report += "\n🟢 AL\n━━━━━━━━━━━━━━\n"
        report += "\n".join(al)

    # =========================
    # SAT
    # =========================
    if sat:
        report += "\n🔴 SAT\n━━━━━━━━━━━━━━\n"
        report += "\n".join(sat)

    # =========================
    # BEKLE
    # =========================
    if bekle:
        report += "\n🟡 BEKLE\n━━━━━━━━━━━━━━\n"
        report += "\n".join(bekle)

    if not al and not sat and not bekle:
        report = "⚠️ Sinyal yok"

    send_message(report)
    print(report)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()