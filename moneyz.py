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

# 3. APP NAVIGATION TABS
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
# TAB 2: SIMPLIFIED CEILING PERFORMANCE VISUALS
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
        actual_cat_spending = month_exp.groupby('Category')['Amount'].sum().to_dict()
        
        # Build clean structural matrix metrics matching requirements
        performance_records = []
        breached_categories = []
        warning_categories = []

        for category, planned_cap in PLANNED_BUDGETS.items():
            actual_spent = actual_cat_spending.get(category, 0.0)
            pct_used = (actual_spent / planned_cap * 100) if planned_cap > 0 else 0.0
            remaining = planned_cap - actual_spent
            
            if actual_spent > planned_cap:
                status = "🔴 Breached"
                color_group = "Wiped Out (>100%)"
                breached_categories.append(f"⚠️ **{category}**: Exceeded limit by {abs(remaining):,.2f} EGP!")
            elif actual_spent >= planned_cap * 0.85:
                status = "🟡 Warning"
                color_group = "Danger Zone (85%-100%)"
                warning_categories.append(f"⚡ **{category}**: Consumed {pct_used:.1f}% of its cap.")
            else:
                status = "🟢 Safe"
                color_group = "Safe Under Target (<85%)"
                
            performance_records.append({
                "Budget Category": category,
                "Planned Cap (EGP)": planned_cap,
                "Actual Spent (EGP)": actual_spent,
                "Remaining Available (EGP)": remaining,
                "Budget Consumed %": round(pct_used, 1),
                "Status": status,
                "Alert Color Level": color_group
            })
            
        perf_df = pd.DataFrame(performance_records)

        # 🚨 UPGRADE 1: AUTOMATED INSTANT BREACH BANNER GRID
        if breached_categories:
            st.error("### 🚨 Absolute Budget Ceiling Breach Alerts!")
            for alert in breached_categories:
                st.markdown(alert)
        if warning_categories:
            st.warning("### ⚡ Budget Warning Zone Notifications (Above 85%)")
            for warn in warning_categories:
                st.markdown(warn)
        if not breached_categories and not warning_categories:
            st.success("### ✅ Perfect Pacing! All variable categories are safely inside their planned limits.")

        st.markdown("---")
        
        # 📊 UPGRADE 2: UNIFIED 100% CEILING PERFORMANCE BAR CHART
        st.subheader("📊 Category Cap Consumed Progress Map")
        st.markdown("Every bar shows your total usage percentage. If any bar crosses the red dotted line at **100%**, it is over budget.")
        
        fig_clean_bars = px.bar(
            perf_df,
            x="Budget Consumed %",
            y="Budget Category",
            color="Alert Color Level",
            orientation="h",
            text="Budget Consumed %",
            color_discrete_map={
                "Wiped Out (>100%)": "#e74c3c",       # Direct Crimson Red
                "Danger Zone (85%-100%)": "#f39c12",  # Amber Alert Yellow
                "Safe Under Target (<85%)": "#2ecc71" # Safe Green
            },
            category_orders={"Budget Category": list(PLANNED_BUDGETS.keys())}
        )
        
        # Add visual benchmark guideline representing 100% absolute ceiling
        fig_clean_bars.add_vline(x=100.0, line_width=3, line_dash="dash", line_color="#c0392b", annotation_text="BUDGET CEILING LINE (100%)", annotation_position="top right")
        fig_clean_bars.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_clean_bars.update_layout(xaxis=dict(range=[0, max(120, perf_df['Budget Consumed %'].max() + 15)]), height=500)
        st.plotly_chart(fig_clean_bars, use_container_width=True, key="unified_performance_bar_chart")

        st.markdown("---")
        
        # Performance Data Grid logs
        st.subheader("📋 Structural Financial Performance Ledger")
        st.dataframe(perf_df[["Budget Category", "Planned Cap (EGP)", "Actual Spent (EGP)", "Remaining Available (EGP)", "Budget Consumed %", "Status"]], use_container_width=True)

        st.markdown("---")
        
        # Daily Run-rate pacing trend line plot
        st.subheader("📉 Daily Cash Outflow Burn-Rate Velocity")
        month_exp['Day'] = month_exp['Date'].dt.day
        daily_timeline = pd.DataFrame({'Day': range(1, 31)})
        daily_sums = month_exp.groupby('Day')['Amount'].sum().reset_index()
        daily_timeline = pd.merge(daily_timeline, daily_sums, on='Day', how='left').fillna(0.0)
        daily_timeline['Actual Cumulative Spend'] = daily_timeline['Amount'].cumsum()
        daily_timeline['Target Ceiling Slope'] = (TOTAL_MONTHLY_PLANNED_EXPENSE / 30.0) * daily_timeline['Day']
        
        fig_pacing = go.Figure()
        fig_pacing.add_trace(go.Scatter(x=daily_timeline['Day'], y=daily_timeline['Target Ceiling Slope'], name="Ideal Month Slope Target (Yellow)", line=dict(color='#f1c40f', width=2, dash='dash')))
        fig_pacing.add_trace(go.Scatter(x=daily_timeline['Day'], y=daily_timeline['Actual Cumulative Spend'], name="Real Cumulative Spending (Blue)", line=dict(color='#3498db', width=4)))
        fig_pacing.update_layout(xaxis_title="Day of Month Timeline", yaxis_title="Total EGP Outflow Pool")
        st.plotly_chart(fig_pacing, use_container_width=True, key="daily_burnrate_pacing_trend")
