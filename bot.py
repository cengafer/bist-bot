import os
import yfinance as yf
import requests

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
# LOAD SYMBOLS
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

        if df is None or df.empty:
            return None

        close = df["Close"].dropna()

        if len(close) < 50:
            return None

        price = float(close.iloc[-1])
        rsi_val = float(rsi(close).iloc[-1])

        high_50 = float(close.tail(50).max())
        low_50 = float(close.tail(50).min())

        # =========================
        # SIGNAL
        # =========================
        signal = "🟡 BEKLE"

        if price >= high_50 * 0.98:
            signal = "🔴 SAT (ZİRVE)"

        elif rsi_val < 40:
            signal = "🔴 SAT"

        elif rsi_val > 60:
            signal = "🟢 AL"

        else:
            signal = "🟡 BEKLE"

        # =========================
        # ENTRY FIX (NO NONSENSE)
        # =========================
        entry = round(price, 2)

        sl = round(price * 0.97, 2)
        tp = round(price * 1.05, 2)

        text = f"""
{signal} {symbol.replace('.IS','')}

💰 Fiyat: {price}
📊 RSI: {round(rsi_val,2)}

🎯 Entry: {entry}
🛑 SL: {sl}
🎯 TP: {tp}
"""

        return signal, text

    except Exception as e:
        print("ERROR:", symbol, e)
        return None


# =========================
# TELEGRAM
# =========================
def send_message(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for i in range(0, len(msg), 3500):
        chunk = msg[i:i+3500]

        try:
            res = requests.post(url, data={
                "chat_id": CHAT_ID,
                "text": chunk
            })
            print(res.status_code, res.text)
        except Exception as e:
            print("TELEGRAM ERROR:", e)


# =========================
# MAIN
# =========================
def main():
    symbols = load_symbols()

    al = []
    sat = []
    bekle = []

    for s in symbols:
        result = analyze(s)

        if result is None:
            continue

        signal, text = result

        if "AL" in signal:
            al.append(text)
        elif "SAT" in signal:
            sat.append(text)
        else:
            bekle.append(text)

    report = "🔥 AKILLI TRADER BOT\n\n"

    if al:
        report += "🟢 AL\n━━━━━━━━━━━━━━\n\n" + "\n\n".join(al) + "\n\n"

    if sat:
        report += "🔴 SAT\n━━━━━━━━━━━━━━\n\n" + "\n\n".join(sat) + "\n\n"

    if bekle:
        report += "🟡 BEKLE\n━━━━━━━━━━━━━━\n\n" + "\n\n".join(bekle)

    if not al and not sat:
        report = "⚠️ Sinyal yok"

    send_message(report)
    print(report)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()