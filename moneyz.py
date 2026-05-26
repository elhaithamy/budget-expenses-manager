import streamlit as st
import pandas as pd
import plotly.express as px

# 1. PAGE SETUP
st.set_page_config(page_title="EGP Cash Flow Hub", layout="wide")
st.title("🏆 Permanent Multi-Month Rolling Budget Hub (EGP)")
st.markdown("---")

# 2. AUTOMATED DIRECT GOOGLE SHEET CONNECTION 
SHEET_ID = "1dwZFbG_ibYGO7msBOl2cFnnX4_A-KJ5tkaKJ5XI2Tj8"
SHEET_NAME = "Transactions"
csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

def clean_numeric(val):
    if pd.isna(val): return 0.0
    val_cleaned = str(val).replace('£', '').replace('$', '').replace(',', '').strip()
    try: return float(val_cleaned)
    except: return 0.0

@st.cache_data(ttl=10) # Live-sync updates within 10 seconds of a sheet edit
def load_and_parse_sheet():
    raw_df = pd.read_csv(csv_url, header=1)
    
    # Extract Side-by-Side Expenses (Cols A-D)
    exp = raw_df.iloc[:, [0, 1, 2, 3]].dropna(subset=[raw_df.columns[1]])
    exp.columns = ['Date', 'Amount', 'Description', 'Category']
    exp['Amount'] = exp['Amount'].apply(clean_numeric)
    exp['Type'] = 'Expense'
    exp['Date'] = pd.to_datetime(exp['Date'], errors='coerce').fillna(pd.to_datetime('2026-06-25'))
    
    # Extract Side-by-Side Income (Cols F-I)
    inc = raw_df.iloc[:, [5, 6, 7, 8]].dropna(subset=[raw_df.columns[6]])
    inc.columns = ['Date', 'Amount', 'Description', 'Category']
    inc['Amount'] = inc['Amount'].apply(clean_numeric)
    inc['Type'] = 'Income'
    inc['Date'] = pd.to_datetime(inc['Date'], errors='coerce').fillna(pd.to_datetime('2026-06-25'))
    
    # Automatic asset sorting engine rules
    def check_liquidity(row):
        desc = str(row['Description']).lower()
        cat = str(row['Category']).lower()
        if 'side project' in desc or 'other' in cat or row['Amount'] in [150500.0, 78000.0]:
            return False
        return True
        
    inc['Is_Liquid'] = inc.apply(check_liquidity, axis=1)
    exp['Is_Liquid'] = True 
    
    combined = pd.concat([exp, inc], ignore_index=True)
    combined['Month'] = combined['Date'].dt.to_period('M').astype(str)
    return combined

df = load_and_parse_sheet()

# 3. MULTI-MONTH ROLLING CALCULATION ENGINE
unique_months = sorted(df['Month'].unique())
rolling_balance = 0.0
monthly_aggregates = {}
historical_trends = []

for m in unique_months:
    m_df = df[df['Month'] == m]
    
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

# 4. INTERFACE NAVIGATION PANEL
st.sidebar.header("Navigation Controls")
selected_month = st.sidebar.selectbox("Choose Target Budget Month", unique_months)
metrics = monthly_aggregates[selected_month]

# Financial KPI Metrics Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("🎬 Starting Cash Pool", f"{metrics['Start']:,.2f} EGP")
k2.metric("📥 Liquid Inflow", f"{metrics['Income']:,.2f} EGP")
k3.metric("📤 Total Expenses", f"{metrics['Expenses']:,.2f} EGP")
k4.metric("🏁 Net Rolling Savings Balance", f"{metrics['End']:,.2f} EGP")

st.markdown("---")

# 5. CHARTS AND VISUALIZATIONS SECTION
st.subheader("📊 Macro Performance Visualizations")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Monthly Cash Inflow vs Outflow Comparison (Bar Chart)**")
    bar_melt = history_df.melt(id_vars=["Month"], value_vars=["Total Income", "Total Expenses"], 
                               var_name="Flow Type", value_name="EGP Amount")
    fig_bar = px.bar(bar_melt, x="Month", y="EGP Amount", color="Flow Type", 
                     barmode="group", color_discrete_sequence=["#2ecc71", "#e74c3c"])
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.markdown("**Long-Term Compounding Cash Line (Lean Savings Chart)**")
    fig_line = px.line(history_df, x="Month", y="Accumulated Cash Savings", markers=True,
                       color_discrete_sequence=["#3498db"])
    fig_line.update_traces(line_width=4, marker_size=10)
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

st.subheader(f"🔍 Expense Allocation Deep Dive: {selected_month}")
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Expense Category Weight Distribution (Pie Chart)**")
    expense_data = df[(df['Month'] == selected_month) & (df['Type'] == 'Expense')]
    if not expense_data.empty:
        fig_pie = px.pie(expense_data, values="Amount", names="Category", 
                         hole=0.4, color_discrete_sequence=px.colors.sequential.YlOrRd_r)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense rows recorded for this month.")

with col_right:
    st.markdown("**Raw Transaction Grid Verification**")
    display_mix = df[df['Month'] == selected_month]
    st.dataframe(display_mix[["Date", "Category", "Amount", "Type", "Is_Liquid"]], use_container_width=True)
