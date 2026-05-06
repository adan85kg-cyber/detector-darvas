import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import json
import os
from datetime import datetime

# ---------- CONFIG ----------
NTFY_TOPIC = "darvas-adan-8519"

WATCHLIST = [
    "NVDA",
    "PLTR",
    "AMD",
    "TSLA",
    "META",
    "MSFT",
    "AAPL",
    "GOOGL",
    "AMZN",
    "COIN",
    "MSTR",
    "SMCI",
    "SOUN",
    "ARM",
    "BTC-USD",
    "ETH-USD",
    "XRP-USD"
]

ARCHIVO_ALERTAS = "alertas_enviadas.json"

# ---------- ALERTAS ----------
def enviar_alerta(mensaje):

    url = f"https://ntfy.sh/{NTFY_TOPIC}"

    requests.post(
        url,
        data=mensaje.encode("utf-8"),
        headers={
            "Title": "🚀 Darvas AI Scanner",
            "Priority": "high"
        },
        timeout=10
    )

# ---------- ARCHIVO ALERTAS ----------
def cargar_alertas():

    if not os.path.exists(ARCHIVO_ALERTAS):
        return {}

    with open(ARCHIVO_ALERTAS, "r") as f:
        return json.load(f)

def guardar_alertas(alertas):

    with open(ARCHIVO_ALERTAS, "w") as f:
        json.dump(alertas, f)

# ---------- DARVAS ----------
def detectar_darvas(df, dias_caja=20):

    maximo = float(
        df["High"].rolling(dias_caja).max().iloc[-2]
    )

    cierre_actual = float(
        df["Close"].iloc[-1]
    )

    ruptura = cierre_actual > maximo

    return ruptura

# ---------- VOLUMEN ----------
def volumen_fuerte(df):

    volumen_actual = float(df["Volume"].iloc[-1])

    volumen_medio = float(
        df["Volume"].rolling(20).mean().iloc[-1]
    )

    return volumen_actual > volumen_medio * 1.5

# ---------- SCORE ----------
def calcular_score(df):

    score = 0

    close = df["Close"]

    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1]

    precio = close.iloc[-1]

    # Tendencia fuerte
    if precio > sma50:
        score += 2

    if precio > sma200:
        score += 2

    if sma50 > sma200:
        score += 2

    # Cerca de máximos
    max_52 = df["High"].rolling(252).max().iloc[-1]

    distancia = (max_52 - precio) / max_52

    if distancia < 0.15:
        score += 2

    # Volumen fuerte
    if volumen_fuerte(df):
        score += 2

    return score

# ---------- APP ----------
st.set_page_config(
    page_title="Darvas AI Scanner",
    page_icon="🚀"
)

st.title("🚀 Darvas AI Scanner")

dias_caja = st.slider(
    "Dias caja Darvas",
    5,
    50,
    20
)

score_minimo = st.slider(
    "Score minimo",
    1,
    10,
    6
)

resultados = []

if st.button("🔍 Escanear mercado"):

    alertas_enviadas = cargar_alertas()

    for ticker in WATCHLIST:

        try:

            df = yf.download(
                ticker,
                period="1y",
                interval="1d",
                progress=False
            )

            if df.empty:
                continue

            ruptura = detectar_darvas(
                df,
                dias_caja
            )

            score = calcular_score(df)

            volumen_ok = volumen_fuerte(df)

            precio_actual = round(
                float(df["Close"].iloc[-1]),
                2
            )

            stop_loss = round(
                float(
                    df["Low"]
                    .rolling(dias_caja)
                    .min()
                    .iloc[-1]
                ),
                2
            )

            riesgo = round(
                precio_actual - stop_loss,
                2
            )

            resultados.append({
                "Ticker": ticker,
                "Precio": precio_actual,
                "Score": score,
                "Ruptura": ruptura,
                "Volumen": volumen_ok,
                "Riesgo": riesgo
            })

            clave_alerta = f"{ticker}_{datetime.now().date()}"

            if (
                ruptura
                and volumen_ok
                and score >= score_minimo
            ):

                if clave_alerta not in alertas_enviadas:

                    mensaje = f"""
🚀 DARVAS BREAKOUT

Ticker: {ticker}

Precio: {precio_actual}

Score: {score}/10

Stop Loss: {stop_loss}

Riesgo: {riesgo}
"""

                    enviar_alerta(mensaje)

                    alertas_enviadas[clave_alerta] = True

        except Exception as e:

            st.error(f"{ticker}: {e}")

    guardar_alertas(alertas_enviadas)

    if resultados:

        df_resultados = pd.DataFrame(resultados)

        df_resultados = df_resultados.sort_values(
            by="Score",
            ascending=False
        )

        st.dataframe(df_resultados)

        st.success("✅ Escaneo completado")
