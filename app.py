import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests

# ===============================
# CONFIGURACION TELEGRAM
# ===============================

BOT_TOKEN = 8608735942:AAEq_8RXuUkSMmDvWSf6gb5RtAwZYUxZ_4k
CHAT_ID = 68807076


def enviar_alerta(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }

    respuesta = requests.post(url, data=payload)

    if respuesta.status_code == 200:
        return True, "Mensaje enviado"
    else:
        return False, respuesta.text


# ===============================
# INTERFAZ
# ===============================

st.set_page_config(page_title="Detector Darvas")

st.title("📈 Detector de Cajas Darvas")


# ===============================
# BOTON TEST TELEGRAM
# ===============================

if st.button("Probar alerta Telegram"):

    ok, respuesta = enviar_alerta("✅ Prueba de alerta Darvas funcionando")

    if ok:
        st.success("Mensaje enviado a Telegram")
    else:
        st.error(f"Error Telegram: {respuesta}")


# ===============================
# PARAMETROS
# ===============================

activo = st.text_input("Escribe el activo", "AAPL")

dias_caja = st.slider("Días para la caja", 10, 60, 20)

factor_volumen = st.slider("Volumen mínimo x media", 1.0, 3.0, 1.5)


# ===============================
# ANALISIS DARVAS
# ===============================

if st.button("Analizar"):

    datos = yf.download(activo, period="1y", interval="1d")

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


# ===============================
# SI HAY RUPTURA
# ===============================

    if len(senales) > 0:

        ultima = senales.iloc[-1]

        entrada = ultima["Close"]
        stop = ultima["suelo"]
        riesgo = entrada - stop
        objetivo = entrada + riesgo * 2

        mensaje = f"🚀 RUPTURA DARVAS\n\nActivo: {activo}\nEntrada: {round(entrada,2)}\nStop: {round(stop,2)}\nObjetivo: {round(objetivo,2)}"

        ok, respuesta = enviar_alerta(mensaje)

        if ok:
            st.success("✅ Hay ruptura Darvas detectada (alerta enviada)")
        else:
            st.error(f"Error Telegram: {respuesta}")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Entrada", round(entrada,2))
        col2.metric("Stop Loss", round(stop,2))
        col3.metric("Riesgo", round(riesgo,2))
        col4.metric("Objetivo 2R", round(objetivo,2))

        st.dataframe(senales.tail(10))


# ===============================
# SI NO HAY RUPTURA
# ===============================

    else:

        st.warning("❌ No hay ruptura Darvas fuerte")


# ===============================
# GRAFICO
# ===============================

    fig, ax = plt.subplots(figsize=(14,6))

    ax.plot(datos.index, datos["Close"], label="Precio")
    ax.plot(datos.index, datos["techo"], label="Techo Darvas")
    ax.plot(datos.index, datos["suelo"], label="Suelo Darvas")

    ax.legend()
    ax.grid()

    st.pyplot(fig)
