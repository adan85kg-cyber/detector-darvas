import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# ---------- CONFIG ----------
NTFY_TOPIC = "darvas-adan-8519"

# ---------- FUNCION ALERTA ----------
def enviar_alerta(mensaje):

    url = f"https://ntfy.sh/{NTFY_TOPIC}"

    requests.post(
        url,
        data=mensaje.encode("utf-8"),
        headers={
            "Title": "Alerta Darvas",
            "Priority": "high"
        }
    )

# ---------- FUNCION DARVAS ----------
def detectar_darvas(df, dias_caja=20):

    maximo = df["High"].rolling(dias_caja).max().iloc[-2]

    cierre_actual = df["Close"].iloc[-1]

    ruptura = cierre_actual > maximo

    return ruptura, maximo

# ---------- INTERFAZ ----------
st.set_page_config(page_title="Detector Darvas")

st.title("🚀 Detector Darvas")

ticker = st.text_input("Ticker", "AAPL")

dias_caja = st.slider(
    "Dias para la caja",
    5,
    50,
    20
)

# ---------- BOTON ----------
if st.button("Analizar"):

    try:

        df = yf.download(
            ticker,
            period="6mo",
            interval="1d"
        )

        if df.empty:
            st.error("No hay datos")
            st.stop()

        ruptura, entrada = detectar_darvas(
            df,
            dias_caja
        )

        precio_actual = round(
            df["Close"].iloc[-1],
            2
        )

        stop_loss = round(
            df["Low"].rolling(dias_caja).min().iloc[-1],
            2
        )

        riesgo = round(
            precio_actual - stop_loss,
            2
        )

        st.subheader(f"Resultado para {ticker}")

        if ruptura:

            st.success("✅ Hay ruptura Darvas")

            mensaje = f"""
🚀 RUPTURA DARVAS

Ticker: {ticker}

Entrada: {precio_actual}

Stop Loss: {stop_loss}

Riesgo: {riesgo}
"""

            enviar_alerta(mensaje)

            st.success("📲 Alerta enviada al móvil")

        else:

            st.warning("❌ No hay ruptura")

        st.write(f"### Entrada\n{precio_actual}")
        st.write(f"### Stop Loss\n{stop_loss}")
        st.write(f"### Riesgo\n{riesgo}")

    except Exception as e:

        st.error(str(e))
