"""
Banking KRI (Key Risk Indicator) Dashboard
-------------------------------------------
A single-file Streamlit app tracking core banking risk indicators: asset
quality (NPL Ratio), capital adequacy (CAR), liquidity (LCR), and
operational/fraud/conduct risk events — across regions and loan portfolios,
with monthly trend charts and interactive filters. Built with Plotly.

Note on KRI vs KPI: a KPI tells you how well the business is performing;
a KRI tells you how much risk exposure the business is carrying. This
dashboard focuses purely on trend visibility (no red/amber/green threshold
system) to keep it simple and readable.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# PAGE CONFIG & STYLE
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Banking KRI Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        border-radius: 12px;
        padding: 14px 18px 10px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    div[data-testid="stMetricLabel"] {font-size: 0.85rem; color: #64748b;}
    section[data-testid="stSidebar"] {background-color: #f5f6fa;}
    h1, h2, h3 {font-family: 'Segoe UI', sans-serif; color: #1e293b;}
    .info-note {
        background-color: #eef2ff; border: 1px solid #c7d2fe; border-radius: 8px;
        padding: 10px 14px; font-size: 0.85rem; color: #3730a3; margin-bottom: 1rem;
    }
    .footer-note {color: #9ca3af; font-size: 0.8rem; margin-top: 2rem;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

TEMPLATE = "plotly_white"
COLOR_SEQ = px.colors.qualitative.Set2


# ----------------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------------
@st.cache_data
def load_data(path: str = "data.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    df["Month_Label"] = df["Date"].dt.strftime("%b %Y")
    return df


try:
    raw_df = load_data()
except FileNotFoundError:
    st.error("`data.csv` not found. Make sure it sits next to app.py in the project folder.")
    st.stop()

if raw_df.empty:
    st.warning("The dataset is empty — nothing to show yet.")
    st.stop()

# ----------------------------------------------------------------------------
# SIDEBAR — FILTERS
# ----------------------------------------------------------------------------
st.sidebar.title("🔎 Filters")

min_date, max_date = raw_df["Date"].min(), raw_df["Date"].max()
date_range = st.sidebar.date_input(
    "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

region_options = sorted(raw_df["Region"].unique())
selected_regions = st.sidebar.multiselect("Region", region_options, default=region_options)

portfolio_options = sorted(raw_df["Portfolio"].unique())
selected_portfolios = st.sidebar.multiselect("Loan Portfolio", portfolio_options, default=portfolio_options)

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit + Plotly · Demo banking risk dataset (2024–2025)")

# ----------------------------------------------------------------------------
# APPLY FILTERS
# ----------------------------------------------------------------------------
mask = (
    (raw_df["Date"] >= pd.to_datetime(start_date))
    & (raw_df["Date"] <= pd.to_datetime(end_date))
    & (raw_df["Region"].isin(selected_regions))
    & (raw_df["Portfolio"].isin(selected_portfolios))
)
df = raw_df.loc[mask].copy()

st.title("🛡️ Banking KRI Dashboard")
st.caption("Monitor key risk indicators — asset quality, capital adequacy, liquidity, "
           "and operational/fraud risk — across regions and loan portfolios.")
st.markdown(
    '<div class="info-note">ℹ️ <b>KRI vs KPI:</b> a KPI shows how well the bank is '
    'performing; a KRI shows how much risk exposure it is carrying. This view is '
    'trend-only — no red/amber/green thresholds are applied.</div>',
    unsafe_allow_html=True,
)

if df.empty:
    st.info("No records match the current filters. Try widening the date range or selections.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI / KRI SUMMARY ROW
# ----------------------------------------------------------------------------
avg_npl = df["NPL_Ratio"].mean()
avg_car = df["CAR_Ratio"].mean()
avg_lcr = df["LCR_Ratio"].mean()
total_op_events = df["Operational_Loss_Events"].sum()
total_fraud = df["Fraud_Incidents"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📉 Avg NPL Ratio", f"{avg_npl:.2f}%", help="Non-Performing Loan ratio — asset quality risk")
k2.metric("🏦 Avg CAR", f"{avg_car:.2f}%", help="Capital Adequacy Ratio — solvency risk (Basel III min ≈10.5%)")
k3.metric("💧 Avg LCR", f"{avg_lcr:.1f}%", help="Liquidity Coverage Ratio — regulatory minimum = 100%")
k4.metric("⚠️ Operational Loss Events", f"{total_op_events:,}", help="Process/system failure events")
k5.metric("🚨 Fraud Incidents", f"{total_fraud:,}", help="Reported fraud cases")

st.markdown("---")

# ----------------------------------------------------------------------------
# ROW 1 — Asset Quality & Capital Trend
# ----------------------------------------------------------------------------
st.subheader("Asset Quality & Capital Trend")
trend_df = df.groupby("Date", as_index=False).agg(
    NPL_Ratio=("NPL_Ratio", "mean"), CAR_Ratio=("CAR_Ratio", "mean"), LCR_Ratio=("LCR_Ratio", "mean"),
).sort_values("Date")
fig_trend = px.line(
    trend_df, x="Date", y=["NPL_Ratio", "CAR_Ratio", "LCR_Ratio"], markers=True,
    template=TEMPLATE, color_discrete_sequence=["#dc2626", "#2563eb", "#16a34a"],
)
fig_trend.update_layout(yaxis_title="Ratio (%)", xaxis_title="Month", legend_title="")
st.plotly_chart(fig_trend, use_container_width=True)

# ----------------------------------------------------------------------------
# ROW 2 — Risk Events Trend (Operational Loss Events + Fraud Incidents)
# ----------------------------------------------------------------------------
st.subheader("Operational & Fraud Risk Events Trend")
events_df = df.groupby("Date", as_index=False).agg(
    Operational_Loss_Events=("Operational_Loss_Events", "sum"),
    Fraud_Incidents=("Fraud_Incidents", "sum"),
).sort_values("Date")

fig_events = go.Figure()
fig_events.add_trace(go.Bar(
    x=events_df["Date"], y=events_df["Operational_Loss_Events"], name="Operational Loss Events",
    marker_color="#93c5fd",
))
fig_events.add_trace(go.Scatter(
    x=events_df["Date"], y=events_df["Fraud_Incidents"], name="Fraud Incidents",
    mode="lines+markers", line=dict(color="#dc2626", width=3),
))
fig_events.update_layout(
    template=TEMPLATE, yaxis_title="Number of Events", xaxis_title="Month",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    barmode="group",
)
st.plotly_chart(fig_events, use_container_width=True)

# ----------------------------------------------------------------------------
# ROW 3 — Risk by Region | Risk by Portfolio
# ----------------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Avg NPL Ratio by Region")
    region_df = df.groupby("Region", as_index=False)["NPL_Ratio"].mean().sort_values(
        "NPL_Ratio", ascending=False)
    fig_region = px.bar(
        region_df, x="Region", y="NPL_Ratio", text_auto=".2f",
        color="Region", color_discrete_sequence=COLOR_SEQ, template=TEMPLATE,
    )
    fig_region.update_layout(showlegend=False, yaxis_title="NPL Ratio (%)", xaxis_title="")
    st.plotly_chart(fig_region, use_container_width=True)

with c2:
    st.subheader("Loan Default Exposure by Portfolio")
    portfolio_df = df.groupby("Portfolio", as_index=False)["Loan_Default_Amount"].sum().sort_values(
        "Loan_Default_Amount", ascending=False)
    fig_portfolio = px.pie(
        portfolio_df, names="Portfolio", values="Loan_Default_Amount", hole=0.45,
        color_discrete_sequence=COLOR_SEQ, template=TEMPLATE,
    )
    fig_portfolio.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_portfolio, use_container_width=True)

# ----------------------------------------------------------------------------
# ROW 4 — Customer Complaints Trend (conduct / reputational risk)
# ----------------------------------------------------------------------------
st.subheader("Customer Complaints Trend")
complaints_df = df.groupby("Date", as_index=False)["Customer_Complaints"].sum().sort_values("Date")
fig_complaints = px.area(
    complaints_df, x="Date", y="Customer_Complaints",
    color_discrete_sequence=["#f59e0b"], template=TEMPLATE,
)
fig_complaints.update_layout(yaxis_title="Complaints", xaxis_title="Month")
st.plotly_chart(fig_complaints, use_container_width=True)

# ----------------------------------------------------------------------------
# DETAIL TABLE
# ----------------------------------------------------------------------------
with st.expander("🔍 View filtered raw data"):
    st.dataframe(
        df.sort_values("Date", ascending=False).drop(columns=["Month_Label"]).reset_index(drop=True),
        use_container_width=True,
    )
    st.download_button(
        "Download filtered data as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_kri_data.csv",
        mime="text/csv",
    )

st.markdown(
    '<p class="footer-note">Banking KRI Dashboard · Demo project · Data is synthetic, '
    'generated for educational / prototyping purposes.</p>',
    unsafe_allow_html=True,
)
