import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cuba Risk 3Y & Dual Economy", layout="wide")
st.title("Stress Test & Dual Economy: Proiezione a 3 Anni")
st.markdown(
    "Modello stocastico avanzato con correlazione di Cholesky "
    "e transizione logistica del mercato informale."
)

# --- 2. DATI STORICI (Gancio con la realtà 2023-2026) ---
# Base 100 = 2026

# PIL reale (indice) calibrato su stime CEEC/ONEI: 
# 2023 ≈ -1.9%, 2024 ≈ -2.0%, 2025 ≈ -5.0%, 2026 ≈ +0.9% [CEEC 2026]
h_y = np.array([2023, 2024, 2025, 2026])
h_p = np.array([106.4, 104.3, 99.1, 100.0])

# Inflazione (indice prezzi, base 100 = 2026).
# Scenario coerente con inflazione ufficiale elevata e serie di rialzi:
# 2023–2025 cumulati e 2026=100 come ancora.
h_i = np.array([55.0, 70.0, 85.0, 100.0])

# --- 3. PANNELLO DI CONTROLLO (LEVE LATERALI) ---
st.sidebar.header("📡 Dati Live (Mercato Nero)")

# Tasso elTOQUE indicativo: 1 USD ≈ 525 CUP il 13/04/2026 [elTOQUE]
cup = st.sidebar.number_input("CUP/USD (es. elTOQUE)", 100, 1000, 525, 5)

st.sidebar.divider()
st.sidebar.header("⚖️ Leve Dual Economy")
st.sidebar.markdown("*Dinamica Sigmoide (Non-Lineare)*")

# Peso sommerso oggi: ~50% considerando MIPYME + mercato informale
w_init = st.sidebar.slider("Peso Sommerso Oggi (%)", 10, 80, 50) / 100
# Tra 3 anni (orizzonte 2029 relativo a base 2026+3): tendenza a salire
w_fin = st.sidebar.slider("Peso Sommerso 2029 (%)", 10, 90, 62) / 100

st.sidebar.divider()
st.sidebar.header("📊 Shock Macro")

# SHOCK ENERGETICO – deficit medio ≈ 1500–1800 MW su domanda ≈ 3000 MW → ~50–60%
# Default di partenza oggi: -50% (shock negativo forte)
es = st.sidebar.slider("Shock Energia (%)", -80, 50, -50)

# SHOCK RIMESSE – remittances 2024/25 ≈ 1,0–1,2 mld vs picco 3,4 mld → -60% dal picco
# Default di partenza oggi: -40% rispetto a "normalità" pre-crisi
rs = st.sidebar.slider("Shock Rimesse (%)", -80, 50, -40)

# Sentiment: -1 pessimo (alta incertezza), +1 ottimo (bassa incertezza)
sv = st.sidebar.slider("Sentiment / Incertezza", -1.0, 1.0, -0.7)

st.sidebar.divider()
st.sidebar.header("🦢 Eventi Estremi")
# Prob. annua di cigno nero positivo/negativo (in %)
cp = st.sidebar.slider("Cigno Nero (%)", 0, 20, 5)
pp = st.sidebar.slider("Cigno Bianco (%)", 0, 20, 1)

# --- 4. MOTORE STOCASTICO AVANZATO (3 ANNI) ---
it, anni = 100000, 3
np.random.seed(42)  # Per riproducibilità accademica

# Calcolo Inflazione "Importata" dal cambio informale
# Soglia 250 CUP/USD come baseline pre-crisi; sopra questa soglia
# l'inflazione importata cresce del 2% ogni +50 CUP
inf_imp = max(0, (cup - 250) / 50 * 0.02)

# Correlazione tra Stato e Mercato Nero (Decomposizione di Cholesky)
rho = 0.60

# Drift (tendenze di base calcolate con shock condivisi)
# PIL ufficiale: tendenza -7% annuo, modulata da shock energetico
dp_off = -0.07 + (es / 100 * 0.15)

# Mercato nero: più resiliente, ma risente di energia e rimesse
dp_inf = -0.01 + (rs / 100 * 0.10) + (es / 100 * 0.05)

# Inflazione: base 15% + inflazione importata + aggiustamenti per shock
di = 0.15 + inf_imp - (es / 100 * 0.20) + (rs / 100 * 0.10)

# Volatilità: aumenta con pessimo sentiment (sv negativo)
base_scale = (1.4 - sv)
vol_off = 0.08 * base_scale    # settore ufficiale
vol_inf = 0.12 * base_scale    # mercato nero più volatile

sp_off = np.zeros((anni + 1, it))
sp_inf = np.zeros((anni + 1, it))
si = np.zeros((anni + 1, it))
sp_off[0], sp_inf[0], si[0] = 100, 100, 100

# Transizione Non-Lineare del Mercato Nero (Curva Sigmoide)
k = 3.0          # Ripidità del tipping-point
t0 = anni / 2.0  # Punto di flesso (exploit a metà periodo)
tempi = np.linspace(0, anni, anni + 1)
pesi_sommerso = w_init + (w_fin - w_init) / (1 + np.exp(-k * (tempi - t0)))

# Simulazione Monte Carlo
for t in range(1, anni + 1):
    # Generazione Variabili Normali Indipendenti
    Z1 = np.random.normal(0, 1, it)
    Z2 = np.random.normal(0, 1, it)

    # Applicazione Decomposizione di Cholesky
    shock_off = dp_off + vol_off * Z1
    shock_inf = dp_inf + vol_inf * (rho * Z1 + np.sqrt(1 - rho**2) * Z2)

    # Inflazione con volatilità più alta
    hi = np.random.normal(di, vol_off * 1.3, it)

    # Processo di Salto (Jump Diffusion)
    ev = np.random.random(it)
    # Cigni neri
    shock_off[ev < (cp / 100)] -= 0.18
    shock_inf[ev < (cp / 100)] -= 0.05
    # Cigni bianchi
    shock_off[ev > (1 - pp / 100)] += 0.14
    shock_inf[ev > (1 - pp / 100)] += 0.08

    # Aggiornamento percorsi
    sp_off[t] = sp_off[t - 1] * (1 + shock_off)
    sp_inf[t] = sp_inf[t - 1] * (1 + shock_inf)
    si[t] = si[t - 1] * (1 + hi)

# Calcolo PIL Totale Effettivo (Media Ponderata Dinamica)
sp_tot = np.zeros((anni + 1, it))
for t in range(anni + 1):
    sp_tot[t] = (1 - pesi_sommerso[t]) * sp_off[t] + pesi_sommerso[t] * sp_inf[t]

# --- 5. GRAFICI INTEGRATI ---
x_p = np.arange(2026, 2026 + anni + 1)
c1, c2 = st.columns(2)

# Grafico 1: PIL Dual Economy
f1, a1 = plt.subplots(figsize=(8, 4))
p_tot = np.percentile(sp_tot, [5, 50, 95], axis=1)
p_off = np.percentile(sp_off, 50, axis=1)
p_inf = np.percentile(sp_inf, 50, axis=1)

a1.plot(h_y, h_p, 'ko-', lw=2, label="Storico 23-26")
a1.plot(x_p, sp_tot[:, :100], color='gray', alpha=0.03)  # Sfondo stocastico
a1.fill_between(x_p, p_tot[0], p_tot[2],
                color='#0D47A1', alpha=0.2, label="Rischio Totale 90%")

# Le tre linee cruciali
a1.plot(x_p, p_off, color='#d62728', lw=2, linestyle=':',
        label="Stato (Ufficiale)")
a1.plot(x_p, p_inf, color='#ff7f0e', lw=2, linestyle='-.',
        label="Mercato Nero")
a1.plot(x_p, p_tot[1], color='#1565C0', lw=3,
        label="PIL Reale Effettivo")

a1.set_title("PIL: Dinamica Dual Economy (Base 100)", fontweight='bold')
a1.legend(loc='lower left')
c1.pyplot(f1)

# Grafico 2: Inflazione
f2, a2 = plt.subplots(figsize=(8, 4))
p_si = np.percentile(si, [5, 50, 95], axis=1)
a2.plot(h_y, h_i, 'ko-', lw=2, label="Storico 23-26")
a2.plot(x_p, si[:, :200], color='gray', alpha=0.03)
a2.fill_between(x_p, p_si[0], p_si[2],
                color='#B71C1C', alpha=0.2, label="Rischio 90%")
a2.plot(x_p, p_si[1], color='#C62828', lw=3, label="Proiezione 3y")
a2.set_title("Inflazione e Svalutazione (Base 100 = Oggi)", fontweight='bold')
a2.legend(loc='upper left')
c2.pyplot(f2)

# --- 6. METRICHE NUMERICHE E STATISTICHE ---
st.divider()
st.subheader("📊 Analisi Accademica (Scenari 2029)")

m_f, s_f = np.mean(sp_tot[-1]), np.std(sp_tot[-1])
sk = np.mean(((sp_tot[-1] - m_f) / s_f) ** 3)
ku = np.mean(((sp_tot[-1] - m_f) / s_f) ** 4) - 3

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Var. PIL Effettivo",
    f"{p_tot[1][-1] - 100:.1f}%",
    f"Solo Stato: {p_off[-1] - 100:.1f}%",
    delta_color="normal"
)
m2.metric("Var. Prezzi", f"{p_si[1][-1] - 100:.1f}%")
m3.metric(
    "Skewness (Asimmetria)",
    f"{sk:.2f}",
    help="Se negativo, gli shock avversi pesano più delle riprese."
)
m4.metric(
    "Kurtosis (Rischio Code)",
    f"{ku:.2f}",
    help="Se alto, alta probabilità di eventi estremi (Black Swans)."
)
