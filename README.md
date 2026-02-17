# 2026 Marginal Tax Graphing Tool

This interactive Streamlit app helps visualize the marginal federal income tax rate for 2026 under proposed OBBB rules, including the effects of Social Security, long-term capital gains, senior deductions, and IRMAA (Medicare Part B premium) thresholds.

## What Does This Tool Do?

- **Draws a detailed marginal tax rate graph** for an individual or married couple based on user-supplied income and parameters.
- **Illustrates how various components (ordinary income, long-term capital gains, Social Security, Net Investment Income Tax, IRMAA surcharges, and senior phases)** contribute to your marginal tax rate.
- **Highlights the next IRMAA bump** (Medicare premium change) on the graph so you can see its effect on your projected taxes.

## What Information Do You Need Before Using?

You will need to know or estimate the following:
- **Filing Status:** Either "Single" or "Married Filing Jointly"
- **Ordinary Wages:** Your projected earned income (W-2, 1099, etc.)
- **Long-Term Capital Gains (LTCG):** Estimated LTCG for the year
- **Annual Social Security:** Your (and, if applicable, spouse's) anticipated annual Social Security benefit
- **If user (or spouse) is age 65 or older**
- **If you want to display IRMAA (Medicare premium) lines** on the marginal tax rate graph

## Usage

1. Launch the Streamlit app (locally or on Streamlit Community Cloud).
2. Enter your filing status and each of the income sources in the sidebar.
3. Toggle whether the user is a senior (65+).
4. Optionally, choose to display IRMAA thresholds on the graph.
5. The graph and sidebar will dynamically update with marginal rates, threshold labels, and total effective rate.

## Other Info

- The calculations reflect 2026 OBBB federal tax policy proposals and Medicare IRMAA brackets as coded in `DATA_2026` in the app.
- Marginal rates, effective rates, and all tax calculations are for educational and planning purposes only; actual tax law and computations may differ.
- IRMAA lines and thresholds will appear on the graph if and only if the next income threshold is within your displayed income range.

---

Contributions and suggestions welcome!