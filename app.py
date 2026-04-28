
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Detector Darvas", layout="wide")

st.title("📈 Detector de Cajas Darvas")

activo = st.text_input("Escribe el activo", "AAPL")
dias_caja = st.slider("Días para la caja", 10, 60, 20)
factor_volumen = st.slider("Volumen mínimo x media", 1.0, 3.0, 1.5)

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

    if len(senales) > 0:
        ultima = senales.iloc[-1]

        entrada = ultima["Close"]
        stop = ultima["suelo"]
        riesgo = entrada - stop
        objetivo = entrada + riesgo * 2

        st.success("✅ Hay ruptura Darvas detectada")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Entrada", round(entrada, 2))
        col2.metric("Stop Loss", round(stop, 2))
        col3.metric("Riesgo", round(riesgo, 2))
        col4.metric("Objetivo 2R", round(objetivo, 2))

        st.dataframe(senales.tail(10))

    else:
        st.warning("❌ No hay ruptura Darvas fuerte ahora mismo")

    fig, ax = plt.subplots(figsize=(14,6))

    ax.plot(datos.index, datos["Close"], label="Precio cierre")
    ax.plot(datos.index, datos["techo"], label="Techo Darvas")
    ax.plot(datos.index, datos["suelo"], label="Suelo Darvas")

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
if st.button("Escanear tecnológicas jóvenes"):
    resultados = []

    for activo in activos_jovenes_tech:
        try:
            ticker = yf.Ticker(activo)
            info = ticker.info

            sector = info.get("sector", "")
            nombre = info.get("shortName", activo)

            if sector != "Technology":
                continue

            income = ticker.quarterly_income_stmt

            if income.empty:
                continue

            net_income = income.loc["Net Income"].iloc[0]

            if net_income <= 0:
                continue

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

            if datos["rompe_darvas"].iloc[-1]:
                resultados.append({
                    "Activo": activo,
                    "Nombre": nombre,
                    "Precio": round(datos["Close"].iloc[-1], 2),
                    "Techo": round(datos["techo"].iloc[-1], 2),
                    "Suelo": round(datos["suelo"].iloc[-1], 2),
                    "Beneficio último trimestre": round(net_income, 0)
                })

        except Exception as e:
            pass

    if resultados:
        st.success("Empresas encontradas")
        st.dataframe(pd.DataFrame(resultados))
    else:
        st.warning("Hoy no hay empresas que cumplan todos los filtros")
