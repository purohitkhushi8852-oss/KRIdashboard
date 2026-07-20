"""
Generates a realistic synthetic monthly Key Risk Indicator (KRI) dataset for
a retail/commercial bank: asset quality, capital adequacy, liquidity, and
operational/fraud risk, across regions and loan portfolios.

KRIs included (standard banking risk categories):
- NPL_Ratio (%)        -> Credit / Asset Quality risk
- CAR_Ratio (%)         -> Capital Adequacy / Solvency risk (Basel III min ~10.5%)
- LCR_Ratio (%)         -> Liquidity risk (regulatory min = 100%)
- Loan_Default_Amount   -> Credit risk, dollar exposure
- Operational_Loss_Events -> Operational risk (process/system failures)
- Fraud_Incidents       -> Fraud / operational risk
- Customer_Complaints   -> Conduct / reputational risk
"""
import numpy as np
import pandas as pd

np.random.seed(11)

regions = ["North Zone", "South Zone", "East Zone", "West Zone"]
portfolios = ["Retail Banking", "Corporate Banking", "SME Banking"]

# Baseline risk profile differs by portfolio (corporate/SME loans carry more credit risk)
npl_base = {"Retail Banking": 2.2, "Corporate Banking": 4.5, "SME Banking": 5.5}
default_base = {"Retail Banking": 180000, "Corporate Banking": 650000, "SME Banking": 320000}
region_risk_factor = {"North Zone": 0.9, "South Zone": 1.1, "East Zone": 1.0, "West Zone": 1.2}

months = pd.date_range("2024-01-01", "2025-12-01", freq="MS")  # 24 months

rows = []
for i, month in enumerate(months):
    # Mild macro drift: NPL creeps up slightly in later months (simulated credit cycle softening)
    macro_drift = 1 + (i * 0.006)

    for region in regions:
        for portfolio in portfolios:
            rf = region_risk_factor[region]

            npl_ratio = round(np.clip(
                npl_base[portfolio] * rf * macro_drift + np.random.normal(0, 0.4), 0.5, 12), 2)

            car_ratio = round(np.clip(
                14.5 - (npl_ratio * 0.15) + np.random.normal(0, 0.5), 9.5, 18), 2)

            lcr_ratio = round(np.clip(
                125 - (npl_ratio * 1.2) + np.random.normal(0, 6), 85, 165), 1)

            loan_default_amount = round(max(
                default_base[portfolio] * rf * macro_drift * np.random.normal(1, 0.15), 0), 2)

            operational_loss_events = int(np.random.poisson(lam=1.5 * rf))
            fraud_incidents = int(np.random.poisson(lam=0.8 * rf))
            customer_complaints = int(np.random.poisson(lam=12 * rf))

            rows.append({
                "Date": month.strftime("%Y-%m-%d"),
                "Region": region,
                "Portfolio": portfolio,
                "NPL_Ratio": npl_ratio,
                "CAR_Ratio": car_ratio,
                "LCR_Ratio": lcr_ratio,
                "Loan_Default_Amount": loan_default_amount,
                "Operational_Loss_Events": operational_loss_events,
                "Fraud_Incidents": fraud_incidents,
                "Customer_Complaints": customer_complaints,
            })

df = pd.DataFrame(rows)
df.to_csv("data.csv", index=False)
print(f"Generated {len(df)} rows across {len(months)} months -> data.csv")
print(df.head())
