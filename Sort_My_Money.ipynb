import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ====== PAGE CONFIG ======
st.set_page_config(
    page_title="Family Budget Dashboard 2026",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====== HELPER FUNCTIONS ======
@st.cache_data(ttl=600)
def load_google_sheet(sheet_url):
    """Load data from Google Sheets public link"""
    try:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"Error loading sheet: {str(e)}")
        return None

def initialize_month_data():
    """Initialize default month data structure"""
    return {
        'income': {
            'salary_planned': 15000,
            'salary_actual': 15000,
            'bonus_planned': 0,
            'bonus_actual': 0,
            'notes': ''
        },
        'fixed': {
            'housing_p': 5250, 'housing_a': 5250,
            'insurance_p': 600, 'insurance_a': 600,
            'education_p': 1500, 'education_a': 1500,
            'transport_p': 2250, 'transport_a': 2250,
            'comm_p': 300, 'comm_a': 300,
            'notes': ''
        },
        'variable': {
            'food_p': 3000, 'food_a': 3000,
            'util_p': 1500, 'util_a': 1500,
            'ent_p': 450, 'ent_a': 450,
            'seasonal_p': 1000, 'seasonal_a': 1000,
            'notes': ''
        },
        'investments': {
            'emergency_p': 1200, 'emergency_a': 1200,
            'stock_p': 800, 'stock_a': 800,
            're_p': 500, 're_a': 500,
            'edu_p': 400, 'edu_a': 400,
            'ret_p': 600, 'ret_a': 600,
            'metal_grams_p': 0, 'metal_grams_a': 0,
            'notes': ''
        }
    }

# ====== INITIALIZE SESSION STATE ======
if 'month_state' not in st.session_state:
    st.session_state.month_state = [initialize_month_data() for _ in range(12)]

if 'fixed_settings' not in st.session_state:
    st.session_state.fixed_settings = {
        'base_salary': 15000,
        'target_savings_pct': 40,
        'emergency_target': 90000,
        'portfolio_target': 160000,
        'gold_price_per_gram': 85.0,
        'silver_price_per_gram': 1.0
    }

# ====== CONSTANTS ======
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']

# ====== SIDEBAR ======
st.sidebar.title("💰 Budget Dashboard 2026")

# Today's date
today = datetime.now()
st.sidebar.info(f"📅 **Today:** {today.strftime('%d %b %Y')}")
st.sidebar.info(f"📆 **Week:** {(today.day - 1) // 7 + 1} of {MONTHS[today.month - 1]}")

# Month selector
active_month = st.sidebar.selectbox(
    "Select Active Month",
    range(12),
    format_func=lambda x: MONTHS[x],
    index=today.month - 1,
    key='active_month_selector'
)

st.sidebar.divider()

# Google Sheet loader
with st.sidebar.expander("📊 Load from Google Sheets"):
    sheet_url = st.text_input(
        "Paste Google Sheets URL",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        key='sheet_url_input'
    )
    if st.button("Load Data", key='load_sheet_btn'):
        if sheet_url:
            with st.spinner("Loading..."):
                df = load_google_sheet(sheet_url)
                if df is not None:
                    st.success("✅ Sheet loaded!")
                    st.dataframe(df.head(5), use_container_width=True)
        else:
            st.warning("Please enter a URL")

st.sidebar.divider()

# Fixed Settings
with st.sidebar.expander("⚙️ Fixed Settings"):
    st.session_state.fixed_settings['base_salary'] = st.number_input(
        "Base Salary (EGP)",
        value=st.session_state.fixed_settings['base_salary'],
        step=500,
        key='fs_base_salary'
    )
    st.session_state.fixed_settings['target_savings_pct'] = st.number_input(
        "Savings Target %",
        value=st.session_state.fixed_settings['target_savings_pct'],
        step=5,
        key='fs_target_pct'
    )
    st.session_state.fixed_settings['gold_price_per_gram'] = st.number_input(
        "Gold Price/Gram (EGP)",
        value=st.session_state.fixed_settings['gold_price_per_gram'],
        step=1.0,
        format="%.2f",
        key='fs_gold_price'
    )
    st.session_state.fixed_settings['silver_price_per_gram'] = st.number_input(
        "Silver Price/Gram (EGP)",
        value=st.session_state.fixed_settings['silver_price_per_gram'],
        step=0.1,
        format="%.2f",
        key='fs_silver_price'
    )

# Reset button
if st.sidebar.button("🔄 Reset All to Defaults", key='reset_btn'):
    st.session_state.month_state = [initialize_month_data() for _ in range(12)]
    st.success("✅ Reset complete!")
    st.rerun()

# ====== MAIN TABS ======
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📥 Monthly Inputs",
    "📆 Daily Tracking",
    "📈 Investments",
    "📉 Charts"
])

# ====== TAB 1: DASHBOARD ======
with tab1:
    st.header(f"📊 {MONTHS[active_month]} Overview")
    
    m = st.session_state.month_state[active_month]
    fs = st.session_state.fixed_settings
    
    # Calculate totals
    income_planned = m['income']['salary_planned'] + m['income']['bonus_planned']
    income_actual = m['income']['salary_actual'] + m['income']['bonus_actual']
    
    fixed_planned = sum([v for k, v in m['fixed'].items() if k.endswith('_p')])
    fixed_actual = sum([v for k, v in m['fixed'].items() if k.endswith('_a')])
    
    var_planned = sum([v for k, v in m['variable'].items() if k.endswith('_p')])
    var_actual = sum([v for k, v in m['variable'].items() if k.endswith('_a')])
    
    inv_planned = sum([v for k, v in m['investments'].items() if k.endswith('_p') and k != 'metal_grams_p'])
    inv_actual = sum([v for k, v in m['investments'].items() if k.endswith('_a') and k != 'metal_grams_a'])
    
    metal_value_actual = m['investments']['metal_grams_a'] * fs['gold_price_per_gram']
    inv_actual += metal_value_actual
    
    total_expense_actual = fixed_actual + var_actual
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Monthly Income",
            value=f"{income_actual:,.0f} EGP",
            delta=f"{income_actual - income_planned:+,.0f}"
        )
    
    with col2:
        st.metric(
            label="💸 Total Expenses",
            value=f"{total_expense_actual:,.0f} EGP",
            delta=f"{total_expense_actual - (fixed_planned + var_planned):+,.0f}"
        )
    
    with col3:
        st.metric(
            label="📈 Investments",
            value=f"{inv_actual:,.0f} EGP",
            delta=f"{inv_actual - inv_planned:+,.0f}"
        )
    
    with col4:
        target_savings = fs['base_salary'] * fs['target_savings_pct'] / 100
        savings_rate = (inv_actual / fs['base_salary']) * 100 if fs['base_salary'] > 0 else 0
        delta_vs_target = savings_rate - fs['target_savings_pct']
        st.metric(
            label="🎯 Savings Rate",
            value=f"{savings_rate:.1f}%",
            delta=f"{delta_vs_target:+.1f}% vs target"
        )
    
    st.divider()
    
    # Summary Tables
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Income Breakdown")
        income_df = pd.DataFrame({
            'Category': ['Base Salary', 'Bonus', 'TOTAL'],
            'Planned': [
                m['income']['salary_planned'],
                m['income']['bonus_planned'],
                income_planned
            ],
            'Actual': [
                m['income']['salary_actual'],
                m['income']['bonus_actual'],
                income_actual
            ]
        })
        income_df['Variance'] = income_df['Actual'] - income_df['Planned']
        st.dataframe(income_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("💸 Expense Breakdown")
        expense_df = pd.DataFrame({
            'Category': ['Fixed Bills', 'Variable Spending', 'TOTAL'],
            'Planned': [fixed_planned, var_planned, fixed_planned + var_planned],
            'Actual': [fixed_actual, var_actual, total_expense_actual]
        })
        expense_df['Variance'] = expense_df['Actual'] - expense_df['Planned']
        st.dataframe(expense_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Detailed breakdown
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🏠 Fixed Bills Detail")
        fixed_detail = pd.DataFrame({
            'Item': ['Housing', 'Insurance', 'Education', 'Transport', 'Communication'],
            'Planned': [
                m['fixed']['housing_p'],
                m['fixed']['insurance_p'],
                m['fixed']['education_p'],
                m['fixed']['transport_p'],
                m['fixed']['comm_p']
            ],
            'Actual': [
                m['fixed']['housing_a'],
                m['fixed']['insurance_a'],
                m['fixed']['education_a'],
                m['fixed']['transport_a'],
                m['fixed']['comm_a']
            ]
        })
        fixed_detail['Var'] = fixed_detail['Actual'] - fixed_detail['Planned']
        st.dataframe(fixed_detail, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🍽️ Variable Spending Detail")
        var_detail = pd.DataFrame({
            'Item': ['Food', 'Utilities', 'Entertainment', 'Seasonal'],
            'Planned': [
                m['variable']['food_p'],
                m['variable']['util_p'],
                m['variable']['ent_p'],
                m['variable']['seasonal_p']
            ],
            'Actual': [
                m['variable']['food_a'],
                m['variable']['util_a'],
                m['variable']['ent_a'],
                m['variable']['seasonal_a']
            ]
        })
        var_detail['Var'] = var_detail['Actual'] - var_detail['Planned']
        st.dataframe(var_detail, use_container_width=True, hide_index=True)
    
    with col3:
        st.subheader("📈 Investments Detail")
        inv_detail = pd.DataFrame({
            'Item': ['Emergency', 'Stocks', 'Real Estate', 'Education', 'Retirement'],
            'Planned': [
                m['investments']['emergency_p'],
                m['investments']['stock_p'],
                m['investments']['re_p'],
                m['investments']['edu_p'],
                m['investments']['ret_p']
            ],
            'Actual': [
                m['investments']['emergency_a'],
                m['investments']['stock_a'],
                m['investments']['re_a'],
                m['investments']['edu_a'],
                m['investments']['ret_a']
            ]
        })
        inv_detail['Var'] = inv_detail['Actual'] - inv_detail['Planned']
        st.dataframe(inv_detail, use_container_width=True, hide_index=True)

# ====== TAB 2: MONTHLY INPUTS ======
with tab2:
    st.header(f"📥 Edit {MONTHS[active_month]} Values")
    
    m = st.session_state.month_state[active_month]
    
    # Income Section
    with st.expander("💰 Income", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            m['income']['salary_planned'] = st.number_input(
                "Salary - Planned",
                value=m['income']['salary_planned'],
                step=500,
                key=f'income_sal_p_{active_month}'
            )
            m['income']['bonus_planned'] = st.number_input(
                "Bonus - Planned",
                value=m['income']['bonus_planned'],
                step=500,
                key=f'income_bon_p_{active_month}'
            )
        with col2:
            m['income']['salary_actual'] = st.number_input(
                "Salary - Actual",
                value=m['income']['salary_actual'],
                step=500,
                key=f'income_sal_a_{active_month}'
            )
            m['income']['bonus_actual'] = st.number_input(
                "Bonus - Actual",
                value=m['income']['bonus_actual'],
                step=500,
                key=f'income_bon_a_{active_month}'
            )
        m['income']['notes'] = st.text_area(
            "Income Notes",
            value=m['income']['notes'],
            key=f'income_notes_{active_month}'
        )
    
    # Fixed Bills Section
    with st.expander("💳 Fixed Bills"):
        col1, col2 = st.columns(2)
        with col1:
            m['fixed']['housing_p'] = st.number_input("Housing - Planned", value=m['fixed']['housing_p'], key=f'fix_hou_p_{active_month}')
            m['fixed']['insurance_p'] = st.number_input("Insurance - Planned", value=m['fixed']['insurance_p'], key=f'fix_ins_p_{active_month}')
            m['fixed']['education_p'] = st.number_input("Education - Planned", value=m['fixed']['education_p'], key=f'fix_edu_p_{active_month}')
            m['fixed']['transport_p'] = st.number_input("Transport - Planned", value=m['fixed']['transport_p'], key=f'fix_tra_p_{active_month}')
            m['fixed']['comm_p'] = st.number_input("Communication - Planned", value=m['fixed']['comm_p'], key=f'fix_com_p_{active_month}')
        with col2:
            m['fixed']['housing_a'] = st.number_input("Housing - Actual", value=m['fixed']['housing_a'], key=f'fix_hou_a_{active_month}')
            m['fixed']['insurance_a'] = st.number_input("Insurance - Actual", value=m['fixed']['insurance_a'], key=f'fix_ins_a_{active_month}')
            m['fixed']['education_a'] = st.number_input("Education - Actual", value=m['fixed']['education_a'], key=f'fix_edu_a_{active_month}')
            m['fixed']['transport_a'] = st.number_input("Transport - Actual", value=m['fixed']['transport_a'], key=f'fix_tra_a_{active_month}')
            m['fixed']['comm_a'] = st.number_input("Communication - Actual", value=m['fixed']['comm_a'], key=f'fix_com_a_{active_month}')
        m['fixed']['notes'] = st.text_area("Fixed Bills Notes", value=m['fixed']['notes'], key=f'fix_notes_{active_month}')
    
    # Variable Spending
    with st.expander("🍽️ Variable Spending"):
        col1, col2 = st.columns(2)
        with col1:
            m['variable']['food_p'] = st.number_input("Food - Planned", value=m['variable']['food_p'], key=f'var_foo_p_{active_month}')
            m['variable']['util_p'] = st.number_input("Utilities - Planned", value=m['variable']['util_p'], key=f'var_uti_p_{active_month}')
            m['variable']['ent_p'] = st.number_input("Entertainment - Planned", value=m['variable']['ent_p'], key=f'var_ent_p_{active_month}')
            m['variable']['seasonal_p'] = st.number_input("Seasonal - Planned", value=m['variable']['seasonal_p'], key=f'var_sea_p_{active_month}')
        with col2:
            m['variable']['food_a'] = st.number_input("Food - Actual", value=m['variable']['food_a'], key=f'var_foo_a_{active_month}')
            m['variable']['util_a'] = st.number_input("Utilities - Actual", value=m['variable']['util_a'], key=f'var_uti_a_{active_month}')
            m['variable']['ent_a'] = st.number_input("Entertainment - Actual", value=m['variable']['ent_a'], key=f'var_ent_a_{active_month}')
            m['variable']['seasonal_a'] = st.number_input("Seasonal - Actual", value=m['variable']['seasonal_a'], key=f'var_sea_a_{active_month}')
        m['variable']['notes'] = st.text_area("Variable Notes", value=m['variable']['notes'], key=f'var_notes_{active_month}')
    
    # Investments
    with st.expander("📈 Investments & Savings"):
        col1, col2 = st.columns(2)
        with col1:
            m['investments']['emergency_p'] = st.number_input("Emergency Fund - Planned", value=m['investments']['emergency_p'], key=f'inv_eme_p_{active_month}')
            m['investments']['stock_p'] = st.number_input("Stocks - Planned", value=m['investments']['stock_p'], key=f'inv_sto_p_{active_month}')
            m['investments']['re_p'] = st.number_input("Real Estate - Planned", value=m['investments']['re_p'], key=f'inv_re_p_{active_month}')
            m['investments']['edu_p'] = st.number_input("Education Fund - Planned", value=m['investments']['edu_p'], key=f'inv_edu_p_{active_month}')
            m['investments']['ret_p'] = st.number_input("Retirement - Planned", value=m['investments']['ret_p'], key=f'inv_ret_p_{active_month}')
        with col2:
            m['investments']['emergency_a'] = st.number_input("Emergency Fund - Actual", value=m['investments']['emergency_a'], key=f'inv_eme_a_{active_month}')
            m['investments']['stock_a'] = st.number_input("Stocks - Actual", value=m['investments']['stock_a'], key=f'inv_sto_a_{active_month}')
            m['investments']['re_a'] = st.number_input("Real Estate - Actual", value=m['investments']['re_a'], key=f'inv_re_a_{active_month}')
            m['investments']['edu_a'] = st.number_input("Education Fund - Actual", value=m['investments']['edu_a'], key=f'inv_edu_a_{active_month}')
            m['investments']['ret_a'] = st.number_input("Retirement - Actual", value=m['investments']['ret_a'], key=f'inv_ret_a_{active_month}')
        
        st.divider()
        st.subheader("🥇 Gold/Silver Investment")
        col1, col2 = st.columns(2)
        with col1:
            m['investments']['metal_grams_p'] = st.number_input("Grams - Planned", value=m['investments']['metal_grams_p'], key=f'inv_met_p_{active_month}', step=1.0)
        with col2:
            m['investments']['metal_grams_a'] = st.number_input("Grams - Actual", value=m['investments']['metal_grams_a'], key=f'inv_met_a_{active_month}', step=1.0)
        
        if fs['gold_price_per_gram'] > 0:
            value = m['investments']['metal_grams_a'] * fs['gold_price_per_gram']
            st.info(f"💰 Current metals value: **{value:,.2f} EGP** ({m['investments']['metal_grams_a']} grams × {fs['gold_price_per_gram']:.2f} EGP/gram)")
        
        m['investments']['notes'] = st.text_area("Investment Notes", value=m['investments']['notes'], key=f'inv_notes_{active_month}')
    
    if st.button("✅ Save All Changes", type="primary", key='save_inputs_btn'):
        st.success(f"✅ {MONTHS[active_month]} data saved!")
        st.rerun()

# ====== TAB 3: DAILY TRACKING ======
with tab3:
    st.header(f"📆 Daily Tracking - {MONTHS[active_month]}")
    st.info("🚧 **Coming soon!** Daily expense tracking with weekly summaries and insights.")
    st.write("This feature will let you:")
    st.write("- Track daily food, transport, and other expenses")
    st.write("- See weekly aggregates and compare to budget")
    st.write("- Get alerts if spending pace is too high")

# ====== TAB 4: INVESTMENTS ======
with tab4:
    st.header("📈 Investment Portfolio Overview")
    
    # Calculate annual totals
    total_portfolio = {
        'Emergency': 0,
        'Stocks': 0,
        'Real Estate': 0,
        'Education': 0,
        'Retirement': 0,
        'Metals': 0
    }
    
    for month_data in st.session_state.month_state:
        total_portfolio['Emergency'] += month_data['investments']['emergency_a']
        total_portfolio['Stocks'] += month_data['investments']['stock_a']
        total_portfolio['Real Estate'] += month_data['investments']['re_a']
        total_portfolio['Education'] += month_data['investments']['edu_a']
        total_portfolio['Retirement'] += month_data['investments']['ret_a']
        total_portfolio['Metals'] += month_data['investments']['metal_grams_a'] * fs['gold_price_per_gram']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Portfolio distribution pie chart
        df_portfolio = pd.DataFrame({
            'Type': list(total_portfolio.keys()),
            'Amount': list(total_portfolio.values())
        })
        fig_pie = px.pie(
            df_portfolio,
            values='Amount',
            names='Type',
            title='Portfolio Distribution (Annual Contributions)',
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Annual Totals")
        for key, value in total_portfolio.items():
            st.metric(label=key, value=f"{value:,.0f} EGP")

# ====== TAB 5: CHARTS ======
with tab5:
    st.header("📉 Financial Visualizations")
    
    # Prepare data for all 12 months
    months_data = []
    for i in range(12):
        m = st.session_state.month_state[i]
        income = m['income']['salary_actual'] + m['income']['bonus_actual']
        expenses = (sum([v for k, v in m['fixed'].items() if k.endswith('_a')]) +
                   sum([v for k, v in m['variable'].items() if k.endswith('_a')]))
        investments = sum([v for k, v in m['investments'].items() if k.endswith('_a') and k != 'metal_grams_a'])
        investments += m['investments']['metal_grams_a'] * fs['gold_price_per_gram']
        
        months_data.append({
            'Month': MONTHS[i],
            'Income': income,
            'Expenses': expenses,
            'Investments': investments,
            'Balance': income - expenses - investments
        })
    
    df_months = pd.DataFrame(months_data)
    
    # Chart 1: Income vs Expenses
    st.subheader("💰 Income vs Expenses by Month")
    fig_income_exp = go.Figure()
    fig_income_exp.add_trace(go.Bar(
        x=df_months['Month'],
        y=df_months['Income'],
        name='Income',
        marker_color='#4CAF50'
    ))
    fig_income_exp.add_trace(go.Bar(
        x=df_months['Month'],
        y=df_months['Expenses'],
        name='Expenses',
        marker_color='#FF6B6B'
    ))
    fig_income_exp.update_layout(barmode='group', height=400)
    st.plotly_chart(fig_income_exp, use_container_width=True)
    
    st.divider()
    
    # Chart 2: Cumulative Investments
    st.subheader("📈 Cumulative Investment Growth")
    df_months['Cumulative_Investments'] = df_months['Investments'].cumsum()
    fig_cumulative = px.line(
        df_months,
        x='Month',
        y='Cumulative_Investments',
        markers=True,
        title='Investment Accumulation Over 2026'
    )
    fig_cumulative.update_traces(line_color='#667eea', line_width=3)
    st.plotly_chart(fig_cumulative, use_container_width=True)
    
    st.divider()
    
    # Chart 3: Monthly Balance
    st.subheader("💵 Monthly Balance (Income - Expenses - Investments)")
    fig_balance = go.Figure()
    colors = ['#4CAF50' if x >= 0 else '#FF6B6B' for x in df_months['Balance']]
    fig_balance.add_trace(go.Bar(
        x=df_months['Month'],
        y=df_months['Balance'],
        marker_color=colors,
        text=df_months['Balance'].apply(lambda x: f"{x:+,.0f}"),
        textposition='outside'
    ))
    fig_balance.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_balance.update_layout(
        title='Surplus (+) or Deficit (-) Each Month',
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig_balance, use_container_width=True)

# ====== FOOTER ======
st.divider()
st.caption("💰 Family Budget Dashboard 2026 | Built with Streamlit | Free & Open Source")
