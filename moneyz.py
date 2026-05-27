import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import time
from datetime import datetime

# 1. LIVE DASHBOARD CONFIGURATIONS
st.set_page_config(page_title="EGP Wealth Center", layout="wide")
st.title("🏆 Financial Command Center (EGP)")
st.markdown("---")

# 2. SECURE CLOUD STORAGE LINKS
SHEET_ID = "1dwZFbG_ibYGO7msBOl2cFnnX4_A-KJ5tkaKJ5XI2Tj8"
GID_ID = "1026248782" 
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzJwFoRsR4GBBctlWQlTvwpeQM6sG1Kd-71KoMUe7uDiTKKGjtLLMnqPWO1fKC1FWIPWQ/exec"

# Master baseline spending boundaries
PLANNED_BUDGETS = {
    'Food': 15000.0, 'Allowance': 4000.0, 'Medication/Health': 3500.0,
    'Mother': 4000.0, 'Gas': 1500.0, 'BabySitter': 11000.0, 'Nurse': 1000.0,
    'Physical Therapy': 7200.0, 'Rent': 14200.0, 'Rent 2': 1500.0, 'Credit Card': 10000.0
}
TOTAL_PLANNED_EXPENSE = sum(PLANNED_BUDGETS.values())

# 🔄 SIDEBAR CONTROL PANEL
st.sidebar.markdown("## ⚙️ Data Control Center")
if st.sidebar.button("🔄 Sync & Force Refresh", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("Cache cleared! Re-fetching live cells...")
    time.sleep(0.3)
    st.rerun()

def clean_numeric(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    cleaned = str(val).replace('£', '').replace('$', '').replace(',', '').replace('EGP', '').strip()
    try: return float(cleaned)
    except: return 0.0

@st.cache_data(ttl=0)
def load_realtime_database():
    # Anti-caching query parameter injection
    live_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_ID}&cb={int(time.time())}"
    raw_df = pd.read_csv(live_url, header=None, dtype=str)
    
    # Anti-IndexError Protection: Pad columns if sheet shape is truncated
    while raw_df.shape[1] < 9:
        raw_df[raw_df.shape[1]] = ""
    
    # Isolate Expenses Matrix (Columns A-D)
    exp = raw_df.iloc[2:, [0, 1, 2, 3]].copy()
    exp.columns = ['Date', 'Amount', 'Description', 'Category']
    exp['Amount'] = exp['Amount'].apply(clean_numeric)
    exp = exp[exp['Amount'] > 0]
    exp['Type'] = 'Expense'
    exp['Date'] = pd.to_datetime(exp['Date'], format='mixed', errors='coerce').fillna(pd.Timestamp(datetime.now().date()))
    
    # Isolate Income Matrix (Columns F-I)
    inc = raw_df.iloc[2:, [5, 6, 7, 8]].copy()
    inc.columns = ['Date', 'Amount', 'Description', 'Category']
    inc['Amount'] = inc['Amount'].apply(clean_numeric)
    inc = inc[inc['Amount'] > 0]
    inc['Type'] = 'Income'
    inc['Date'] = pd.to_datetime(inc['Date'], format='mixed', errors='coerce').fillna(pd.Timestamp(datetime.now().date()))
    
    combined = pd.concat([exp, inc], ignore_index=True)
    combined['Month'] = combined['Date'].dt.to_period('M').astype(str)
    return combined, raw_df

try:
    df, raw_spreadsheet = load_realtime_database()
except Exception as e:
    st.error(f"❌ Spreadsheet Connection Failure: {e}")
    st.stop()

# Dynamic Month Selector Dropdown to completely eliminate spelling errors
if not df.empty:
    unique_months = sorted(df['Month'].unique())
else:
    unique_months = [datetime.now().strftime('%Y-%m')]
selected_month = st.sidebar.selectbox("Active View Month", unique_months, index=len(unique_months)-1)

# Filter datasets down to chosen active month view safely
month_df = df[df['Month'] == selected_month] if not df.empty else pd.DataFrame()
month_expenses = month_df[month_df['Type'] == 'Expense'] if not month_df.empty else pd.DataFrame()
month_income = month_df[month_df['Type'] == 'Income'] if not month_df.empty else pd.DataFrame()

# Robust lowercase/stripped category matching map
actual_spending_map = {}
if not month_expenses.empty:
    for cat, amt in month_expenses.groupby('Category')['Amount'].sum().items():
        actual_spending_map[str(cat).strip().lower()] = amt

# =========================================================
# SECTION 1: LIVE DATA ENTRY FORM
# =========================================================
st.subheader("📥 Log New Transaction Entry")
with st.form("unified_entry_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        entry_date = st.date_input("Transaction Date", datetime.now().date())
        entry_type = st.selectbox("Transaction Type", ["Expense", "Income"])
    with c2:
        entry_amount = st.number_input("Numerical Value (EGP)", min_value=0.0, step=500.0)
        entry_desc = st.text_input("Context / Vendor Notes", placeholder="e.g. Row Outflow Description")
    with c3:
        entry_cat = st.selectbox("Budget Allocation Category", list(PLANNED_BUDGETS.keys()) + ['Paycheck', 'Savings', 'Other'])
        
    if st.form_submit_button("🔒 Securely Commit Row to Google Sheet"):
        if entry_amount > 0:
            payload = {"date": entry_date.strftime("%m/%d/%Y"), "amount": entry_amount, "description": entry_desc, "category": entry_cat, "type": entry_type}
            try:
                res = requests.post(WEBAPP_URL, json=payload)
                if res.status_code == 200 and "Success" in res.text:
                    st.balloons()
                    st.success("Data successfully saved online!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Google Web App Rejected Payload.")
            except Exception as err:
                st.error(f"Network error: {err}")

st.markdown("---")

# =========================================================
# SECTION 2: PERFORMANCE STATUS LEDGER (WITH EXACT RULES)
# =========================================================
st.subheader(f"📋 Budget Cap Status Ledger for {selected_month}")

status_records = []
total_actual_spent = 0.0

for category, planned in PLANNED_BUDGETS.items():
    actual = actual_spending_map.get(category.strip().lower(), 0.0)
    total_actual_spent += actual
    remaining = planned - actual
    pct_used = (actual / planned * 100) if planned > 0 else 0.0
    
    # 🚨 EXACT USER STATUS THRESHOLD IMPLEMENTATION:
    # Red: Exceeding planned limits
    # Yellow: Below planned but within 15% of the ceiling (>= 85% consumed)
    # Green: Safely below planned by more than 30% (<= 70% consumed)
    if actual > planned:
        status_label = "🔴 Red (Exceeding Planned)"
    elif actual >= (planned * 0.85):
        status_label = "🟡 Yellow (Close to Ceiling)"
    else:
        status_label = "🟢 Green (Safe Target)"
        
    status_records.append({
        "Expense Category": category,
        "Planned Cap (EGP)": planned,
        "Actual Spent (EGP)": actual,
        "Remaining Balance (EGP)": remaining,
        "Cap Consumed %": f"{pct_used:.1f}%",
        "Current Spending Status": status_label
    })

perf_df = pd.DataFrame(status_records)
st.dataframe(perf_df, use_container_width=True)
st.markdown("---")

# =========================================================
# SECTION 3: TWO TARGETED CHARTS (OVERALL PERF & SAVINGS RATIO)
# =========================================================
st.subheader(f"📊 Macro Metrics for {selected_month}")
chart_col_left, chart_col_right = st.columns(2)

with chart_col_left:
    st.markdown("**Chart 1: Overall Monthly Expenses (Planned vs Actual)**")
    overall_bar_df = pd.DataFrame({
        "Budget Metric": ["Total Planned Budget", "Total Actual Expenses"],
        "EGP Amount": [TOTAL_PLANNED_EXPENSE, total_actual_spent]
    })
    fig_bar = px.bar(
        overall_bar_df,
        x="Budget Metric",
        y="EGP Amount",
        color="Budget Metric",
        text_auto=',.2f',
        color_discrete_map={"Total Planned Budget": "#3498db", "Total Actual Expenses": "#e74c3c"}
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="overall_performance_bar")

with chart_col_right:
    st.markdown("**Chart 2: Overall Savings % of Total Income**")
    total_income_val = month_income['Amount'].sum() if not month_income.empty else 0.0
    net_savings_val = max(0.0, total_income_val - total_actual_spent)
    
    if total_income_val > 0:
        pie_df = pd.DataFrame({
            "Financial Segment": ["Total Expenses", "Net Savings Balance"],
            "EGP Volume": [total_actual_spent, net_savings_val]
        })
        fig_pie = px.pie(
            pie_df,
            names="Financial Segment",
            values="EGP Volume",
            hole=0.4,
            color_discrete_sequence=["#e74c3c", "#2ecc71"]
        )
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True, key="savings_ratio_pie")
    else:
        st.info("💡 Please log your monthly income rows to populate the Savings Ratio Pie Chart.")

st.markdown("---")
st.markdown("### 📋 Live Side-by-Side Spreadsheet Cells Preview")
st.dataframe(raw_spreadsheet.fillna(""), use_container_width=True)
