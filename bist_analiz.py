import os
import subprocess
import sys

# 🚀 KESİN ÇÖZÜM: 'ta' kütüphanesi eksikse, hangi .yml çalışırsa çalışsın kod çökmek yerine kendisi yükler
try:
    import ta
    HAS_TA = True
except ImportError:
    try:
        import pandas_ta as ta
        HAS_TA = False
    except ImportError:
        print("▶ 'ta' kütüphanesi bulunamadı, sistem otomatik yüklüyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ta", "pandas-ta", "yfinance", "pandas", "python-telegram-bot"])
        import ta
        HAS_TA = True

import yfinance as yf
import pandas as pd
from telegram import Bot
import asyncio

def calculate_indicators(data):
    close_series = data["Close"]
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.iloc[:, 0]
        
    if HAS_TA:
        ema20 = ta.trend.EMAIndicator(close_series, window=20).ema_indicator()
        ema50 = ta.trend.EMAIndicator(close_series, window=50).ema_indicator()
        rsi = ta.momentum.RSIIndicator(close_series, window=14).rsi()
    else:
        ema20 = close_series.ta.ema(length=20)
        ema50 = close_series.ta.ema(length=50)
        rsi = close_series.ta.rsi(length=14)
        
    return ema20, ema50, rsi

def bist_stratos_analiz(hisse):
    symbol = f"{hisse}.IS" if not hisse.endswith(".IS") else hisse
    data = yf.download(symbol, period="6mo", interval="1d")
    
    if data.empty:
        return f"⚠️ {hisse} | Veri bulunamadı."

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    ema20_series, ema50_series, rsi_series = calculate_indicators(data)
    
    fiyat = float(data["Close"].to_numpy()[-1])
    ema20 = float(ema20_series.to_numpy()[-1])
    ema50 = float(ema50_series.to_numpy()[-1])
    rsi = float(rsi_series.to_numpy()[-1])

    trend = "Yükseliş" if ema20 > ema50 else "Düşüş"
    risk = "Yüksek (Aşırı Alım)" if rsi > 70 else "Yüksek (Aşırı Satım)" if rsi < 30 else "Orta"

    if rsi < 30 and trend == "Yükseliş":
        durum, sinyal = "Alım Eşiği – Güçlü Yükseliş Potansiyeli", "AL"
    elif rsi < 35:
        durum, sinyal = "Destek Seviyesi – Tepki Alımı Bekleniyor", "KADEMELİ AL"
    elif rsi > 70 and trend == "Düşüş":
        durum, sinyal = "Panik Bölgesi – Satış Baskısı Çok Yüksek", "SAT"
    elif rsi > 65:
        durum, sinyal = "Hedef Bölgesi – Direnç Yakın", "KÂR AL (Yarım)"
    elif trend == "Yükseliş":
        durum, sinyal = "Yükseliş Trendi Korunuyor", "KORU"
    else:
        durum, sinyal = "Nötr / Belirsiz Bölge", "BEKLE"

    stop_loss = round(fiyat * 0.95, 2)
    kar_al = round(fiyat * 1.15, 2)
    
    hedef1 = fiyat * 1.05
    hedef2 = fiyat * 1.10
    hedef3 = fiyat * 1.20

    return f"""
📊 {hisse} Stratos Analiz
Fiyat: {fiyat:.2f} ₺
Trend: {trend}
Risk: {risk}
RSI: {rsi:.2f}
Durum: {durum}
Sinyal: {sinyal}
🛑 Stop-Loss: {stop_loss:.2f} ₺
🎯 Kar Al: {kar_al:.2f} ₺
🎯 1. Hedef: {hedef1:.2f} ₺
🎯 2. Hedef: {hedef2:.2f} ₺
🎯 3. Hedef: {hedef3:.2f} ₺
"""

def load_stocks():
    # Dosya ismi ne olursa olsun esnek okuma yapısı
    possible_files = ["stocks.txt", "new_stocks.txt", "old_stocks.txt"]
    for file in possible_files:
        if os.path.exists(file):
            with open(file, "r") as f:
                lines = [line.strip() for line in f if line.strip()]
                if lines:
                    return lines
    return ["THYAO", "EREGL"]

async def main():
    hisseler = load_stocks()
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    bot = Bot(token=token)

    for hisse in hisseler:
        try:
            rapor = bist_stratos_analiz(hisse)
            await bot.send_message(chat_id=chat_id, text=rapor)
        except Exception as e:
            try:
                await bot.send_message(chat_id=chat_id, text=f"⚠️ {hisse} için analiz hatası: {e}")
            except Exception as telegram_error:
                print(f"Telegram kritik hata: {telegram_error}")

if __name__ == "__main__":
    asyncio.run(main())
