import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skewnorm as sn

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cuba Risk 3Y & Dual Economy", layout="wide")
st.title("Stress Test & Dual Economy: Proiezione a 3 Anni")
st.markdown(
    "Modello stocastico con correlazione di Cholesky "
    "e transizione logistica del mercato informale."
)

# --- 2. DATI STORICI ---
h_y = np.array([2023, 2024, 2025, 2026])
h_p = np.array([106.4, 104.3, 99.1, 100.0])
h_i = np.array([55.0, 70.0, 85.0, 100.0])

# --- 3. PANNELLO DI CONTROLLO ---
st.sidebar.header("Dati Live (Mercato Nero)")
cup = st.sidebar.number_input("CUP/USD (es. elTOQUE)", 100, 1000, 525, 5)

st.sidebar.divider()
st.sidebar.header("Leve Dual Economy")
st.sidebar.markdown("*Dinamica Sigmoide (Non-Lineare)*")
w_init = st.sidebar.slider("Peso Sommerso Oggi (%)", 10, 80, 50) / 100
w_fin  = st.sidebar.slider("Peso Sommerso 2029 (%)", 10, 90, 62) / 100

st.sidebar.divider()
st.sidebar.header("Shock Macro")
es = st.sidebar.slider("Shock Energia (%)", -80, 50, -50)
rs = st.sidebar.slider("Shock Rimesse (%)", -80, 50, -40)
sv = st.sidebar.slider("Sentiment / Incertezza", -1.0, 1.0, -0.7)

st.sidebar.divider()
st.sidebar.header("Eventi Estremi")
cp = st.sidebar.slider("Cigno Nero (%)",   0, 20, 7)   # ← MODIFICA: default 5→7
pp = st.sidebar.slider("Cigno Bianco (%)", 0, 20, 1)

# --- 4. MOTORE STOCASTICO ---
it, anni = 100000, 3
np.random.seed(42)

# ← MODIFICA: soglia aggiornata 250→450, sensibilità 0.02→0.04,
#             termine monetario fisso +0.08 (stampa di pesos)
inf_imp = 0.08 + max(0, (cup - 450) / 50 * 0.04)

rho = 0.60

dp_off = -0.07 + (es / 100 * 0.15)
dp_inf = -0.01 + (rs / 100 * 0.10) + (es / 100 * 0.05)
di     =  0.15 + inf_imp - (es / 100 * 0.20) + (rs / 100 * 0.10)

base_scale = (1.4 - sv)
vol_off = 0.08 * base_scale
vol_inf = 0.12 * base_scale

sp_off = np.zeros((anni + 1, it))
sp_inf = np.zeros((anni + 1, it))
si     = np.zeros((anni + 1, it))
sp_off[0], sp_inf[0], si[0] = 100, 100, 100

k  = 3.0
t0 = anni / 2.0
tempi         = np.linspace(0, anni, anni + 1)
pesi_sommerso = w_init + (w_fin - w_init) / (1 + np.exp(-k * (tempi - t0)))

# ← MODIFICA: innovazioni skew-normali (Azzalini 1985)
#   alpha=-4 → coda sinistra più pesante (shock negativi strutturalmente più
#   frequenti e più intensi in un'economia da frontiera come Cuba)
ALPHA_SKEW = -4.0
delta_sk   = ALPHA_SKEW / np.sqrt(1 + ALPHA_SKEW**2)
mu_sk      = delta_sk * np.sqrt(2 / np.pi)
sig_sk     = np.sqrt(1 - mu_sk**2)

# ← MODIFICA: leverage asimmetrico (Black 1976)
LEVERAGE = 1.8

for t in range(1, anni + 1):
    # Innovazioni skew-normali standardizzate
    Z1 = (sn.rvs(a=ALPHA_SKEW, size=it) - mu_sk) / sig_sk
    Z2 = (sn.rvs(a=ALPHA_SKEW, size=it) - mu_sk) / sig_sk

    # Cholesky
    eps_off_raw = Z1
    eps_inf_raw = rho * Z1 + np.sqrt(1 - rho**2) * Z2

    # Leverage: shock negativi amplificati 1.8x
    eps_off = np.where(eps_off_raw < 0, eps_off_raw * LEVERAGE, eps_off_raw)
    eps_inf = np.where(eps_inf_raw < 0, eps_inf_raw * LEVERAGE, eps_inf_raw)

    # ← MODIFICA: GBM esatto con correzione di Itô (previene PIL<0)
    log_ret_off = (dp_off - 0.5 * vol_off**2) + vol_off * eps_off
    log_ret_inf = (dp_inf - 0.5 * vol_inf**2) + vol_inf * eps_inf

    hi = np.random.normal(di, vol_off * 1.3, it)

    # ← MODIFICA: jump moltiplicativi (np.log(1+j)) + cigno nero più forte
    ev = np.random.random(it)
    log_ret_off += np.where(ev < (cp / 100), np.log(1 - 0.30), 0.0)  # -30%
    log_ret_inf += np.where(ev < (cp / 100), np.log(1 - 0.16), 0.0)  # -16%
    log_ret_off += np.where(ev > (1 - pp / 100), np.log(1 + 0.09), 0.0)
    log_ret_inf += np.where(ev > (1 - pp / 100), np.log(1 + 0.06), 0.0)

    sp_off[t] = sp_off[t - 1] * np.exp(log_ret_off)
    sp_inf[t] = sp_inf[t - 1] * np.exp(log_ret_inf)
    si[t]     = si[t - 1] * (1 + hi)

sp_tot = np.zeros((anni + 1, it))
for t in range(anni + 1):
    sp_tot[t] = (1 - pesi_sommerso[t]) * sp_off[t] + pesi_sommerso[t] * sp_inf[t]

# --- 5. GRAFICI (identici all'originale) ---
x_p = np.arange(2026, 2026 + anni + 1)
c1, c2 = st.columns(2)

f1, a1 = plt.subplots(figsize=(8, 4))
p_tot = np.percentile(sp_tot, [5, 50, 95], axis=1)
p_off = np.percentile(sp_off, 50, axis=1)
p_inf = np.percentile(sp_inf, 50, axis=1)

a1.plot(h_y, h_p, 'ko-', lw=2, label="Storico 23-26")
a1.plot(x_p, sp_tot[:, :100], color='gray', alpha=0.03)
a1.fill_between(x_p, p_tot[0], p_tot[2],
                color='#0D47A1', alpha=0.2, label="Rischio Totale 90%")
a1.plot(x_p, p_off,    color='#d62728', lw=2, linestyle=':',  label="Stato (Ufficiale)")
a1.plot(x_p, p_inf,    color='#ff7f0e', lw=2, linestyle='-.', label="Mercato Nero")
a1.plot(x_p, p_tot[1], color='#1565C0', lw=3,                 label="PIL Reale Effettivo")
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
st.subheader("Analisi (Scenari 2029)")

# ← MODIFICA CHIAVE: skewness e kurtosi sui LOG-RENDIMENTI cumulati,
#   non sui livelli assoluti. I livelli di un GBM hanno SEMPRE skewness
#   positiva (proprietà matematica del lognormale). I log-rendimenti
#   riflettono correttamente l'asimmetria degli shock sottostanti.
log_ret_3y = np.log(sp_tot[-1] / 100.0)
m_lr, s_lr = np.mean(log_ret_3y), np.std(log_ret_3y)
sk = np.mean(((log_ret_3y - m_lr) / s_lr) ** 3)
ku = np.mean(((log_ret_3y - m_lr) / s_lr) ** 4) - 3

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
    help="Calcolata sui log-rendimenti cumulati 3Y. "
         "Se negativo: gli shock avversi pesano più delle riprese."
)
m4.metric(
    "Kurtosis (Rischio Code)",
    f"{ku:.2f}",
    help="Se alto, alta probabilità di eventi estremi (Black Swans)."
)
