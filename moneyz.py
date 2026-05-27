import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import time
from datetime import datetime

# 1. LIVE DASHBOARD CONFIGURATIONS
st.set_page_config(page_title="EGP Wealth Center", layout="wide")
st.title("🏆 Unified Financial Command Center (EGP)")
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

# 🔄 SIDEBAR CONTROL PANEL
st.sidebar.markdown("## ⚙️ Data Control Center")
selected_month = st.sidebar.text_input("Active Analytics Month (YYYY-MM)", datetime.now().strftime('%Y-%m'))

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
    
    # Isolate Expenses Matrix (Columns A-D)
    exp = raw_df.iloc[2:, [0, 1, 2, 3]].copy()
    exp.columns = ['Date', 'Amount', 'Description', 'Category']
    exp['Amount'] = exp['Amount'].apply(clean_numeric)
    exp = exp[exp['Amount'] > 0]
    exp['Type'] = 'Expense'
    exp['Date'] = pd.to_datetime(exp['Date'], format='mixed', errors='coerce').fillna(datetime.now())
    
    # Isolate Income Matrix (Columns F-I)
    inc = raw_df.iloc[2:, [5, 6, 7, 8]].copy()
    inc.columns = ['Date', 'Amount', 'Description', 'Category']
    inc['Amount'] = inc['Amount'].apply(clean_numeric)
    inc = inc[inc['Amount'] > 0]
    inc['Type'] = 'Income'
    inc['Date'] = pd.to_datetime(inc['Date'], format='mixed', errors='coerce').fillna(datetime.now())
    
    combined = pd.concat([exp, inc], ignore_index=True)
    combined['Month'] = combined['Date'].dt.to_period('M').astype(str)
    return combined, raw_df

try:
    df, raw_spreadsheet = load_realtime_database()
except Exception as e:
    st.error(f"❌ Spreadsheet Connection Failure: {e}")
    st.stop()

# Filter datasets down to chosen active month view safely
month_df = df[df['Month'] == selected_month] if not df.empty else pd.DataFrame()
month_expenses = month_df[month_df['Type'] == 'Expense'] if not month_df.empty else pd.DataFrame()
actual_spending_map = month_expenses.groupby('Category')['Amount'].sum().to_dict() if not month_expenses.empty else {}

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
# SECTION 2: LIVE PERFORMANCE STATUS LEDGER
# =========================================================
st.subheader("📋 Structural Financial Performance Status Ledger")

status_records = []
for category, planned in PLANNED_BUDGETS.items():
    actual = actual_spending_map.get(category, 0.0)
    pct_of_plan = (actual / planned) if planned > 0 else 0.0
    remaining = planned - actual
    
    # STRICT USER STATUS THRESHOLD IMPLEMENTATION:
    # Red: Exceeding planned limits
    # Yellow: Below planned but within 15% of the ceiling (85% - 100% consumed)
    # Green: Safely below planned by more than 30% (0% - 70% consumed)
    if actual > planned:
        status_label = "🔴 Red (Exceeding Planned Ceiling)"
    elif actual >= (planned * 0.85):
        status_label = "🟡 Yellow (Warning: Within 15% of Cap)"
    elif actual <= (planned * 0.70):
        status_label = "🟢 Green (Safe: Below Planned by 30%+)"
    else:
        status_label = "🟢 Green (Safe Baseline Usage)"
        
    status_records.append({
        "Expense Category": category,
        "Planned Cap (EGP)": f"{planned:,.2f}",
        "Actual Spent (EGP)": f"{actual:,.2f}",
        "Remaining Balance (EGP)": f"{remaining:,.2f}",
        "Cap Consumed %": f"{pct_of_plan * 100:.1f}%",
        "Current Spending Status": status_label
    })

st.dataframe(pd.DataFrame(status_records), use_container_width=True)
st.markdown("---")

# =========================================================
# SECTION 3: TARGETED ANALYTICS CHARTS (EXACTLY TWO VISUALS)
# =========================================================
st.subheader(f"📊 Macro Pacing & Savings Visualization for {selected_month}")
chart_col_left, chart_col_right = st.columns(2)

with chart_col_left:
    # CHART 1: OVERALL PERFORMANCE OF PLANNED VS ACTUAL (BAR CHART)
    bar_data = []
    for category, planned in PLANNED_BUDGETS.items():
        actual = actual_spending_map.get(category, 0.0)
        bar_data.append({"Category": category, "EGP Amount": planned, "Metrics Layout": "Planned Cap Baseline"})
        bar_data.append({"Category": category, "EGP Amount": actual, "Metrics Layout": "Actual Live Outflow"})
        
    if bar_data:
        fig_bar = px.bar(
            pd.DataFrame(bar_data),
            x="Category",
            y="EGP Amount",
            color="Metrics Layout",
            barmode="group",
            title="Planned Caps vs. Actual Live Outflows",
            color_discrete_map={"Planned Cap Baseline": "#3498db", "Actual Live Outflow": "#e74c3c"}
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="overall_planned_vs_actual_bar")
    else:
        st.info("No expense data found to populate bar matrix.")

with chart_col_right:
    # CHART 2: OVERALL SAVINGS % OF TOTAL INCOME (PIE CHART)
    total_income = month_df[month_df['Type'] == 'Income']['Amount'].sum() if not month_df.empty else 0.0
    total_expenses = month_expenses['Amount'].sum() if not month_expenses.empty else 0.0
    net_savings = max(0.0, total_income - total_expenses)
    
    if total_income > 0:
        pie_df = pd.DataFrame({
            "Financial Metric": ["Total Expenses Logged", "Net Accumulated Savings"],
            "EGP Volume": [total_expenses, net_savings]
        })
        fig_pie = px.pie(
            pie_df,
            names="Financial Metric",
            values="EGP Volume",
            hole=0.4,
            title=f"Overall Monthly Savings % of Total Income (Total: {total_income:,.2f} EGP)",
            color_discrete_sequence=["#e74c3c", "#2ecc71"]
        )
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True, key="savings_ratio_pie_chart")
    else:
        st.info("Enter monthly income via Tab 1 form to generate the Savings Ratio Pie Chart.")

st.markdown("---")
st.markdown("### 📋 Back-End Raw Cell Feed Ledger")
st.dataframe(raw_spreadsheet.fillna(""), use_container_width=True)
