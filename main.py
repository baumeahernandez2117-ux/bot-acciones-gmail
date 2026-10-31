import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import yfinance as yf

# 1. CONFIGURACIÓN
TICKERS = ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD", "BAC", "INTC"]

# Leemos las credenciales desde las variables de entorno de GitHub
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def send_gmail_alert(subject: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[OK] Correo enviado: {subject}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar el correo: {e}")

def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_market():
    print("\n[INFO] Analizando las 10 acciones...")
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="5d", interval="5m", progress=False)
            if df.empty or len(df) < 15:
                continue

            close_prices = df['Close']
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.squeeze()

            df['RSI'] = calculate_rsi(close_prices)
            last_price = float(close_prices.iloc[-1])
            last_rsi = float(df['RSI'].iloc[-1])
            
            print(f"-> {ticker}: Precio = ${last_price:.2f} | RSI = {last_rsi:.2f}")

            if last_rsi <= 40:
                send_gmail_alert(
                    f"🟢 COMPRA: {ticker}",
                    f"La acción {ticker} está en zona de sobreventa (RSI: {last_rsi:.2f}). Precio: ${last_price:.2f}"
                )
            elif last_rsi >= 60:
                send_gmail_alert(
                    f"🔴 VENTA: {ticker}",
                    f"La acción {ticker} está en zona de sobrecompra (RSI: {last_rsi:.2f}). Precio: ${last_price:.2f}"
                )
        except Exception as e:
            print(f"[ERROR] Falló el análisis de {ticker}: {e}")

if __name__ == "__main__":
    analyze_market()
