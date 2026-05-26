import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="EGP Financial Command Center", layout="wide")
st.title("🏆 Live Interactive Financial Command Center (EGP)")
st.markdown("---")

# 2. INITIALIZE MASTER DATA FROM GOOGLE SHEET
SHEET_ID = "1dwZFbG_ibYGO7msBOl2cFnnX4_A-KJ5tkaKJ5XI2Tj8"
SHEET_NAME = "Transactions"
csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

def clean_numeric(val):
    if pd.isna(val): return 0.0
    val_cleaned = str(val).replace('£', '').replace('$', '').replace(',', '').strip()
    try: return float(val_cleaned)
    except: return 0.0

@st.cache_data(ttl=60)
def fetch_base_sheet_data():
    try:
        raw_df = pd.read_csv(csv_url, header=1)
        # Extract Side-by-Side Expenses (Cols A-D) [cite: 3]
        exp = raw_df.iloc[:, [0, 1, 2, 3]].dropna(subset=[raw_df.columns[1]])
        exp.columns = ['Date', 'Amount', 'Description', 'Category']
        exp['Amount'] = exp['Amount'].apply(clean_numeric)
        exp['Type'] = 'Expense'
        exp['Is_Liquid'] = True
        
        # Extract Side-by-Side Income (Cols F-I) [cite: 5]
        inc = raw_df.iloc[:, [5, 6, 7, 8]].dropna(subset=[raw_df.columns[6]])
        inc.columns = ['Date', 'Amount', 'Description', 'Category']
        inc['Amount'] = inc['Amount'].apply(clean_numeric)
        inc['Type'] = 'Income'
        
        def check_liquidity(row):
            desc = str(row['Description']).lower()
            cat = str(row['Category']).lower()
            if 'side project' in desc or 'other' in cat or row['Amount'] in [150500.0, 78000.0]: # [cite: 5]
                return False
            return True
        inc['Is_Liquid'] = inc.apply(check_liquidity, axis=1)
        
        combined = pd.concat([exp, inc], ignore_index=True)
        combined['Date'] = pd.to_datetime(combined['Date']).dt.date
        return combined
    except:
        # Emergency local initialization if Google Sheet connection limits are hit
        return pd.DataFrame(columns=['Date', 'Amount', 'Description', 'Category', 'Type', 'Is_Liquid'])

# Keep the data alive across page changes using Streamlit Session State
if 'main_dataset' not in st.session_state:
    st.session_state.main_dataset = fetch_base_sheet_data()

# 3. SIDE-BY-SIDE INTERACTIVE INPUT FORMS (MATCHING YOUR SPREADSHEET LAYOUT)
st.subheader("📥 Add Daily Transactions Live")
input_col_left, input_col_right = st.columns(2)

with input_col_left:
    st.markdown("<h4 style='color: #e74c3c;'>🔻 Record New Expense Row</h4>", unsafe_allow_html=True)
    with st.form("expense_form", clear_on_submit=True):
        exp_date = st.date_input("Expense Date", datetime.now().date(), key="exp_d")
        exp_amount = st.number_input("Amount (EGP)", min_value=0.0, step=100.0, key="exp_a")
        exp_desc = st.text_input("Description", placeholder="e.g., Carrefour Groceries", key="exp_de")
        exp_cat = st.selectbox("Category", ['Food', 'Allowance', 'Medication/Health', 'Mother', 'Gas', 'BabySitter', 'Nurse', 'Physical Therapy', 'Rent', 'Rent 2', 'Credit Card'], key="exp_c") # [cite: 3]
        
        submit_expense = st.form_submit_with_button_label("Add Expense Row")
        if submit_expense and exp_amount > 0:
            new_row = pd.DataFrame([{"Date": exp_date, "Amount": exp_amount, "Description": exp_desc, "Category": exp_cat, "Type": "Expense", "Is_Liquid": True}])
            st.session_state.main_dataset = pd.concat([st.session_state.main_dataset, new_row], ignore_index=True)
            st.toast("Expense added successfully!", icon="🔥")

with input_col_right:
    st.markdown("<h4 style='color: #2ecc71;'>🔺 Record New Income Row</h4>", unsafe_allow_html=True)
    with st.form("income_form", clear_on_submit=True):
        inc_date = st.date_input("Income Date", datetime.now().date(), key="inc_d")
        inc_amount = st.number_input("Amount (EGP)", min_value=0.0, step=500.0, key="inc_a")
        inc_desc = st.text_input("Description", placeholder="e.g., Monthly Base Paycheck", key="inc_de")
        inc_cat = st.selectbox("Category", ['Paycheck', 'Savings', 'Other'], key="inc_c") # [cite: 5]
        inc_liquid = st.checkbox("Is this cash immediately spendable (Liquid)?", value=True, key="inc_l")
        
        submit_income = st.form_submit_with_button_label("Add Income Row")
        if submit_income and inc_amount > 0:
            new_row = pd.DataFrame([{"Date": inc_date, "Amount": inc_amount, "Description": inc_desc, "Category": inc_cat, "Type": "Income", "Is_Liquid": inc_liquid}])
            st.session_state.main_dataset = pd.concat([st.session_state.main_dataset, new_row], ignore_index=True)
            st.toast("Income added successfully!", icon="💰")

st.markdown("---")

# 4. RUNNING ENGINE CALCULATIONS FOR MULTI-MONTH ROLLOVERS
working_df = st.session_state.main_dataset.copy()
working_df['Date'] = pd.to_datetime(working_df['Date'])
working_df['Month'] = working_df['Date'].dt.to_period('M').astype(str)

unique_months = sorted(working_df['Month'].unique())
rolling_balance = 0.0
monthly_aggregates = {}
historical_trends = []

for m in unique_months:
    m_df = working_df[working_df['Month'] == m]
    
    liquid_inflow = m_df[(m_df['Type'] == 'Income') & (m_df['Is_Liquid'] == True)]['Amount'].sum()
    total_outflow = m_df[m_df['Type'] == 'Expense']['Amount'].sum()
    locked_inflow = m_df[(m_df['Type'] == 'Income') & (m_df['Is_Liquid'] == False)]['Amount'].sum()
    
    start_bal = rolling_balance
    net_savings = liquid_inflow - total_outflow
    end_bal = start_bal + net_savings
    
    monthly_aggregates[m] = {
        "Start": start_bal, "Income": liquid_inflow,
        "Expenses": total_outflow, "End": end_bal, "Locked": locked_inflow
    }
    
    historical_trends.append({
        "Month": m, "Accumulated Cash Savings": end_bal, 
        "Total Income": liquid_inflow, "Total Expenses": total_outflow
    })
    rolling_balance = end_bal

history_df = pd.DataFrame(historical_trends)

# 5. DASHBOARD SUMMARY CARDS (BLUE & GREEN INPUTS/INFLOW THEME)
st.sidebar.header("Navigation Controls")
if unique_months:
    selected_month = st.sidebar.selectbox("Choose Target Budget Month", unique_months, index=len(unique_months)-1)
    metrics = monthly_aggregates[selected_month]
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🎬 Starting Cash Pool", f"{metrics['Start']:,.2f} EGP")
    k2.metric("📥 Liquid Inflow (Green/Blue)", f"{metrics['Income']:,.2f} EGP")
    k3.metric("📤 Total Expenses", f"{metrics['Expenses']:,.2f} EGP")
    k4.metric("🏁 Net Rolling Savings Balance", f"{metrics['End']:,.2f} EGP")
else:
    st.warning("Please add data rows to unlock dashboard functionalities.")
    st.stop()

st.markdown("---")

# 6. CHARTS PLOTTING ENGINE (RED & YELLOW SPENT VARIATIONS THEME)
st.subheader("📊 Performance Visualizations")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Monthly Cash Flow Baseline (Bar Chart)**")
    bar_melt = history_df.melt(id_vars=["Month"], value_vars=["Total Income", "Total Expenses"], 
                               var_name="Flow Type", value_name="EGP Amount")
    # Setting Income to Green, Expenses to Red
    fig_bar = px.bar(bar_melt, x="Month", y="EGP Amount", color="Flow Type", 
                     barmode="group", color_discrete_map={"Total Income": "#2ecc71", "Total Expenses": "#e74c3c"})
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.markdown("**Long-Term Compounding Cash Line (Lean Savings Curve - Blue Theme)**")
    fig_line = px.line(history_df, x="Month", y="Accumulated Cash Savings", markers=True,
                       color_discrete_sequence=["#3498db"])
    fig_line.update_traces(line_width=4, marker_size=10)
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

# Row 2: Expense Distribution (Red/Yellow Custom Sequence)
col_graph, col_grid = st.columns(2)

with col_graph:
    st.markdown("**Expense Category Weight Variations (Red & Yellow Pie Chart)**")
    expense_data = working_df[(working_df['Month'] == selected_month) & (working_df['Type'] == 'Expense')]
    if not expense_data.empty:
        # Custom explicitly mapped Hex codes for strict Red and Yellow spent variations
        red_yellow_palette = ['#e74c3c', '#f1c40f', '#e67e22', '#f39c12', '#d35400', '#f5b041', '#ec7063']
        fig_pie = px.pie(expense_data, values="Amount", names="Category", 
                         hole=0.4, color_discrete_sequence=red_yellow_palette)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense rows found for this block sequence.")

with col_grid:
    st.markdown("**Active Transaction Logs & Session Master Sync**")
    st.dataframe(working_df[["Date", "Category", "Amount", "Type", "Is_Liquid"]], use_container_width=True)
    
    # Backup trigger button to save data offline before browser cache clears
    csv_data = working_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Download Session Data as CSV",
        data=csv_data,
        file_name=f"budget_backup_{selected_month}.csv",
        mime="text/csv",
    )
    st.caption("⚠️ Note: Browser refreshes clear screen history. Download your CSV row outputs to paste back into your Google Sheet master file.")
