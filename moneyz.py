import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. LIVE PAGE SETTINGS
st.set_page_config(page_title="EGP Wealth Hub", layout="wide")
st.title("🏆 Financial Command Center (EGP)")
st.markdown("---")

# 2. ESTABLISH SECURE DATA CONNECTION
# Paste your fresh Google Sheet URL here:
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1dwZFbG_ibYGO7msBOl2cFnnX4_A-KJ5tkaKJ5XI2Tj8/edit#gid=0"

# Import Streamlit's secure sheet connector
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5) # Cache refreshes every 5 seconds for fast live updates
def load_ledger_data():
    # Reads the clean, single flat table format seamlessly
    data = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Ledger")
    data['Date'] = pd.to_datetime(data['Date'])
    data['Amount'] = pd.to_numeric(data['Amount'], errors='coerce').fillna(0.0)
    data['Month'] = data['Date'].dt.to_period('M').astype(str)
    return data

try:
    df = load_ledger_data()
except:
    st.error("Please connect your Google Sheet correctly or check column naming conversions.")
    st.stop()

# 3. SPLIT APPLICATION INTO TWO CLEAN FUNCTIONAL TABS
tab_input, tab_visuals = st.tabs(["📥 Tab 1: Live Data Entry Form", "📊 Tab 2: Visual Charts & Analytics"])

# =========================================================
# TAB 1: DATA ENTRY FORMS (BLUE & GREEN DESIGN FOCUS)
# =========================================================
with tab_input:
    st.markdown("<h3 style='color: #3498db;'>📝 Append New Row Straight to Google Sheets</h3>", unsafe_allow_html=True)
    st.markdown("Fill out the transaction below. Submitting will instantly write this record into your online spreadsheet database.")
    
    # Single unified layout form
    with st.form("database_form", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            entry_date = st.date_input("Transaction Calendar Date", datetime.now().date())
            entry_type = st.selectbox("Flow Classification (Type)", ["Expense", "Income"])
            
        with col_f2:
            entry_amount = st.number_input("Numerical Amount (EGP)", min_value=0.0, step=100.0)
            entry_desc = st.text_input("Context / Vendor Description", placeholder="e.g., Cairo Rent Payment")
            
        with col_f3:
            # Combined available categories dropdown picker
            entry_cat = st.selectbox("Budget Assignment Category", [
                'Food', 'Allowance', 'Medication/Health', 'Mother', 'Gas', 
                'BabySitter', 'Nurse', 'Physical Therapy', 'Rent', 'Rent 2', 
                'Credit Card', 'Paycheck', 'Savings', 'Other'
            ])
            entry_liquid = st.checkbox("Is Cash Liquid / Accessible?", value=True)
            
        # Form submission trigger button
        save_trigger = st.form_submit_button("🔒 Securely Save Row to Google Sheet")
        
        if save_trigger:
            if entry_amount > 0:
                # Structure the input to match your exact sheet columns
                new_row_df = pd.DataFrame([{
                    "Date": entry_date.strftime("%Y-%m-%d"),
                    "Amount": entry_amount,
                    "Description": entry_desc,
                    "Category": entry_cat,
                    "Type": entry_type,
                    "Is_Liquid": entry_liquid
                }])
                
                # Append to current dataset matrix and save back online
                updated_master = pd.concat([df.drop(columns=['Month'], errors='ignore'), new_row_df], ignore_index=True)
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="Ledger", data=updated_master)
                
                st.balloons()
                st.success("Success! Record successfully written into Google Sheets. Click Tab 2 to view updated charts.", icon="✅")
                st.cache_data.clear() # Clear memory to force data reload
            else:
                st.warning("Please specify an amount higher than 0 EGP to file a ledger entry.")

    st.markdown("---")
    st.markdown("**Current Live Database Spreadsheet Log view:**")
    st.dataframe(df[["Date", "Type", "Category", "Amount", "Description", "Is_Liquid"]], use_container_width=True)

# =========================================================
# TAB 2: VISUAL CHARTS (RED & YELLOW SPENT FOCUS)
# =========================================================
with tab_visuals:
    # RUN CALCULATIONS PIPELINE FOR MULTI-MONTH ROLLOVERS
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

    # Sidebar Filter Module for Visuals View panel
    st.sidebar.markdown("---")
    selected_month = st.sidebar.selectbox("Filter Chart Month View", unique_months, index=len(unique_months)-1 if unique_months else 0)
    
    if not history_df.empty and selected_month in monthly_aggregates:
        metrics = monthly_aggregates[selected_month]
        
        # Numeric Scorecards KPIs row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🎬 Start Pool Balance", f"{metrics['Start']:,.2f} EGP")
        m2.metric("📥 Liquid Inflow (Green/Blue)", f"{metrics['Income']:,.2f} EGP")
        m3.metric("📤 Total Expenses (Red)", f"{metrics['Expenses']:,.2f} EGP")
        m4.metric("🏁 Net Rolling Cash Pool", f"{metrics['End']:,.2f} EGP")
        
        st.markdown("---")
        
        # Interactive Visual Dashboard Panel Row
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.markdown("**Income vs Expenses Baseline (Bar Chart - Green/Red Scheme)**")
            bar_melt = history_df.melt(id_vars=["Month"], value_vars=["Total Income", "Total Expenses"], var_name="Type", value_name="EGP")
            fig_bar = px.bar(bar_melt, x="Month", y="EGP", color="Type", barmode="group",
                             color_discrete_map={"Total Income": "#2ecc71", "Total Expenses": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c_right:
            st.markdown("**Long-Term Cumulative Savings Track (Lean Line Chart - Blue Scheme)**")
            fig_line = px.line(history_df, x="Month", y="Accumulated Cash Savings", markers=True, color_discrete_sequence=["#3498db"])
            fig_line.update_traces(line_width=4, marker_size=10)
            st.plotly_chart(fig_line, use_container_width=True)
            
        st.markdown("---")
        
        # Row 2: Expense Proportions Weight distribution map
        st.markdown(f"### 🔍 Spent Category Structural Breakdown for {selected_month}")
        exp_filter = df[(df['Month'] == selected_month) & (df['Type'] == 'Expense')]
        
        if not exp_filter.empty:
            # Custom assigned hot warning hex variations sequence matching requirements exactly
            spent_colors = ['#e74c3c', '#f1c40f', '#e67e22', '#f39c12', '#d35400', '#f5b041', '#f8c471']
            fig_pie = px.pie(exp_filter, values="Amount", names="Category", hole=0.4, color_discrete_sequence=spent_colors)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense entries logged yet for this selected calendar month branch.")
