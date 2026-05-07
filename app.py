import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

NTFY_TOPIC = "darvas-adan-8519"
ARCHIVO_ALERTAS = "alertas_enviadas.json"

WATCHLIST = [
    "NVDA", "PLTR", "AMD", "TSLA", "META", "MSFT", "AAPL",
    "GOOGL", "AMZN", "COIN", "MSTR", "SMCI", "SOUN", "ARM",
    "CRWD", "NET", "SNOW", "DDOG", "APP", "DUOL", "SHOP",
    "BTC-USD", "ETH-USD", "XRP-USD"
]

def numero_seguro(valor):
    try:
        if hasattr(valor, "iloc"):
            if len(valor) > 0:
                return float(valor.iloc[0])
        return float(valor)
    except Exception:
        return 0.0

def enviar_alerta(mensaje):
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    r = requests.post(
        url,
        data=mensaje.encode("utf-8"),
        headers={
            "Title": "🚀 Darvas Growth Scanner",
            "Priority": "high"
        },
        timeout=10
    )
    return r.status_code

def cargar_alertas():
    if not os.path.exists(ARCHIVO_ALERTAS):
        return {}
    try:
        with open(ARCHIVO_ALERTAS, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def guardar_alertas(alertas):
    with open(ARCHIVO_ALERTAS, "w") as f:
        json.dump(alertas, f)

def detectar_darvas(df, dias_caja):
    maximo_caja = numero_seguro(df["High"].rolling(dias_caja).max().iloc[-2])
    cierre_actual = numero_seguro(df["Close"].iloc[-1])
    return cierre_actual > maximo_caja, maximo_caja, cierre_actual

def volumen_fuerte(df, multiplicador):
    volumen_actual = numero_seguro(df["Volume"].iloc[-1])
    volumen_medio = numero_seguro(df["Volume"].rolling(20).mean().iloc[-1])
    if volumen_medio <= 0:
        return False, 0
    volumen_relativo = volumen_actual / volumen_medio
    return volumen_relativo >= multiplicador, round(volumen_relativo, 2)

def calcular_atr(df, periodo=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    rango1 = high - low
    rango2 = (high - close.shift()).abs()
    rango3 = (low - close.shift()).abs()

    true_range = pd.concat([rango1, rango2, rango3], axis=1).max(axis=1)
    atr = true_range.rolling(periodo).mean().iloc[-1]

    return numero_seguro(atr)

def calcular_score(df, volumen_ok, riesgo_pct, distancia_maximos):
    score = 0

    close = df["Close"]
    precio = numero_seguro(close.iloc[-1])
    sma20 = numero_seguro(close.rolling(20).mean().iloc[-1])
    sma50 = numero_seguro(close.rolling(50).mean().iloc[-1])
    sma200 = numero_seguro(close.rolling(200).mean().iloc[-1])

    if precio > sma20:
        score += 1

    if precio > sma50:
        score += 2

    if precio > sma200:
        score += 2

    if sma20 > sma50:
        score += 1

    if sma50 > sma200:
        score += 2

    if distancia_maximos <= 15:
        score += 1

    if distancia_maximos <= 8:
        score += 1

    if volumen_ok:
        score += 2

    if riesgo_pct <= 8:
        score += 1

    if riesgo_pct <= 5:
        score += 1

    return min(score, 10)

def escanear_mercado(tickers, dias_caja, score_minimo, multiplicador_volumen, riesgo_maximo):
    alertas_enviadas = cargar_alertas()
    resultados = []

    for ticker in tickers:
        try:
            df = yf.download(
                ticker,
                period="1y",
                interval="1d",
                auto_adjust=False,
                progress=False
            )

            if df.empty or len(df) < 220:
                resultados.append({
                    "Ticker": ticker,
                    "Precio": "-",
                    "Score": 0,
                    "Ruptura": False,
                    "Volumen x": "-",
                    "Riesgo %": "-",
                    "Máximos %": "-",
                    "Estado": "Sin datos suficientes"
                })
                continue

            ruptura, entrada_darvas, precio_actual = detectar_darvas(df, dias_caja)

            volumen_ok, volumen_relativo = volumen_fuerte(df, multiplicador_volumen)

            precio_actual = round(precio_actual, 2)

            stop_loss = round(
                numero_seguro(df["Low"].rolling(dias_caja).min().iloc[-1]),
                2
            )

            riesgo = round(precio_actual - stop_loss, 2)

            if precio_actual > 0:
                riesgo_pct = round((riesgo / precio_actual) * 100, 2)
            else:
                riesgo_pct = 999

            max_52 = numero_seguro(df["High"].rolling(252).max().iloc[-1])

            if max_52 > 0:
                distancia_maximos = round(((max_52 - precio_actual) / max_52) * 100, 2)
            else:
                distancia_maximos = 999

            atr = round(calcular_atr(df), 2)

            score = calcular_score(
                df,
                volumen_ok,
                riesgo_pct,
                distancia_maximos
            )

            calidad = (
                ruptura and
                volumen_ok and
                score >= score_minimo and
                riesgo_pct <= riesgo_maximo and
                distancia_maximos <= 20
            )

            resultados.append({
                "Ticker": ticker,
                "Precio": precio_actual,
                "Score": score,
                "Ruptura": ruptura,
                "Volumen x": volumen_relativo,
                "Stop Loss": stop_loss,
                "Riesgo": riesgo,
                "Riesgo %": riesgo_pct,
                "ATR": atr,
                "Máximos %": distancia_maximos,
                "Señal buena": calidad,
                "Estado": "OK"
            })

            clave_alerta = f"{ticker}_{datetime.now().date()}"

            if calidad and clave_alerta not in alertas_enviadas:
                mensaje = f"""
🚀 DARVAS GROWTH BREAKOUT

Ticker: {ticker}

Precio: {precio_actual}
Score: {score}/10

Stop Loss: {stop_loss}
Riesgo: {riesgo}
Riesgo %: {riesgo_pct}%

Volumen x media: {volumen_relativo}
Distancia máximos 52s: {distancia_maximos}%
ATR: {atr}
"""
                codigo = enviar_alerta(mensaje)

                if codigo == 200:
                    alertas_enviadas[clave_alerta] = True

        except Exception as e:
            resultados.append({
                "Ticker": ticker,
                "Precio": "-",
                "Score": 0,
                "Ruptura": False,
                "Volumen x": "-",
                "Riesgo %": "-",
                "Máximos %": "-",
                "Estado": f"Error: {e}"
            })

    guardar_alertas(alertas_enviadas)
    return resultados

st.set_page_config(
    page_title="Darvas Growth Scanner",
    page_icon="🚀"
)

st.title("🚀 Darvas Growth Scanner")

st.write("Scanner automático con Darvas, tendencia, volumen, riesgo, ATR, máximos y alertas al móvil.")

modo_auto = st.toggle("Autoescaneo activado", value=True)

minutos = st.slider("Escanear cada X minutos", 1, 60, 5)

dias_caja = st.slider("Días caja Darvas", 5, 50, 20)

score_minimo = st.slider("Score mínimo para alerta", 1, 10, 7)

multiplicador_volumen = st.slider(
    "Volumen mínimo x media",
    1.0,
    5.0,
    1.5,
    0.1
)

riesgo_maximo = st.slider(
    "Riesgo máximo %",
    2,
    30,
    10
)

tickers_texto = st.text_area(
    "Tickers a escanear",
    ", ".join(WATCHLIST)
)

tickers = [
    t.strip().upper()
    for t in tickers_texto.split(",")
    if t.strip()
]

if modo_auto:
    st_autorefresh(
        interval=minutos * 60 * 1000,
        key="auto_scanner"
    )

ejecutar = modo_auto

if st.button("🔍 Escanear ahora"):
    ejecutar = True

if ejecutar:
    st.info(f"Último escaneo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    with st.spinner("Escaneando mercado..."):
        resultados = escanear_mercado(
            tickers,
            dias_caja,
            score_minimo,
            multiplicador_volumen,
            riesgo_maximo
        )

    if resultados:
        df_resultados = pd.DataFrame(resultados)

        df_resultados = df_resultados.sort_values(
            by=["Señal buena", "Score"],
            ascending=False
        )

        st.subheader("Resultados")
        st.dataframe(df_resultados, use_container_width=True)

        buenas = df_resultados[df_resultados["Señal buena"] == True]

        st.success(f"✅ Escaneo completado. Señales buenas: {len(buenas)}")
