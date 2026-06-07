import yfinance as yf
import pandas as pd
from datetime import datetime
from telegram import Bot
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TOKEN)

# Hisseleri dış dosyadan oku
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
    df['RSI'] = calculate_rsi(df)
    last_row = df.iloc[-1]

    fiyat = last_row['Close']
    rsi = last_row['RSI']
    hacim = last_row['Volume']

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
    report = f"📊 Günlük BIST Analizi ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
    for stock in stocks:
        report += analyze_stock(stock) + "\n\n"

    bot.send_message(chat_id=CHAT_ID, text=report)
    print("✅ Günlük rapor ve alarm mesajları Telegram'a gönderildi.")
