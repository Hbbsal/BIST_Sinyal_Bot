import os
import yfinance as yf
import ta
from telegram import Bot

def bist_stratos_analiz(hisse):
    data = yf.download(f"{hisse}.IS", period="6mo", interval="1d")
    fiyat = data["Close"].iloc[-1]

    data["EMA20"] = ta.trend.EMAIndicator(data["Close"], window=20).ema_indicator()
    data["EMA50"] = ta.trend.EMAIndicator(data["Close"], window=50).ema_indicator()
    data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()

    ema20 = data["EMA20"].iloc[-1]
    ema50 = data["EMA50"].iloc[-1]
    rsi = data["RSI"].iloc[-1]

    trend = "Yükseliş" if ema20 > ema50 else "Düşüş"
    risk = "Yüksek (Aşırı Alım)" if rsi > 70 else "Yüksek (Aşırı Satım)" if rsi < 30 else "Orta"

    al_esik = fiyat * 0.95
    risk_bolgesi = fiyat * 0.90
    panik_bolgesi = fiyat * 0.85
    hedef1 = fiyat * 1.05
    hedef2 = fiyat * 1.10
    hedef3 = fiyat * 1.20

    if fiyat < panik_bolgesi:
        durum, sinyal = "Panik Bölgesi – Satış baskısı yüksek", "SAT"
    elif fiyat < risk_bolgesi:
        durum, sinyal = "Risk Bölgesi – Stop aktif", "BEKLE"
    elif fiyat < al_esik:
        durum, sinyal = "Alım Eşiği – Yükseliş potansiyeli", "AL"
    elif fiyat < hedef1:
        durum, sinyal = "Yükseliş başladı – 1. hedefe yakın", "KORU"
    elif fiyat < hedef2:
        durum, sinyal = "Orta hedef bölgesi", "KÂR AL (Yarım)"
    else:
        durum, sinyal = "Uzak hedef bölgesi", "KÂR AL (Tam)"

    stop_loss = round(fiyat * 0.97, 2)
    kar_al = round(fiyat * 1.05, 2)

    return f"""
📊 {hisse} Stratos Analiz
Fiyat: {fiyat:.2f} ₺
Trend: {trend}
Risk: {risk}
RSI: {rsi:.2f}
Durum: {durum}
Sinyal: {sinyal}
🛑 Stop-Loss: {stop_loss} ₺
🎯 Kar Al: {kar_al} ₺
🟢 Alım Eşiği: {al_esik:.2f} ₺
🟡 Risk Bölgesi: {risk_bolgesi:.2f} ₺
🔴 Panik Bölgesi: {panik_bolgesi:.2f} ₺
🎯 1. Hedef: {hedef1:.2f} ₺
🎯 2. Hedef: {hedef2:.2f} ₺
🎯 3. Hedef: {hedef3:.2f} ₺
"""

def load_stocks(file_path="stocks.txt"):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def main():
    hisseler = load_stocks()
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    bot = Bot(token=token)

    for hisse in hisseler:
        rapor = bist_stratos_analiz(hisse)
        bot.send_message(chat_id=chat_id, text=rapor)

if __name__ == "__main__":
    main()
