import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cuba Risk 3Y & Dual Economy", layout="wide")

# CSS per nascondere il menu Streamlit e pulire l'interfaccia
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

st.title("Stress Test & Dual Economy: Proiezione a 3 Anni")
st.markdown("Modello stocastico avanzato con correlazione di Cholesky e transizione logistica del mercato informale.")

# --- 2. DATI STORICI ---
h_y = np.array([2023, 2024, 2025, 2026])
h_p = np.array([107.2, 104.5, 101.8, 100.0]) # Trend PIL storico
h_i = np.array([55.0, 70.0, 85.0, 100.0])    # Trend Prezzi storico

# --- 3. PANNELLO DI CONTROLLO (SIDEBAR) ---
st.sidebar.header("📡 Dati Live (Mercato Nero)")
cup = st.sidebar.number_input("CUP/USD (es. El Toque)", 100, 1000, 340, 10)

st.sidebar.divider()
st.sidebar.header("⚖️ Leve Dual Economy")
w_init = st.sidebar.slider("Peso Sommerso Oggi (%)", 10, 80, 40) / 100
w_fin = st.sidebar.slider("Peso Sommerso 2029 (%)", 10, 90, 55) / 100

st.sidebar.divider()
st.sidebar.header("📊 Shock Macro")
es = st.sidebar.slider("Shock Energia (%)", -50, 50, 0)
rs = st.sidebar.slider("Shock Rimesse (%)", -50, 50, 0)
sv = st.sidebar.slider("Sentiment / Incertezza", -1.0, 1.0, 0.0)

st.sidebar.divider()
st.sidebar.header("🦢 Eventi Estremi")
cp = st.sidebar.slider("Cigno Nero (%)", 0, 10, 2)
pp = st.sidebar.slider("Cigno Bianco (%)", 0, 10, 1)

# --- 4. MOTORE STOCASTICO ---
it, anni = 100000, 3
np.random.seed(42)

inf_imp = max(0, (cup - 250) / 50 * 0.02)
rho = 0.60 

dp_off = -0.06 + (es/100 * 0.15) 
dp_inf = -0.01 + (rs/100 * 0.12) + (es/100 * 0.05) 
di = 0.15 + inf_imp - (es/100 * 0.20) + (rs/100 * 0.10)

vol_off = 0.08 * (1.4 - sv)
vol_inf = 0.12 * (1.4 - sv) 

sp_off, sp_inf, si = np.zeros((anni + 1, it)), np.zeros((anni + 1, it)), np.zeros((anni + 1, it))
sp_off[0], sp_inf[0], si[0] = 100, 100, 100

k = 3.0           
t0 = anni / 2.0   
tempi = np.linspace(0, anni, anni + 1)
pesi_sommerso = w_init + (w_fin - w_init) / (1 + np.exp(-k * (tempi - t0)))

for t in range(1, anni + 1):
    Z1 = np.random.normal(0, 1, it)
    Z2 = np.random.normal(0, 1, it)
    
    shock_off = dp_off + vol_off * Z1
    shock_inf = dp_inf + vol_inf * (rho * Z1 + np.sqrt(1 - rho**2) * Z2)
    
    hi = np.random.normal(di, vol_