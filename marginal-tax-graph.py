import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- 2026 TAX DATA (OBBB Rules) ---
# DATA_2026 stores all tax bracket and deduction info for each filing status
#  - std: standard deduction
#  - senior_deduction: extra deduction for seniors
#  - ord: ordinary income brackets (income range, top, marginal rate)
#  - ltcg: long-term capital gains brackets (same structure)
#  - ss_t: social security income taxation thresholds
#  - phaseout_start: where senior deduction starts to phase out
#  - niit: Net Investment Income Tax threshold
#  - irmaa: IRMAA (Medicare premium) thresholds
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
    # Called whenever the filing status changes.
    # Resets the wage input to the standard deduction of the selected status.
    new_status = st.session_state["st_status"]
    st.session_state["wages"] = float(DATA_2026[new_status]["std"])

# --- SESSION STATE INITIALIZATION ---
# If 'wages' is not initialized in Streamlit session state, 
# initialize it to the married joint standard deduction as default.
if "wages" not in st.session_state:
    st.session_state["wages"] = 32200.0

# --- TAX CALCULATION FUNCTION ---
def get_tax_details(wages, ltcg, ss, status, senior):
    """
    Compute all derived tax details for a given scenario.

    Args:
        wages (float): Earned ordinary income
        ltcg (float): Long term capital gains
        ss (float): Social Security annual income
        status (str): Filing status ("Single" or "Married Filing Jointly")
        senior (bool): Whether taxpayer is 65 or older

    Returns:
        ord_tax (float): Tax on ordinary income
        l_tax (float): Tax on long-term capital gains
        niit (float): Net Investment Income Tax
        taxable_ss (float): Taxable portion of SS
        current_ord_rate (float): Top ordinary marginal rate
        current_ltcg_rate (float): Top LTCG marginal rate
        sd_used (float): Senior deduction claimed
    """
    c = DATA_2026[status]

    sd_used = 0
    if senior:
        # 6% phase-out of the senior deduction above the threshold
        phase_out = max(0, (wages + ltcg - c["phaseout_start"]) * 0.06)
        sd_used = max(0, c["senior_deduction"] - phase_out)
    
    deduction = c["std"] + sd_used  # total deduction
    prov = wages + ltcg + (0.5 * ss)  # provisional income for SS taxation
    t1, t2 = c["ss_t"]
    taxable_ss = 0
    if prov > t2: 
        taxable_ss = min(0.85 * ss, (prov - t2) * 0.85 + min(6000 if status == "Married Filing Jointly" else 4500, 0.5 * ss))
    elif prov > t1: 
        taxable_ss = min(0.5 * ss, (prov - t1) * 0.5)
    
    t_ord_inc = max(0, (wages + taxable_ss) - deduction)  # taxed as ordinary income
    ord_tax = 0
    current_ord_rate = 0
    for low, high, rate in c["ord"]:
        if t_ord_inc > low:
            ord_tax += (min(t_ord_inc, high) - low) * (rate / 100)
            current_ord_rate = rate
    
    t_total = max(0, (wages + taxable_ss + ltcg) - deduction)
    l_portion = max(0, t_total - t_ord_inc)  # amount taxed as LTCG
    l_tax = 0
    current_ltcg_rate = 0
    for low, high, rate in c["ltcg"]:
        overlap = max(0, min(t_ord_inc + l_portion, high) - max(t_ord_inc, low))
        l_tax += overlap * (rate / 100)
        if (t_ord_inc + l_portion) > low:
            current_ltcg_rate = rate
    
    niit = max(0, (wages + ltcg - c["niit"]) * 0.038)  # Net Investment Income Tax if above threshold
    return ord_tax, l_tax, niit, taxable_ss, current_ord_rate, current_ltcg_rate, sd_used

# --- STREAMLIT APP CONFIGURATION ---
st.set_page_config(page_title="2026 Tax Analyzer", layout="wide")
st.title("2026 Marginal Tax Analyzer")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Income Parameters")
# Filing status selectbox (updates session state, triggers update_defaults)
st_status = st.sidebar.selectbox(
    "Filing Status", 
    ["Married Filing Jointly", "Single"], 
    key="st_status", 
    on_change=update_defaults
)
# Wage input. Bound to session state so it can be set programmatically
wages = st.sidebar.number_input("Ordinary Wages ($)", key="wages", step=1000.0)
# Long-term capital gains input
ltcg_input = st.sidebar.number_input("Long-Term Capital Gains ($)", value=20000, step=1000)
# Social security income input
ss_income = st.sidebar.number_input("Annual Social Security ($)", value=40000, step=1000)
# Checkbox: is the filer 65+?
is_senior = st.sidebar.checkbox("Is 65 or Older?", value=True)
# Checkbox: show IRMAA lines on the main graph?
show_irmaa = st.sidebar.checkbox("Show IRMAA Lines", value=True)

# --- TAX CALCULATIONS FOR CURRENT SCENARIO ---
# Compute taxes for sidebar metrics and graph
o_f, l_f, n_f, ss_f, br_f, lr_f, sd_f = get_tax_details(wages, ltcg_input, ss_income, st_status, is_senior)
total_tax = o_f + l_f + n_f  # total tax liability
total_in = wages + ltcg_input + ss_income  # total income
eff_rate = (total_tax / total_in * 100) if total_in > 0 else 0  # effective tax rate

# --- SIDEBAR RESULTS & METRICS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Live Analysis")
st.sidebar.metric("Total Tax Liability", f"${total_tax:,.0f}")
st.sidebar.metric("Effective Tax Rate", f"{eff_rate:.1f}%")
st.sidebar.markdown("---")
# Additional sidebar details
st.sidebar.write(f"**Taxable SS:** ${ss_f:,.0f}")
st.sidebar.write(f"**Standard Deduction:** ${DATA_2026[st_status]['std']:,.0f}")
st.sidebar.write(f"**Senior Ded. Used:** ${sd_f:,.0f}")
st.sidebar.write(f"**LTCG Marginal Rate:** {lr_f:.0f}%")
st.sidebar.write(f"**LTCG Eff. Rate:** {((l_f + n_f)/ltcg_input*100 if ltcg_input > 0 else 0):.1f}%")

# --- DATA GENERATION FOR PLOT ---
# Determine X range for plotting
max_x = max(total_in * 2, 150000)  # set x-axis maximum
x_range = np.linspace(0, max_x, 800)  # points to plot, covers wide income span
delta = 1.0  # increment to calculate marginal rates
stack_data = []  # all stacked marginal contributions for plotting
total_m_rates = []  # total marginal tax rates at each point

# For each possible income, calculate marginal tax components for stacking
for x in x_range:
    o1, l1, n1, ss1, br1, lr1, sd1 = get_tax_details(x, ltcg_input, ss_income, st_status, is_senior)
    o2, l2, n2, ss2, br2, lr2, sd2 = get_tax_details(x + delta, ltcg_input, ss_income, st_status, is_senior)
    
    # Total marginal rate: difference in total tax
    total_m = ((o2 + l2 + n2) - (o1 + l1 + n1)) / delta * 100
    # Specific components
    niit_m = (n2 - n1) / delta * 100  # marginal NIIT rate
    ss_m = ((ss2 - ss1) / delta) * (br1 / 100) * 100  # impact of SS portion
    ltcg_m = (l2 - l1) / delta * 100  # marginal LTCG rate
    senior_m = ((sd1 - sd2) * (br1 / 100)) / delta * 100 if is_senior else 0  # marginal senior deduction loss
    ord_m = max(0, total_m - niit_m - ss_m - ltcg_m - senior_m)  # remainder is ordinary marginal rate
    
    stack_data.append((ord_m, ltcg_m, ss_m, senior_m, niit_m))
    total_m_rates.append(total_m)

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(12, 6))

# Stackplot: colors for each component
ax.stackplot(
    x_range, *zip(*stack_data), 
    labels=['Ordinary', 'LTCG Bump', 'Social Security', 'Senior Phase-out', 'NIIT'], 
    colors=['#4CAF50', '#2196F3', '#F44336', '#FFEB3B', '#FF9800'], alpha=0.8
)

# --- Step/bracket labeling logic ---
# Identify the indices where the marginal rate changes for step labels
step_indices = [0]
for i in range(1, len(total_m_rates)):
    if abs(total_m_rates[i] - total_m_rates[i-1]) > 0.1:
        step_indices.append(i)
step_indices.append(len(total_m_rates)-1)  # always end
# For each bracket, label the middle with the marginal rate %
for i in range(len(step_indices)-1):
    start, end = step_indices[i], step_indices[i+1]
    mid = (start + end) // 2
    # Only label brackets wider than 5% of the graph width
    if (x_range[end] - x_range[start]) > (max_x * 0.05):
        rate = total_m_rates[mid]
        ax.text(x_range[mid], rate + 1, f"{rate:.1f}%", 
                ha='center', fontweight='bold', fontsize=9,
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))

# Draw vertical line at current entered wages
ax.axvline(wages, color='black', lw=2, ls='--')

# --- Graph styling ---
ax.set_ylim(0, 60)
ax.set_xlim(0, max_x)
ax.set_ylabel("Marginal Tax Rate (%)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax.legend(loc='upper right', ncol=3)
ax.grid(axis='y', alpha=0.3)

# Show only the next IRMAA line, not all
if show_irmaa:
    irmaa_list = DATA_2026[st_status]["irmaa"]  # All IRMAA thresholds
    next_irmaa = next((tier for tier in irmaa_list if tier > wages), None)  # Smallest threshold above current wages
    if next_irmaa is not None and next_irmaa <= max_x:  # Only draw if visible on the graph
        ax.axvline(next_irmaa, color='red', alpha=0.3, ls=':')
        ax.text(
            next_irmaa, 2, f"IRMAA\n${next_irmaa:,.0f}",
            ha='center', va='bottom', color='red', fontsize=9, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='red', pad=2)
        )

st.pyplot(fig)

