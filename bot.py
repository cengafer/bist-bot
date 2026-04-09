import os
import yfinance as yf
import pandas as pd
import requests
import time

# =========================
# ENV (GitHub Secrets)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# SYMBOLS
# =========================
def load_symbols():
    with open("bist100.txt", "r") as f:
        return [x.strip().upper() + ".IS" for x in f if x.strip()]

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
# WIN RATE (backtest)
# =========================
def win_rate(close):
    returns = close.pct_change().dropna()
    if len(returns) == 0:
        return 0
    wins = returns[returns > 0]
    return round(len(wins) / len(returns) * 100, 2)

# =========================
# ANALYZE
# =========================
def analyze(symbol):
    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        close = df["Close"].dropna().squeeze()

        if len(close) < 60:
            return None

        price = float(close.iloc[-1])

        rsi_val = float(rsi(close).iloc[-1])
        sma20 = float(close.rolling(20).mean().iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1])
        high_50 = float(close.tail(50).max())

        wr = win_rate(close)

        # 🔥 ENTRY (GEÇMİŞ DEĞİL)
        entry = round(price * 0.995, 2)

        sl = round(price * 0.97, 2)
        tp = round(price * 1.06, 2)

        # =========================
        # SIGNAL LOGIC
        # =========================
        signal = "🟡 BEKLE"
        note = "⚖️ Nötr"

        if price >= high_50 * 0.97:
            signal = "🔴 SAT (ZİRVE)"
            note = "⚠️ Zirveye yakın"

        elif rsi_val > 60 and price > sma20:
            signal = "🟢 AL"
            note = "📈 Trend yukarı"

        elif rsi_val < 40 and price < sma20:
            signal = "🔴 SAT"
            note = "📉 Zayıf trend"

        else:
            signal = "🟡 BEKLE"
            note = "⏳ Net sinyal yok"

        text = f"""
{signal} {symbol.replace('.IS','')}

💰 Fiyat: {round(price,2)}
📊 RSI: {round(rsi_val,2)}

🎯 Entry: {entry}
🛑 SL: {sl}
🎯 TP: {tp}

📈 Win Rate: %{wr}

{note}
"""

        return signal, text

    except Exception as e:
        print("ERROR:", symbol, e)
        return None

# =========================
# TELEGRAM
# =========================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    # uzun mesaj böl
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]

        try:
            res = requests.post(url, data={
                "chat_id": CHAT_ID,
                "text": chunk
            })

            print("STATUS:", res.status_code)
            print("RESPONSE:", res.text)

        except Exception as e:
            print("TELEGRAM ERROR:", e)

        time.sleep(1)

# =========================
# MAIN
# =========================
def main():
    symbols = load_symbols()

    al_list = []
    sat_list = []
    bekle_list = []

    for s in symbols:
        result = analyze(s)

        if result is None:
            continue

        signal, text = result

        if "AL" in signal:
            al_list.append(text)
        elif "SAT" in signal:
            sat_list.append(text)
        else:
            bekle_list.append(text)

    report = "🔥 AKILLI TRADER BOT\n\n"

    if al_list:
        report += "🟢 AL\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(al_list) + "\n\n"

    if sat_list:
        report += "🔴 SAT\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(sat_list) + "\n\n"

    if bekle_list:
        report += "🟡 BEKLE\n━━━━━━━━━━━━━━\n\n"
        report += "\n\n━━━━━━━━━━━━━━\n\n".join(bekle_list)

    if not (al_list or sat_list):
        report = "⚠️ Sinyal yok"

    send_message(report)
    print(report)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()