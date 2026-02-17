import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- 2026 TAX DATA (OBBB Rules) ---
DATA_2026 = {
    "Single": {
        "std": 16100, "senior_deduction": 6500,
        "ord": [(0, 12400, 10), (12400, 50400, 12), (50400, 105700, 22), (105700, 201775, 24), 
                (201775, 256225, 32), (256225, 640600, 35), (640600, 9e9, 37)],
        "ltcg": [(0, 49450, 0), (49450, 545500, 15), (545500, 9e9, 20)],
        "ss_t": (25000, 34000), "phaseout_start": 75000, "niit": 200000, 
        "irmaa": [109000, 136000, 170000, 204000, 500000]
    },
    "Married Filing Jointly": {
        "std": 32200, "senior_deduction": 13000,
        "ord": [(0, 24800, 10), (24800, 100800, 12), (100800, 211400, 22), (211400, 403550, 24), 
                (403550, 512450, 32), (512450, 768700, 35), (768700, 9e9, 37)],
        "ltcg": [(0, 98900, 0), (98900, 613700, 15), (613700, 9e9, 20)],
        "ss_t": (32000, 44000), "phaseout_start": 150000, "niit": 250000, 
        "irmaa": [218000, 272000, 340000, 408000, 750000]
    }
}

# --- CALLBACK TO SYNC SIDEBAR ---
def update_defaults():
    # Force the wage input to match the standard deduction of the selected status
    new_status = st.session_state["st_status"]
    st.session_state["wages"] = float(DATA_2026[new_status]["std"])

# Initialize session state for wages if it doesn't exist
if "wages" not in st.session_state:
    st.session_state["wages"] = 32200.0

def get_tax_details(wages, ltcg, ss, status, senior):
    c = DATA_2026[status]
    sd_used = 0
    if senior:
        # 6% phase-out of the senior deduction
        phase_out = max(0, (wages + ltcg - c["phaseout_start"]) * 0.06)
        sd_used = max(0, c["senior_deduction"] - phase_out)
    
    deduction = c["std"] + sd_used
    prov = wages + ltcg + (0.5 * ss)
    t1, t2 = c["ss_t"]
    taxable_ss = 0
    if prov > t2: 
        taxable_ss = min(0.85 * ss, (prov - t2) * 0.85 + min(6000 if status == "Married Filing Jointly" else 4500, 0.5 * ss))
    elif prov > t1: 
        taxable_ss = min(0.5 * ss, (prov - t1) * 0.5)
    
    t_ord_inc = max(0, (wages + taxable_ss) - deduction)
    ord_tax = 0; current_ord_rate = 0
    for low, high, rate in c["ord"]:
        if t_ord_inc > low:
            ord_tax += (min(t_ord_inc, high) - low) * (rate / 100)
            current_ord_rate = rate
    
    t_total = max(0, (wages + taxable_ss + ltcg) - deduction)
    l_portion = max(0, t_total - t_ord_inc); l_tax = 0; current_ltcg_rate = 0
    for low, high, rate in c["ltcg"]:
        overlap = max(0, min(t_ord_inc + l_portion, high) - max(t_ord_inc, low))
        l_tax += overlap * (rate / 100)
        if (t_ord_inc + l_portion) > low: current_ltcg_rate = rate
    
    niit = max(0, (wages + ltcg - c["niit"]) * 0.038)
    return ord_tax, l_tax, niit, taxable_ss, current_ord_rate, current_ltcg_rate, sd_used

# --- STREAMLIT UI ---
st.set_page_config(page_title="2026 Tax Analyzer", layout="wide")
st.title("2026 Marginal Tax Analyzer")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Income Parameters")
st_status = st.sidebar.selectbox(
    "Filing Status", 
    ["Married Filing Jointly", "Single"], 
    key="st_status", 
    on_change=update_defaults
)

# wages is bound to session state to allow the callback to overwrite it
wages = st.sidebar.number_input("Ordinary Wages ($)", key="wages", step=1000.0)
ltcg_input = st.sidebar.number_input("Long-Term Capital Gains ($)", value=20000, step=1000)
ss_income = st.sidebar.number_input("Annual Social Security ($)", value=40000, step=1000)
is_senior = st.sidebar.checkbox("Is 65 or Older?", value=True)
show_irmaa = st.sidebar.checkbox("Show IRMAA Lines", value=True)

# Math for current scenario
o_f, l_f, n_f, ss_f, br_f, lr_f, sd_f = get_tax_details(wages, ltcg_input, ss_income, st_status, is_senior)
total_tax = o_f + l_f + n_f
total_in = wages + ltcg_input + ss_income
eff_rate = (total_tax / total_in * 100) if total_in > 0 else 0

# --- SIDEBAR RESULTS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Live Analysis")
st.sidebar.metric("Total Tax Liability", f"${total_tax:,.0f}")
st.sidebar.metric("Effective Tax Rate", f"{eff_rate:.1f}%")

st.sidebar.markdown("---")
st.sidebar.write(f"**Taxable SS:** ${ss_f:,.0f}")
st.sidebar.write(f"**Standard Deduction:** ${DATA_2026[st_status]['std']:,.0f}")
st.sidebar.write(f"**Senior Ded. Used:** ${sd_f:,.0f}")
st.sidebar.write(f"**LTCG Marginal Rate:** {lr_f:.0f}%")
st.sidebar.write(f"**LTCG Eff. Rate:** {((l_f + n_f)/ltcg_input*100 if ltcg_input > 0 else 0):.1f}%")

# --- DATA GENERATION FOR PLOT ---
max_x = max(total_in * 2, 150000)
x_range = np.linspace(0, max_x, 800); delta = 1.0
stack_data = []; total_m_rates = []

for x in x_range:
    o1, l1, n1, ss1, br1, lr1, sd1 = get_tax_details(x, ltcg_input, ss_income, st_status, is_senior)
    o2, l2, n2, ss2, br2, lr2, sd2 = get_tax_details(x + delta, ltcg_input, ss_income, st_status, is_senior)
    
    total_m = ((o2 + l2 + n2) - (o1 + l1 + n1)) / delta * 100
    niit_m = (n2 - n1) / delta * 100
    ss_m = ((ss2 - ss1) / delta) * (br1 / 100) * 100
    ltcg_m = (l2 - l1) / delta * 100
    senior_m = ((sd1 - sd2) * (br1 / 100)) / delta * 100 if is_senior else 0
    ord_m = max(0, total_m - niit_m - ss_m - ltcg_m - senior_m)
    
    stack_data.append((ord_m, ltcg_m, ss_m, senior_m, niit_m))
    total_m_rates.append(total_m)

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(12, 6))
ax.stackplot(x_range, *zip(*stack_data), 
             labels=['Ordinary', 'LTCG Bump', 'Social Security', 'Senior Phase-out', 'NIIT'], 
             colors=['#4CAF50', '#2196F3', '#F44336', '#FFEB3B', '#FF9800'], alpha=0.8)

# Center Step Labeling Logic
step_indices = [0]
for i in range(1, len(total_m_rates)):
    if abs(total_m_rates[i] - total_m_rates[i-1]) > 0.1:
        step_indices.append(i)
step_indices.append(len(total_m_rates)-1)

for i in range(len(step_indices)-1):
    start, end = step_indices[i], step_indices[i+1]
    mid = (start + end) // 2
    # Only label brackets wider than 5% of the graph width
    if (x_range[end] - x_range[start]) > (max_x * 0.05):
        rate = total_m_rates[mid]
        ax.text(x_range[mid], rate + 1, f"{rate:.1f}%", 
                ha='center', fontweight='bold', fontsize=9,
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))

# Vertical line at current wage
ax.axvline(wages, color='black', lw=2, ls='--')

# Styling
ax.set_ylim(0, 60); ax.set_xlim(0, max_x)
ax.set_ylabel("Marginal Tax Rate (%)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax.legend(loc='upper right', ncol=3)
ax.grid(axis='y', alpha=0.3)

# === UPDATED IRMAA CODE STARTS HERE ===
if show_irmaa:
    irmaa_list = DATA_2026[st_status]["irmaa"]
    next_irmaa = next((tier for tier in irmaa_list if tier > wages), None)
    if next_irmaa:
        ax.axvline(next_irmaa, color='red', alpha=0.3, ls=':')
        ax.text(next_irmaa, 2, f"${next_irmaa:,.0f}",
                ha='center', va='bottom', color='red', fontsize=9, fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='red', pad=2))

st.pyplot(fig)

