import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# 1. LIVE PAGE SETTINGS
st.set_page_config(page_title="EGP Wealth Hub", layout="wide")
st.title("🏆 Financial Command Center (EGP)")
st.markdown("---")

# 2. ESTABLISH SECURE DATA CONNECTIONS
SHEET_ID = "1dwZFbG_ibYGO7msBOl2cFnnX4_A-KJ5tkaKJ5XI2Tj8"
csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Transactions"

# PASTE YOUR GOOGLE APPS SCRIPT WEB APP URL BETWEEN THE QUOTES BELOW:
WEBAPP_URL = "REPLACE_WITH_YOUR_COPIED_APPS_SCRIPT_URL"

def clean_numeric(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    val_cleaned = str(val).replace('£', '').replace('$', '').replace(',', '').strip()
    try: return float(val_cleaned)
    except: return 0.0

@st.cache_data(ttl=1)
def load_side_by_side_data():
    raw_df = pd.read_csv(csv_url, header=None)
    
    # Process Expenses (Columns A-D, from row 3 onwards)
    exp_raw = raw_df.iloc[2:, [0, 1, 2, 3]].copy()
    exp_raw.columns = ['Date', 'Amount', 'Description', 'Category']
    exp_raw['Amount'] = exp_raw['Amount'].apply(clean_numeric)
    exp_raw = exp_raw[exp_raw['Amount'] > 0]
    exp_raw['Type'] = 'Expense'
    exp_raw['Is_Liquid'] = True
    exp_raw['Date'] = pd.to_datetime(exp_raw['Date'], errors='coerce')
    
    # Process Income (Columns F-I / Indices 5-8, from row 3 onwards)
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
    st.error(f"❌ True Connection Error Details: {e}")
    st.stop()

# 3. APP NAVIGATION SYSTEM
tab_input, tab_visuals = st.tabs(["📥 Tab 1: Live Data Entry", "📊 Tab 2: Visual Analytics"])

# =========================================================
# TAB 1: DATA ENTRY FORMS
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
            entry_desc = st.text_input("Description Context", placeholder="e.g., Grocery Outlay")
        with col_f3:
            entry_cat = st.selectbox("Category Grouping", [
                'Food', 'Allowance', 'Medication/Health', 'Mother', 'Gas', 
                'BabySitter', 'Nurse', 'Physical Therapy', 'Rent', 'Rent 2', 
                'Credit Card', 'Paycheck', 'Savings', 'Other'
            ])
            
        save_trigger = st.form_submit_button("🔒 Save Entry to Google Sheet")
        
        if save_trigger and entry_amount > 0:
            # Package form variables into a clean JSON transmission packet
            payload = {
                "date": entry_date.strftime("%m/%d/%Y"),
                "amount": entry_amount,
                "description": entry_desc,
                "category": entry_cat,
                "type": entry_type
            }
            
            try:
                # Fire data package straight to the Google Gateway Script
                response = requests.post(WEBAPP_URL, json=payload)
                if response.status_code == 200:
                    st.balloons()
                    st.success("Successfully saved to your Google Spreadsheet layout!")
                    st.cache_data.clear() # Wipe memory cache to force an instant graph update
                else:
                    st.error(f"Gateway rejected transaction. Status: {response.status_code}")
            except Exception as api_err:
                st.error(f"Failed to communicate with Google Sheets. Verify Web App URL: {api_err}")

    st.markdown("---")
    st.markdown("### 📋 Previewing Your Live Side-by-Side Database")
    st.dataframe(raw_spreadsheet.fillna(""), use_container_width=True)

# =========================================================
# TAB 2: VISUAL ANALYTICS
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
        
        monthly_aggregates[m] = {
            "Start": start_bal, "Income": liquid_inflow, "Expenses": total_outflow, "End": end_bal
        }
        historical_trends.append({
            "Month": m, "Accumulated Cash Savings": end_bal, "Total Income": liquid_inflow, "Total Expenses": total_outflow
        })
        rolling_balance = end_bal

    history_df = pd.DataFrame(historical_trends)

    st.sidebar.markdown("---")
    if unique_months:
        selected_month = st.sidebar.selectbox("Filter Chart Month View", unique_months, index=len(unique_months)-1)
        metrics = monthly_aggregates[selected_month]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🎬 Start Pool Balance", f"{metrics['Start']:,.2f} EGP")
        m2.metric("📥 Liquid Inflow (Green/Blue)", f"{metrics['Income']:,.2f} EGP")
        m3.metric("📤 Total Expenses (Red)", f"{metrics['Expenses']:,.2f} EGP")
        m4.metric("🏁 Net Rolling Cash Pool", f"{metrics['End']:,.2f} EGP")
        
        st.markdown("---")
        
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("**Income vs Expenses Baseline (Bar Chart)**")
            bar_melt = history_df.melt(id_vars=["Month"], value_vars=["Total Income", "Total Expenses"], var_name="Type", value_name="EGP")
            fig_bar = px.bar(bar_melt, x="Month", y="EGP", color="Type", barmode="group",
                             color_discrete_map={"Total Income": "#2ecc71", "Total Expenses": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c_right:
            st.markdown("**Long-Term Cumulative Savings Track (Lean Line Chart)**")
            fig_line = px.line(history_df, x="Month", y="Accumulated Cash Savings", markers=True, color_discrete_sequence=["#3498db"])
            fig_line.update_traces(line_width=4, marker_size=10)
            st.plotly_chart(fig_line, use_container_width=True)
            
        st.markdown("---")
        
        st.markdown(f"### 🔍 Spent Category Structural Breakdown for {selected_month}")
        exp_filter = df[(df['Month'] == selected_month) & (df['Type'] == 'Expense')]
        
        if not exp_filter.empty:
            spent_colors = ['#e74c3c', '#f1c40f', '#e67e22', '#f39c12', '#d35400', '#f5b041', '#f8c471']
            fig_pie = px.pie(exp_filter, values="Amount", names="Category", hole=0.4, color_discrete_sequence=spent_colors)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense entries logged for this selected month.")
