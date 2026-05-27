import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# 1. LIVE PAGE SETTINGS
st.set_page_config(page_title="EGP Wealth Hub", layout="wide")
st.title("🏆 Advanced Financial Command Center (EGP)")
st.markdown("---")

# 2. ESTABLISH SECURE DATA CONNECTIONS
SHEET_ID = "1dwZFbG_ibYGO7msBOl2cFnnX4_A-KJ5tkaKJ5XI2Tj8"
csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Transactions"

# Web App Execution endpoint
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzJwFoRsR4GBBctlWQlTvwpeQM6sG1Kd-71KoMUe7uDiTKKGjtLLMnqPWO1fKC1FWIPWQ/exec"

# Hardcoded Baseline Target Ceilings from your master planning schema
PLANNED_BUDGETS = {
    'Food': 15000.0, 'Allowance': 4000.0, 'Medication/Health': 3500.0,
    'Mother': 4000.0, 'Gas': 1500.0, 'BabySitter': 11000.0, 'Nurse': 1000.0,
    'Physical Therapy': 7200.0, 'Rent': 14200.0, 'Rent 2': 1500.0, 'Credit Card': 10000.0
}
TOTAL_MONTHLY_PLANNED_EXPENSE = sum(PLANNED_BUDGETS.values())

def clean_numeric(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    val_cleaned = str(val).replace('£', '').replace('$', '').replace(',', '').strip()
    try: return float(val_cleaned)
    except: return 0.0

@st.cache_data(ttl=1)
def load_side_by_side_data():
    raw_df = pd.read_csv(csv_url, header=None)
    
    # Process Expenses (Columns A-D)
    exp_raw = raw_df.iloc[2:, [0, 1, 2, 3]].copy()
    exp_raw.columns = ['Date', 'Amount', 'Description', 'Category']
    exp_raw['Amount'] = exp_raw['Amount'].apply(clean_numeric)
    exp_raw = exp_raw[exp_raw['Amount'] > 0]
    exp_raw['Type'] = 'Expense'
    exp_raw['Is_Liquid'] = True
    exp_raw['Date'] = pd.to_datetime(exp_raw['Date'], errors='coerce')
    
    # Process Income (Columns F-I)
    inc_raw = raw_df.iloc[2:, [5, 6, 7, 8]].copy()
    inc_raw.columns = ['Date', 'Amount', 'Description', 'Category']
    inc_raw['Amount'] = inc_raw['Amount'].apply(clean_numeric)
    inc_raw = inc_raw[inc_raw['Amount'] > 0]
    inc_raw['Type'] = 'Income'
    
    def check_liquidity(row):
        desc = str(row['Description']).lower()
        cat = str(row['Category']).lower()
        if 'side project' in desc or 'other' in cat or row['Amount'] in [150500.0, 78000.0]:
            return False
        return True
        
    if not inc_raw.empty:
        inc_raw['Is_Liquid'] = inc_raw.apply(check_liquidity, axis=1)
    else:
        inc_raw['Is_Liquid'] = True
        
    inc_raw['Date'] = pd.to_datetime(inc_raw['Date'], errors='coerce')
    
    combined = pd.concat([exp_raw, inc_raw], ignore_index=True).dropna(subset=['Date'])
    combined['Month'] = combined['Date'].dt.to_period('M').astype(str)
    return combined, raw_df

try:
    df, raw_spreadsheet = load_side_by_side_data()
except Exception as e:
    st.error(f"❌ Connection Sync Error: {e}")
    st.stop()

# 3. APP NAVIGATION TABS (DELETION COMPONENT COMPLETELY REMOVED)
tab_input, tab_visuals = st.tabs(["📥 Tab 1: Live Data Entry Form", "📊 Tab 2: Visual Ceiling Analytics"])

# =========================================================
# TAB 1: LIVE DATA ENTRY FORM
# =========================================================
with tab_input:
    st.markdown("<h3 style='color: #3498db;'>📝 Add Transaction Live</h3>", unsafe_allow_html=True)
    
    with st.form("dynamic_entry_form", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            entry_date = st.date_input("Transaction Date", datetime.now().date())
            entry_type = st.selectbox("Transaction Type", ["Expense", "Income"])
        with col_f2:
            entry_amount = st.number_input("Amount (EGP)", min_value=0.0, step=500.0)
            entry_desc = st.text_input("Description Context", placeholder="e.g., Carrefour Basket")
        with col_f3:
            entry_cat = st.selectbox("Category Grouping", list(PLANNED_BUDGETS.keys()) + ['Paycheck', 'Savings', 'Other'])
            
        save_trigger = st.form_submit_button("🔒 Save Entry to Google Sheet")
        
        if save_trigger and entry_amount > 0:
            payload = {"date": entry_date.strftime("%m/%d/%Y"), "amount": entry_amount, "description": entry_desc, "category": entry_cat, "type": entry_type}
            try:
                response = requests.post(WEBAPP_URL, json=payload)
                if response.status_code == 200 and "Success" in response.text:
                    st.balloons()
                    st.success("Record appended successfully!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("⚠️ Google Connection Refused Entry.")
            except Exception as api_err:
                st.error(f"Network link failure: {api_err}")

    st.markdown("---")
    st.markdown("### 📋 Previewing Your Live Side-by-Side Database")
    st.dataframe(raw_spreadsheet.fillna(""), use_container_width=True)

# =========================================================
# TAB 2: ENHANCED VISUAL CEILING METERS
# =========================================================
with tab_visuals:
    unique_months = sorted(df['Month'].unique())
    rolling_balance = 0.0
    monthly_aggregates = {}
    historical_trends = []

    for m in unique_months:
        m_df = df[df['Month'] == m]
        liquid_inflow = m_df[(m_df['Type'] == 'Income') & (m_df['Is_Liquid'] == True)]['Amount'].sum()
        total_outflow = m_df[m_df['Type'] == 'Expense']['Amount'].sum()
        start_bal = rolling_balance
        net_savings = liquid_inflow - total_outflow
        end_bal = start_bal + net_savings
        
        monthly_aggregates[m] = {"Start": start_bal, "Income": liquid_inflow, "Expenses": total_outflow, "End": end_bal}
        historical_trends.append({"Month": m, "Accumulated Cash Savings": end_bal, "Total Income": liquid_inflow, "Total Expenses": total_outflow})
        rolling_balance = end_bal

    history_df = pd.DataFrame(historical_trends)

    st.sidebar.markdown("---")
    selected_month = st.sidebar.selectbox("Filter Chart Month View", unique_months, index=len(unique_months)-1 if unique_months else 0)
    
    if selected_month:
        metrics = monthly_aggregates[selected_month]
        month_exp = df[(df['Month'] == selected_month) & (df['Type'] == 'Expense')].copy()
        
        # 📊 UPGRADE 1: OVERALL MONTHLY EXPENSE MASTER METER
        st.subheader("🏁 Overall Monthly Expense vs. Planned Budget Ceiling")
        total_actual_expenses = metrics['Expenses']
        pct_total_consumed = total_actual_expenses / TOTAL_MONTHLY_PLANNED_EXPENSE if TOTAL_MONTHLY_PLANNED_EXPENSE > 0 else 0.0
        
        if pct_total_consumed >= 1.0: overall_color = "#e74c3c"     # Red (Exceeded limits)
        elif pct_total_consumed >= 0.85: overall_color = "#f39c12"  # Amber Yellow (Danger Warning zone)
        else: overall_color = "#2ecc71"                             # Green (Safe budget pacing)
        
        fig_overall = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = total_actual_expenses,
            delta = {'reference': TOTAL_MONTHLY_PLANNED_EXPENSE, 'position': "top", 'valueformat': ',.2f EGP'},
            gauge = {
                'axis': {'range': [None, max(TOTAL_MONTHLY_PLANNED_EXPENSE * 1.2, total_actual_expenses * 1.1)], 'tickformat': ',.0f EGP'},
                'bar': {'color': overall_color},
                'steps': [
                    {'range': [0, TOTAL_MONTHLY_PLANNED_EXPENSE * 0.85], 'color': "rgba(46, 204, 113, 0.1)"},
                    {'range': [TOTAL_MONTHLY_PLANNED_EXPENSE * 0.85, TOTAL_MONTHLY_PLANNED_EXPENSE], 'color': "rgba(243, 156, 18, 0.1)"},
                    {'range': [TOTAL_MONTHLY_PLANNED_EXPENSE, max(TOTAL_MONTHLY_PLANNED_EXPENSE * 1.2, total_actual_expenses * 1.1)], 'color': "rgba(231, 76, 60, 0.1)"}
                ],
                'threshold': {
                    'line': {'color': "#c0392b", 'width': 5},
                    'thickness': 0.8,
                    'value': TOTAL_MONTHLY_PLANNED_EXPENSE
                }
            }
        ))
        fig_overall.update_layout(height=280, margin=dict(l=50, r=50, t=40, b=20))
        st.plotly_chart(fig_overall, use_container_width=True, key="overall_master_budget_gauge")

        st.markdown("---")
        
        # Core Metrics KPI Panel Blocks
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🎬 Start Pool Balance", f"{metrics['Start']:,.2f} EGP")
        m2.metric("📥 Liquid Inflow (Green/Blue)", f"{metrics['Income']:,.2f} EGP")
        m3.metric("📤 Total Expenses (Red)", f"{metrics['Expenses']:,.2f} EGP")
        m4.metric("🏁 Net Rolling Cash Pool", f"{metrics['End']:,.2f} EGP")
        
        st.markdown("---")
        
        # Daily Velocity Run-rate Pacing Plot
        st.subheader("📉 Micro Spending Velocity & Burn-Rate Pacing")
        month_exp['Day'] = month_exp['Date'].dt.day
        daily_timeline = pd.DataFrame({'Day': range(1, 31)})
        daily_sums = month_exp.groupby('Day')['Amount'].sum().reset_index()
        daily_timeline = pd.merge(daily_timeline, daily_sums, on='Day', how='left').fillna(0.0)
        daily_timeline['Actual Cumulative Spend'] = daily_timeline['Amount'].cumsum()
        daily_timeline['Target Ceiling Slope'] = (TOTAL_MONTHLY_PLANNED_EXPENSE / 30.0) * daily_timeline['Day']
        
        fig_pacing = go.Figure()
        fig_pacing.add_trace(go.Scatter(x=daily_timeline['Day'], y=daily_timeline['Target Ceiling Slope'], name="Ideal Burn Rate Slope (Yellow)", line=dict(color='#f1c40f', width=2, dash='dash')))
        fig_pacing.add_trace(go.Scatter(x=daily_timeline['Day'], y=daily_timeline['Actual Cumulative Spend'], name="Your Realized Outflow Velocity (Blue)", line=dict(color='#3498db', width=4)))
        fig_pacing.update_layout(xaxis_title="Day of Month Timeline", yaxis_title="EGP Value Outflow Pool")
        st.plotly_chart(fig_pacing, use_container_width=True, key="daily_burnrate_pacing_trend")
        
        st.markdown("---")
        
        # 🚨 UPGRADE 2: ENHANCED COLORFUL CATEGORY CEILING METERS
        st.subheader("🚨 Category Expense Cap Alert Threshold Matrix")
        cat_cols_1, cat_cols_2 = st.columns(2)
        actual_cat_spending = month_exp.groupby('Category')['Amount'].sum().to_dict()
        
        for idx, (category, planned_cap) in enumerate(PLANNED_BUDGETS.items()):
            actual_spent = actual_cat_spending.get(category, 0.0)
            pct_consumed = (actual_spent / planned_cap) if planned_cap > 0 else 0.0
            
            if pct_consumed >= 1.0: color_hex = "#e74c3c"
            elif pct_consumed >= 0.85: color_hex = "#f39c12"
            else: color_hex = "#2ecc71"
            
            target_column = cat_cols_1 if idx % 2 == 0 else cat_cols_2
            with target_column:
                st.markdown(f"**{category}** (Cap: {planned_cap:,.0f} EGP)")
                fig_progress = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = actual_spent,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [None, max(planned_cap * 1.2, actual_spent * 1.1)], 'tickformat': ',.0f EGP'},
                        'bar': {'color': color_hex},
                        'steps': [
                            {'range': [0, planned_cap * 0.85], 'color': "rgba(46, 204, 113, 0.05)"},
                            {'range': [planned_cap * 0.85, planned_cap], 'color': "rgba(243, 156, 18, 0.05)"},
                            {'range': [planned_cap, max(planned_cap * 1.2, actual_spent * 1.1)], 'color': "rgba(231, 76, 60, 0.05)"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 3},
                            'thickness': 0.75,
                            'value': planned_cap
                        }
                    }
                ))
                fig_progress.update_layout(height=145, margin=dict(l=30, r=30, t=15, b=15))
                st.plotly_chart(fig_progress, use_container_width=True, key=f"enhanced_gauge_chart_{category}")
