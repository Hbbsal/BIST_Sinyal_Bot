import yfinance as yf
import pandas as pd
from datetime import datetime
from telegram import Bot
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TOKEN)

added = os.getenv("ADDED", "").strip()
removed = os.getenv("REMOVED", "").strip()

if added or removed:
    mode = "diff"
    added_list = [s.strip() for s in added.split(",") if s.strip()]
    removed_list = [s.strip() for s in removed.split(",") if s.strip()]
    stocks = added_list  # sadece eklenen hisseler analiz edilir
else:
    mode = "full"
    with open("stocks.txt") as f:
        stocks = [line.strip() for line in f if line.strip()]

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_stock(symbol):
    df = yf.download(symbol, period="15d", interval="15m")
    if df.empty:
        return f"{symbol} | Veri bulunamadı."

    df['RSI'] = calculate_rsi(df)
    df.dropna(inplace=True)

    if df.empty or 'RSI' not in df.columns:
        return f"{symbol} | RSI verisi bulunamadı."

    fiyat = float(df['Close'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    hacim = int(df['Volume'].iloc[-1])

    if rsi > 70:
        sinyal = "📈 Yükseliş sinyali"
        hedef = fiyat * 1.15
        stop = fiyat * 0.95
        bot.send_message(chat_id=CHAT_ID, text=f"🚨 {symbol} için ALARM: {sinyal} | Fiyat {fiyat:.2f}")
    elif rsi < 30:
        sinyal = "📉 Düşüş sinyali"
        hedef = fiyat * 0.85
        stop = fiyat * 1.05
        bot.send_message(chat_id=CHAT_ID, text=f"🚨 {symbol} için ALARM: {sinyal} | Fiyat {fiyat:.2f}")
    else:
        sinyal = "⏸ Nötr / Bekle"
        hedef = fiyat
        stop = fiyat

    if fiyat >= hedef and hedef != fiyat:
        bot.send_message(chat_id=CHAT_ID, text=f"🎯 {symbol} hedef fiyat {hedef:.2f} gerçekleşti!")
    if fiyat <= stop and stop != fiyat:
        bot.send_message(chat_id=CHAT_ID, text=f"🛑 {symbol} stop-loss {stop:.2f} tetiklendi!")

    return f"{symbol} | Fiyat: {fiyat:.2f} | RSI: {rsi:.2f} | Hacim: {hacim}\n{sinyal}\n🎯 Hedef: {hedef:.2f} | 🛑 Stop: {stop:.2f}"

if __name__ == "__main__":
    if mode == "diff":
        report = f"📌 Değişen Hisseler ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
        if added_list:
            report += "➕ Eklenen:\n" + "\n".join(added_list) + "\n\n"
        if removed_list:
            report += "➖ Çıkarılan:\n" + "\n".join(removed_list) + "\n\n"
    else:
        report = f"📊 Günlük BIST Analizi ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"

    for stock in stocks:
        report += analyze_stock(stock) + "\n\n"

    bot.send_message(chat_id=CHAT_ID, text=report)
    print("✅ Rapor ve alarm mesajları Telegram'a gönderildi.")
