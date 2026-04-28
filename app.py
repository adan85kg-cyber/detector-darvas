import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests

# =========================
# TELEGRAM
# =========================
BOT_TOKEN = 8608735942:AAEq_8RXuUkSMmDvWSf6gb5RtAwZYUxZ_4k
CHAT_ID = 68807076  # sin comillas


def enviar_alerta(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }

    try:
        r = requests.post(url, data=payload, timeout=10)

        if r.status_code == 200:
            return True, "Mensaje enviado correctamente"
        else:
            return False, r.text

    except Exception as e:
        return False, str(e)


# =========================
# APP
# =========================
st.set_page_config(page_title="Detector Darvas", layout="wide")

st.title("📈 Detector de Cajas Darvas")

if st.button("Probar alerta Telegram"):
    ok, respuesta = enviar_alerta("✅ Prueba de alerta Darvas funcionando")

    if ok:
        st.success("Mensaje enviado a Telegram")
    else:
        st.error(f"Error Telegram: {respuesta}")

activo = st.text_input("Escribe el activo", "AAPL")

dias_caja = st.slider("Días para la caja", 10, 60, 20)

factor_volumen = st.slider("Volumen mínimo x media", 1.0, 3.0, 1.5)

if st.button("Analizar"):

    with st.spinner("Descargando datos..."):

        datos = yf.download(
            activo,
            period="1y",
            interval="1d",
            progress=False
        )

    if datos.empty:
        st.error("No se han encontrado datos para ese activo.")

    else:

        if isinstance(datos.columns, pd.MultiIndex):
            datos.columns = datos.columns.get_level_values(0)

        datos["techo"] = datos["High"].rolling(dias_caja).max()
        datos["suelo"] = datos["Low"].rolling(dias_caja).min()
        datos["volumen_medio"] = datos["Volume"].rolling(20).mean()

        datos = datos.dropna()

        datos["rompe_darvas"] = (
            (datos["Close"] > datos["techo"].shift(1)) &
            (datos["Volume"] > datos["volumen_medio"] * factor_volumen)
        )

        senales = datos[datos["rompe_darvas"]]

        st.subheader(f"Resultado para {activo}")

        if len(senales) > 0:

            ultima = senales.iloc[-1]

            entrada = float(ultima["Close"])
            stop = float(ultima["suelo"])
            riesgo = entrada - stop
            objetivo = entrada + riesgo * 2

            mensaje = (
                f"🚀 RUPTURA DARVAS\n\n"
                f"Activo: {activo}\n"
                f"Entrada: {round(entrada, 2)}\n"
                f"Stop Loss: {round(stop, 2)}\n"
                f"Riesgo: {round(riesgo, 2)}\n"
                f"Objetivo 2R: {round(objetivo, 2)}"
            )

            ok, respuesta = enviar_alerta(mensaje)

            if ok:
                st.success("✅ Hay ruptura Darvas detectada y alerta enviada")
            else:
                st.warning("✅ Hay ruptura Darvas, pero falló Telegram")
                st.error(respuesta)

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Entrada", round(entrada, 2))
            col2.metric("Stop Loss", round(stop, 2))
            col3.metric("Riesgo", round(riesgo, 2))
            col4.metric("Objetivo 2R", round(objetivo, 2))

            st.dataframe(senales.tail(10))

        else:
            st.warning("❌ No hay ruptura Darvas fuerte")

        fig, ax = plt.subplots(figsize=(14, 6))

        ax.plot(datos.index, datos["Close"], label="Precio")
        ax.plot(datos.index, datos["techo"], label="Techo Darvas")
        ax.plot(datos.index, datos["suelo"], label="Suelo Darvas")

        if len(senales) > 0:
            ax.scatter(
                senales.index,
                senales["Close"],
                marker="^",
                s=120,
                label="Ruptura"
            )

        ax.legend()
        ax.grid()

        st.pyplot(fig)






