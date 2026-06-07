import yfinance as yf
import pandas as pd
from datetime import datetime
from telegram import Bot
import os
import asyncio

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Bot nesnesini oluşturuyoruz
bot = Bot(token=TOKEN)

added = os.getenv("ADDED", "").strip()
removed = os.getenv("REMOVED", "").strip()

if added or removed:
    mode = "diff"
    added_list = [s.strip() for s in added.split(",") if s.strip()]
    removed_list = [s.strip() for s in removed.split(",") if s.strip()]
    stocks = added_list
else:
    mode = "full"
    with open("stocks.txt") as f:
        stocks = [line.strip() for line in f if line.strip()]

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 🔧 Telegram gönderimi yeni nesil kütüphaneler için async hale getirildi
async def safe_send_message(text):
    try:
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            await bot.send_message(chat_id=CHAT_ID, text=chunk)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

async def analyze_stock(symbol):
    df = yf.download(symbol, period="15d", interval="15m")
    if df.empty:
        return f"{symbol} | Veri bulunamadı."

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['RSI'] = calculate_rsi(df)
    df.dropna(inplace=True)

    if df.empty or 'RSI' not in df.columns:
        return f"{symbol} | RSI verisi bulunamadı."

    rsi = float(df['RSI'].to_numpy()[-1])
    fiyat = float(df['Close'].to_numpy()[-1])
    hacim = int(df['Volume'].to_numpy()[-1])

    if rsi > 70:
        sinyal = "📈 Yükseliş sinyali"
        hedef = fiyat * 1.15
        stop = fiyat * 0.95
        await safe_send_message(f"🚨 {symbol} için ALARM: {sinyal} | Fiyat {fiyat:.2f}")
    elif rsi < 30:
        sinyal = "📉 Düşüş sinyali"
        hedef = fiyat * 0.85
        stop = fiyat * 1.05
        await safe_send_message(f"🚨 {symbol} için ALARM: {sinyal} | Fiyat {fiyat:.2f}")
    else:
        sinyal = "⏸ Nötr / Bekle"
        hedef = fiyat
        stop = fiyat

    if fiyat >= hedef and hedef != fiyat:
        await safe_send_message(f"🎯 {symbol} hedef fiyat {hedef:.2f} gerçekleşti!")
    if fiyat <= stop and stop != fiyat:
        await safe_send_message(f"🛑 {symbol} stop-loss {stop:.2f} tetiklendi!")

    return f"{symbol} | Fiyat: {fiyat:.2f} | RSI: {rsi:.2f} | Hacim: {hacim}\n{sinyal}\n🎯 Hedef: {hedef:.2f} | 🛑 Stop: {stop:.2f}"

async def main():
    if mode == "diff":
        report = f"📌 Değişen Hisseler ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
        if added_list:
            report += "➕ Eklenen:\n" + "\n".join(added_list) + "\n\n"
        if removed_list:
            report += "➖ Çıkarılan:\n" + "\n".join(removed_list) + "\n\n"
    else:
        report = f"📊 Günlük BIST Analizi ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"

    for stock in stocks:
        res = await analyze_stock(stock)
        report += res + "\n\n"

    await safe_send_message(report)
    print("✅ Rapor ve alarm mesajları Telegram'a gönderildi.")

if __name__ == "__main__":
    # Async ana fonksiyonu tetikliyoruz
    asyncio.run(main())
