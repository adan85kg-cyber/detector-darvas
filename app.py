import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import json
import os
from datetime import datetime

# ---------- CONFIG ----------
NTFY_TOPIC = "darvas-adan-8519"
ARCHIVO_ALERTAS = "alertas_enviadas.json"

WATCHLIST = [
