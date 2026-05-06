import streamlit as st
import yfinance as yf
import requests

# ---------- CONFIG ----------
NTFY_TOPIC = "darvas-adan-8519"

# ---------- ALERTA NTFY ----------
def enviar_alerta(mensaje):
    url = f"https://ntfy.sh/{NTFY_TOPIC}"

    respuesta = requests.post(
        url,
        data=mensaje.encode("utf-8"),
        headers={
            "Title": "Alerta Darvas",
            "Priority": "high"
        },
        timeout=10
    )

    return respuesta.status_code


# ---------- DARVAS ----------
def detectar_darvas(df, dias_caja=20):
    maximo = float(df["High"].rolling(dias_caja).max().iloc[-2])
    cierre_actual = float(df["Close"].iloc[-1])

    ruptura = cierre_actual > maximo

    return ruptura, maximo, cierre_actual


# ---------- APP ----------
st.set_page_config(page_title="Detector Darvas", page_icon="🚀")

st.title("🚀 Detector Darvas")

ticker = st.text_input("Ticker", "AAPL").upper()

dias_caja = st.slider(
    "Dias para la caja",
    min_value=5,
    max_value=50,
    value=20
)

if st.button("Analizar"):

    try:
        df = yf.download(
            ticker,
            period="6mo",
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if df.empty:
            st.error("No hay datos para ese ticker")
            st.stop()

        ruptura, entrada_darvas, precio_actual = detectar_darvas(
            df,
            dias_caja
        )

        precio_actual = round(float(precio_actual), 2)

        stop_loss = round(
            float(df["Low"].rolling(dias_caja).min().iloc[-1]),
            2
        )

        riesgo = round(precio_actual - stop_loss, 2)

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

            estado = enviar_alerta(mensaje)

            if estado == 200:
                st.success("📲 Alerta enviada al móvil")
            else:
                st.error(f"Falló ntfy. Código: {estado}")

        else:
            st.warning("❌ No hay ruptura Darvas")

        st.write(f"### Entrada\n{precio_actual}")
        st.write(f"### Stop Loss\n{stop_loss}")
        st.write(f"### Riesgo\n{riesgo}")

    except Exception as e:
        st.error(f"Error: {e}")
