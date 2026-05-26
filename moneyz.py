import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. LIVE PAGE SETTINGS
st.set_page_config(page_title="EGP Wealth Hub", layout="wide")
st.title("🏆 Financial Command Center (EGP)")
st.markdown("---")

# 2. ESTABLISH SECURE DATA CONNECTION
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1dwZFbG_ibYGO7msBOl2cFnnX4_A-KJ5tkaKJ5XI2Tj8/edit"

from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)

def clean_numeric(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    val_cleaned = str(val).replace('£', '').replace('$', '').replace(',', '').strip()
    try: return float(val_cleaned)
    except: return 0.0

@st.cache_data(ttl=5)
def load_side_by_side_data():
    # Read raw sheet without a header to parse indices manually
    raw_df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Transactions", header=None)
    
    # Process Expenses (Rows 3+ because Row 1 is Title and Row 2 is Subheaders)
    exp_raw = raw_df.iloc[2:, [0, 1, 2, 3]].dropna(subset=[raw_df.columns[1]])
    exp_raw.columns = ['Date', 'Amount', 'Description', 'Category']
    exp_raw['Amount'] = exp_raw['Amount'].apply(clean_numeric)
    exp_raw['Type'] = 'Expense'
    exp_raw['Is_Liquid'] = True
    exp_raw['Date'] = pd.to_datetime(exp_raw['Date'], errors='coerce')
    
    # Process Income (Rows 3+ / Columns F-I are positional indices 5, 6, 7, 8)
    inc_raw = raw_df.iloc[2:, [5, 6, 7, 8]].dropna(subset=[raw_df.columns[6]])
    inc_raw.columns = ['Date', 'Amount', 'Description', 'Category']
    inc_raw['Amount'] = inc_raw['Amount'].apply(clean_numeric)
    inc_raw['Type'] = 'Income'
    
    # Built-in automatic sorting rules to protect illiquid assets
    def check_liquidity(row):
        desc = str(row['Description']).lower()
        cat = str(row['Category']).lower()
        if 'side project' in desc or 'other' in cat or row['Amount'] in [150500.0, 78000.0]:
            return False
        return True
    inc_raw['Is_Liquid'] = inc_raw.apply(check_liquidity, axis=1)
    inc_raw['Date'] = pd.to_datetime(inc_raw['Date'], errors='coerce')
    
    # Merge for backend calculations
    combined = pd.concat([exp_raw, inc_raw], ignore_index=True).dropna(subset=['Date'])
    combined['Month'] = combined['Date'].dt.to_period('M').astype(str)
    return combined, raw_df

try:
    df, raw_spreadsheet = load_side_by_side_data()
except Exception as e:
    st.error("Connection sync mismatch. Verify that your columns match the 'Transactions' format precisely.")
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
            # Create a working copy of the master spreadsheet to manipulate cell blocks
            updated_sheet = raw_spreadsheet.copy()
            
            if entry_type == "Expense":
                # Scan column B (index 1) starting at row index 2 to find the next empty slot
                next_exp_idx = 2
                while next_exp_idx < len(updated_sheet) and pd.notna(updated_sheet.iloc[next_exp_idx, 1]) and str(updated_sheet.iloc[next_exp_idx, 1]).strip() != "":
                    next_exp_idx += 1
                
                # Append blank padding row if existing matrix boundary is reached
                if next_exp_idx == len(updated_sheet):
                    updated_sheet.loc[len(updated_sheet)] = [None] * len(updated_sheet.columns)
                    
                updated_sheet.iloc[next_exp_idx, 0] = entry_date.strftime("%m/%d/%Y")
                updated_sheet.iloc[next_exp_idx, 1] = entry_amount
                updated_sheet.iloc[next_exp_idx, 2] = entry_desc
                updated_sheet.iloc[next_exp_idx, 3] = entry_cat
                
            else: # Income Type Processing
                # Scan column G (index 6) starting at row index 2 to find the next empty slot
                next_inc_idx = 2
                while next_inc_idx < len(updated_sheet) and pd.notna(updated_sheet.iloc[next_inc_idx, 6]) and str(updated_sheet.iloc[next_inc_idx, 6]).strip() != "":
                    next_inc_idx += 1
                    
                if next_inc_idx == len(updated_sheet):
                    updated_sheet.loc[len(updated_sheet)] = [None] * len(updated_sheet.columns)
                    
                updated_sheet.iloc[next_inc_idx, 5] = entry_date.strftime("%m/%d/%Y")
                updated_sheet.iloc[next_inc_idx, 6] = entry_amount
                updated_sheet.iloc[next_inc_idx, 7] = entry_desc
                updated_sheet.iloc[next_inc_idx, 8] = entry_cat

            # Push the updated side-by-side array back to Google Sheets
            conn.update(spreadsheet=SPREADSHEET_URL, worksheet="Transactions", data=updated_sheet, header=False)
            st.balloons()
            st.success("Successfully compiled and saved to your spreadsheet layout! Head to Tab 2 to review changes.")
            st.cache_data.clear()

    st.markdown("---")
    st.markdown("### 📋 Previewing Your Live Side-by-Side Database")
    st.dataframe(raw_spreadsheet.fillna(""), use_container_width=True)

# =========================================================
# TAB 2: VISUAL ANALYTICS (RED & YELLOW SPENT THEME)
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
    selected_month = st.sidebar.selectbox("Filter Chart Month View", unique_months, index=len(unique_months)-1 if unique_months else 0)
    
    if not history_df.empty and selected_month in monthly_aggregates:
        metrics = monthly_aggregates[selected_month]
        
        # Financial Cards Display row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🎬 Start Pool Balance", f"{metrics['Start']:,.2f} EGP")
        m2.metric("📥 Liquid Inflow (Green/Blue)", f"{metrics['Income']:,.2f} EGP")
        m3.metric("📤 Total Expenses (Red)", f"{metrics['Expenses']:,.2f} EGP")
        m4.metric("🏁 Net Rolling Cash Pool", f"{metrics['End']:,.2f} EGP")
        
        st.markdown("---")
        
        # Financial Graph Rows
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.markdown("**Income vs Expenses Baseline (Bar Chart - Green/Red Map)**")
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
        
        # Category Expense Pie Chart Section
        st.markdown(f"### 🔍 Spent Category Structural Breakdown for {selected_month}")
        exp_filter = df[(df['Month'] == selected_month) & (df['Type'] == 'Expense')]
        
        if not exp_filter.empty:
            # Custom sequential sequence composed of exact Red and Yellow hot warning color variations
            spent_colors = ['#e74c3c', '#f1c40f', '#e67e22', '#f39c12', '#d35400', '#f5b041', '#f8c471']
            fig_pie = px.pie(exp_filter, values="Amount", names="Category", hole=0.4, color_discrete_sequence=spent_colors)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense entries logged for this selected month branch.")
