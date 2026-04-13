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
h_p = np.array([107.2, 104.5, 101.8, 100.0]) 
h_i = np.array([55.0, 70.0, 85.0, 100.0])

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
    
    # RIGA CORRETTA QUI SOTTO:
    hi = np.random.normal(di, vol_off * 1.3, it)
    
    ev = np.random.random(it)
    shock_off[ev < (cp/100)] -= 0.18
    shock_inf[ev < (cp/100)] -= 0.05
    shock_off[ev > (1 - pp/100)] += 0.14
    shock_inf[ev > (1 - pp/100)] += 0.08
    
    sp_off[t] = sp_off[t-1] * (1 + shock_off)
    sp_inf[t] = sp_inf[t-1] * (1 + shock_inf)
    si[t] = si[t-1] * (1 + hi)

sp_tot = np.zeros((anni + 1, it))
for t in range(anni + 1):
    sp_tot[t] = (1 - pesi_sommerso[t]) * sp_off[t] + pesi_sommerso[t] * sp_inf[t]

# --- 5. GRAFICI ---
x_p = np.arange(2026, 2026 + anni + 1)
c1, c2 = st.columns(2)

f1, a1 = plt.subplots(figsize=(8, 4))
p_tot = np.percentile(sp_tot, [5, 50, 95], axis=1)
p_off = np.percentile(sp_off, 50, axis=1)
p_inf = np.percentile(sp_inf, 50, axis=1)

a1.plot(h_y, h_p, 'ko-', lw=2, label="Storico 23-26")
a1.plot(x_p, sp_tot[:, :100], color='gray', alpha=0.03) 
a1.fill_between(x_p, p_tot[0], p_tot[2], color='#0D47A1', alpha=0.2, label="Rischio Totale 90%")
a1.plot(x_p, p_off, color='#d62728', lw=2, linestyle=':', label="Stato (Ufficiale)")
a1.plot(x_p, p_inf, color='#ff7f0e', lw=2, linestyle='-.', label="Mercato Nero")
a1.plot(x_p, p_tot[1], color='#1565C0', lw=3, label="PIL Reale Effettivo")
a1.set_title("PIL: Dinamica Dual Economy (Base 100)", fontweight='bold')
a1.legend(loc='lower left')
c1.pyplot(f1)

f2, a2 = plt.subplots(figsize=(8, 4))
p_si = np.percentile(si, [5, 50, 95], axis=1)
a2.plot(h_y, h_i, 'ko-', lw=2, label="Storico 23-26")
a2.plot(x_p, si[:, :200], color='gray', alpha=0.03)
a2.fill_between(x_p, p_si[0], p_si[2], color='#B71C1C', alpha=0.2, label="Rischio 90%")
a2.plot(x_p, p_si[1], color='#C62828', lw=3, label="Proiezione 3y")
a2.set_title("Inflazione e Svalutazione (Base 100 = Oggi)", fontweight='bold')
a2.legend(loc='upper left')
c2.pyplot(f2)

# --- 6. METRICHE ---
st.divider()
st.subheader("📊 Analisi Accademica (Scenari 2029)")

m_f, s_f = np.mean(sp_tot[-1]), np.std(sp_tot[-1])
sk = np.mean(((sp_tot[-1] - m_f)/s_f)**3)
ku = np.mean(((sp_tot[-1] - m_f)/s_f)**4) - 3

m1, m2, m3, m4 = st.columns(4)
m1.metric("Var. PIL Effettivo", f"{p_tot[1][-1]-100:.1f}%", f"Solo Stato: {p_off[-1]-100:.1f}%", delta_color="normal")
m2.metric("Var. Prezzi", f"{p_si[1][-1]-100:.1f}%")
m3.metric("Skewness (Asimmetria)", f"{sk:.2f}")
m4.metric("Kurtosis (Rischio Code)", f"{ku:.2f}")
