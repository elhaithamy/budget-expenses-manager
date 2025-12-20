import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# ====== PAGE CONFIG ======
st.set_page_config(
    page_title="Sort My Money - Budget 2026",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====== GOOGLE SHEETS INTEGRATION ======
@st.cache_data(ttl=300)
def load_from_google_sheets(sheet_url):
    """Load planned data from Google Sheets"""
    try:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        
        # Try to load the first sheet
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        df = pd.read_csv(csv_url)
        
        return df
    except Exception as e:
        st.error(f"❌ Error loading sheet: {str(e)}")
        st.info("💡 Make sure your Google Sheet is set to 'Anyone with the link can view'")
        return None

def save_to_google_sheets(sheet_url, data_dict):
    """
    Prepare data for manual export to Google Sheets
    Since we can't write directly without OAuth, we'll provide a downloadable CSV
    """
    try:
        # Convert month_state to a flat DataFrame for export
        export_data = []
        
        for month_idx, month_data in enumerate(data_dict['month_state']):
            month_name = data_dict['months'][month_idx]
            
            # Income
            export_data.append({
                'Month': month_name,
                'Category': 'Income',
                'Subcategory': 'Salary',
                'Planned': month_data['income']['salary_planned'],
                'Actual': month_data['income']['salary_actual'],
                'Notes': month_data['income']['notes']
            })
            export_data.append({
                'Month': month_name,
                'Category': 'Income',
                'Subcategory': 'Bonus',
                'Planned': month_data['income']['bonus_planned'],
                'Actual': month_data['income']['bonus_actual'],
                'Notes': ''
            })
            
            # Fixed expenses
            for key in ['housing', 'insurance', 'education', 'transport', 'comm']:
                export_data.append({
                    'Month': month_name,
                    'Category': 'Fixed Expense',
                    'Subcategory': key.title(),
                    'Planned': month_data['fixed'][f'{key}_p'],
                    'Actual': month_data['fixed'][f'{key}_a'],
                    'Notes': month_data['fixed']['notes'] if key == 'housing' else ''
                })
            
            # Variable expenses
            for key in ['food', 'util', 'ent', 'seasonal']:
                export_data.append({
                    'Month': month_name,
                    'Category': 'Variable Expense',
                    'Subcategory': key.title(),
                    'Planned': month_data['variable'][f'{key}_p'],
                    'Actual': month_data['variable'][f'{key}_a'],
                    'Notes': month_data['variable']['notes'] if key == 'food' else ''
                })
            
            # Investments
            for key in ['emergency', 'stock', 're', 'edu', 'ret']:
                export_data.append({
                    'Month': month_name,
                    'Category': 'Investment',
                    'Subcategory': key.title(),
                    'Planned': month_data['investments'][f'{key}_p'],
                    'Actual': month_data['investments'][f'{key}_a'],
                    'Notes': month_data['investments']['notes'] if key == 'emergency' else ''
                })
            
            # Metals
            export_data.append({
                'Month': month_name,
                'Category': 'Investment',
                'Subcategory': 'Metals (grams)',
                'Planned': month_data['investments']['metal_grams_p'],
                'Actual': month_data['investments']['metal_grams_a'],
                'Notes': ''
            })
        
        df_export = pd.DataFrame(export_data)
        return df_export
        
    except Exception as e:
        st.error(f"Error preparing export: {str(e)}")
        return None

# ====== HELPER FUNCTIONS ======
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
            'metal_grams_p': 0.0, 'metal_grams_a': 0.0,  # Float for proper number_input handling
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

if 'sheet_url' not in st.session_state:
    st.session_state.sheet_url = ''

if 'auto_save' not in st.session_state:
    st.session_state.auto_save = True

# ====== CONSTANTS ======
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']

# ====== SIDEBAR ======
st.sidebar.title("💰 Sort My Money")
st.sidebar.caption("Budget Dashboard 2026")

# Today's date
today = datetime.now()
st.sidebar.success(f"📅 **Today:** {today.strftime('%d %b %Y')}")
st.sidebar.info(f"📆 **Week {(today.day - 1) // 7 + 1}** of {MONTHS[today.month - 1]}")

st.sidebar.divider()

# Month selector
active_month = st.sidebar.selectbox(
    "📊 Select Active Month",
    range(12),
    format_func=lambda x: MONTHS[x],
    index=today.month - 1,
    key='active_month_selector'
)

st.sidebar.divider()

# Google Sheets Integration
with st.sidebar.expander("☁️ Google Sheets Sync", expanded=False):
    st.write("**Load defaults from your planning sheet**")
    
    sheet_url_input = st.text_input(
        "Google Sheets URL",
        value=st.session_state.sheet_url,
        placeholder="https://docs.google.com/spreadsheets/d/...",
        key='sheet_url_input_field'
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Load Plan", use_container_width=True):
            if sheet_url_input:
                st.session_state.sheet_url = sheet_url_input
                with st.spinner("Loading from Google Sheets..."):
                    df = load_from_google_sheets(sheet_url_input)
                    if df is not None:
                        st.success("✅ Loaded!")
                        st.dataframe(df.head(3), use_container_width=True)
                        # Here you could parse df and update month_state planned values
            else:
                st.warning("Enter URL first")
    
    with col2:
        if st.button("💾 Export Data", use_container_width=True):
            export_df = save_to_google_sheets(
                st.session_state.sheet_url,
                {
                    'month_state': st.session_state.month_state,
                    'months': MONTHS
                }
            )
            if export_df is not None:
                csv = export_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"budget_actuals_{today.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    st.caption("💡 Set sheet to 'Anyone with link can view' for loading")
    st.caption("📝 Export creates a CSV you can paste into Sheets")

st.sidebar.divider()

# Fixed Settings
with st.sidebar.expander("⚙️ Fixed Settings", expanded=False):
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
    st.session_state.fixed_settings['emergency_target'] = st.number_input(
        "Emergency Fund Target",
        value=st.session_state.fixed_settings['emergency_target'],
        step=5000,
        key='fs_emergency_target'
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

st.sidebar.divider()

# Auto-save toggle
st.session_state.auto_save = st.sidebar.checkbox(
    "✨ Auto-save changes",
    value=st.session_state.auto_save,
    help="Changes are saved instantly to session (resets on page refresh)"
)

if st.sidebar.button("🔄 Reset All to Defaults", use_container_width=True):
    st.session_state.month_state = [initialize_month_data() for _ in range(12)]
    st.success("✅ Reset complete!")
    st.rerun()

st.sidebar.divider()
st.sidebar.caption("💡 Changes auto-save in your browser session")
st.sidebar.caption("📤 Use 'Export Data' to save permanently")

# ====== MAIN TABS ======
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📥 Edit Month",
    "📆 Daily Track",
    "📈 Portfolio",
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
            label="💰 Income",
            value=f"{income_actual:,.0f} EGP",
            delta=f"{income_actual - income_planned:+,.0f}"
        )
    
    with col2:
        st.metric(
            label="💸 Expenses",
            value=f"{total_expense_actual:,.0f} EGP",
            delta=f"{total_expense_actual - (fixed_planned + var_planned):+,.0f}",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="📈 Invested",
            value=f"{inv_actual:,.0f} EGP",
            delta=f"{inv_actual - inv_planned:+,.0f}"
        )
    
    with col4:
        target_savings = fs['base_salary'] * fs['target_savings_pct'] / 100
        savings_rate = (inv_actual / fs['base_salary']) * 100 if fs['base_salary'] > 0 else 0
        delta_vs_target = savings_rate - fs['target_savings_pct']
        st.metric(
            label=f"🎯 Savings ({fs['target_savings_pct']}% target)",
            value=f"{savings_rate:.1f}%",
            delta=f"{delta_vs_target:+.1f}%"
        )
    
    st.divider()
    
    # Summary Tables
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Income")
        income_df = pd.DataFrame({
            'Item': ['Salary', 'Bonus', 'TOTAL'],
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
        st.subheader("💸 Expenses")
        expense_df = pd.DataFrame({
            'Category': ['Fixed Bills', 'Variable', 'TOTAL'],
            'Planned': [fixed_planned, var_planned, fixed_planned + var_planned],
            'Actual': [fixed_actual, var_actual, total_expense_actual]
        })
        expense_df['Variance'] = expense_df['Actual'] - expense_df['Planned']
        st.dataframe(expense_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Detailed breakdown
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🏠 Fixed Bills")
        fixed_detail = pd.DataFrame({
            'Item': ['Housing', 'Insurance', 'Education', 'Transport', 'Comm'],
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
        fixed_detail['Δ'] = fixed_detail['Actual'] - fixed_detail['Planned']
        st.dataframe(fixed_detail, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🍽️ Variable")
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
        var_detail['Δ'] = var_detail['Actual'] - var_detail['Planned']
        st.dataframe(var_detail, use_container_width=True, hide_index=True)
    
    with col3:
        st.subheader("📈 Investments")
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
        inv_detail['Δ'] = inv_detail['Actual'] - inv_detail['Planned']
        st.dataframe(inv_detail, use_container_width=True, hide_index=True)
    
    # Metals widget
    if m['investments']['metal_grams_a'] > 0 or fs['gold_price_per_gram'] > 0:
        st.info(f"🥇 **Metals:** {m['investments']['metal_grams_a']:.1f} grams × {fs['gold_price_per_gram']:.2f} EGP/g = **{metal_value_actual:,.2f} EGP**")

# ====== TAB 2: EDIT MONTH ======
with tab2:
    st.header(f"📥 Edit {MONTHS[active_month]} Values")
    st.caption("✨ Changes auto-save when enabled in sidebar")
    
    m = st.session_state.month_state[active_month]
    
    # Income
    with st.expander("💰 Income", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Planned")
            m['income']['salary_planned'] = st.number_input(
                "Salary",
                value=m['income']['salary_planned'],
                step=500,
                key=f'inc_sal_p_{active_month}'
            )
            m['income']['bonus_planned'] = st.number_input(
                "Bonus",
                value=m['income']['bonus_planned'],
                step=500,
                key=f'inc_bon_p_{active_month}'
            )
        with col2:
            st.subheader("Actual")
            m['income']['salary_actual'] = st.number_input(
                "Salary",
                value=m['income']['salary_actual'],
                step=500,
                key=f'inc_sal_a_{active_month}',
                label_visibility="collapsed"
            )
            m['income']['bonus_actual'] = st.number_input(
                "Bonus",
                value=m['income']['bonus_actual'],
                step=500,
                key=f'inc_bon_a_{active_month}',
                label_visibility="collapsed"
            )
        m['income']['notes'] = st.text_area(
            "Notes",
            value=m['income']['notes'],
            key=f'inc_notes_{active_month}',
            height=60
        )
    
    # Fixed Bills
    with st.expander("💳 Fixed Bills"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Planned")
            m['fixed']['housing_p'] = st.number_input("Housing", value=m['fixed']['housing_p'], key=f'fix_hou_p_{active_month}')
            m['fixed']['insurance_p'] = st.number_input("Insurance", value=m['fixed']['insurance_p'], key=f'fix_ins_p_{active_month}')
            m['fixed']['education_p'] = st.number_input("Education", value=m['fixed']['education_p'], key=f'fix_edu_p_{active_month}')
            m['fixed']['transport_p'] = st.number_input("Transport", value=m['fixed']['transport_p'], key=f'fix_tra_p_{active_month}')
            m['fixed']['comm_p'] = st.number_input("Communication", value=m['fixed']['comm_p'], key=f'fix_com_p_{active_month}')
        with col2:
            st.subheader("Actual")
            m['fixed']['housing_a'] = st.number_input("Housing", value=m['fixed']['housing_a'], key=f'fix_hou_a_{active_month}', label_visibility="collapsed")
            m['fixed']['insurance_a'] = st.number_input("Insurance", value=m['fixed']['insurance_a'], key=f'fix_ins_a_{active_month}', label_visibility="collapsed")
            m['fixed']['education_a'] = st.number_input("Education", value=m['fixed']['education_a'], key=f'fix_edu_a_{active_month}', label_visibility="collapsed")
            m['fixed']['transport_a'] = st.number_input("Transport", value=m['fixed']['transport_a'], key=f'fix_tra_a_{active_month}', label_visibility="collapsed")
            m['fixed']['comm_a'] = st.number_input("Communication", value=m['fixed']['comm_a'], key=f'fix_com_a_{active_month}', label_visibility="collapsed")
        m['fixed']['notes'] = st.text_area("Notes", value=m['fixed']['notes'], key=f'fix_notes_{active_month}', height=60)
    
    # Variable Spending
    with st.expander("🍽️ Variable Spending"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Planned")
            m['variable']['food_p'] = st.number_input("Food & Groceries", value=m['variable']['food_p'], key=f'var_foo_p_{active_month}')
            m['variable']['util_p'] = st.number_input("Utilities", value=m['variable']['util_p'], key=f'var_uti_p_{active_month}')
            m['variable']['ent_p'] = st.number_input("Entertainment", value=m['variable']['ent_p'], key=f'var_ent_p_{active_month}')
            m['variable']['seasonal_p'] = st.number_input("Seasonal/Misc", value=m['variable']['seasonal_p'], key=f'var_sea_p_{active_month}')
        with col2:
            st.subheader("Actual")
            m['variable']['food_a'] = st.number_input("Food & Groceries", value=m['variable']['food_a'], key=f'var_foo_a_{active_month}', label_visibility="collapsed")
            m['variable']['util_a'] = st.number_input("Utilities", value=m['variable']['util_a'], key=f'var_uti_a_{active_month}', label_visibility="collapsed")
            m['variable']['ent_a'] = st.number_input("Entertainment", value=m['variable']['ent_a'], key=f'var_ent_a_{active_month}', label_visibility="collapsed")
            m['variable']['seasonal_a'] = st.number_input("Seasonal/Misc", value=m['variable']['seasonal_a'], key=f'var_sea_a_{active_month}', label_visibility="collapsed")
        m['variable']['notes'] = st.text_area("Notes", value=m['variable']['notes'], key=f'var_notes_{active_month}', height=60)
    
    # Investments
    with st.expander("📈 Investments & Savings"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Planned")
            m['investments']['emergency_p'] = st.number_input("Emergency Fund", value=m['investments']['emergency_p'], key=f'inv_eme_p_{active_month}')
            m['investments']['stock_p'] = st.number_input("Stock Market", value=m['investments']['stock_p'], key=f'inv_sto_p_{active_month}')
            m['investments']['re_p'] = st.number_input("Real Estate", value=m['investments']['re_p'], key=f'inv_re_p_{active_month}')
            m['investments']['edu_p'] = st.number_input("Education Fund", value=m['investments']['edu_p'], key=f'inv_edu_p_{active_month}')
            m['investments']['ret_p'] = st.number_input("Retirement", value=m['investments']['ret_p'], key=f'inv_ret_p_{active_month}')
        with col2:
            st.subheader("Actual")
            m['investments']['emergency_a'] = st.number_input("Emergency Fund", value=m['investments']['emergency_a'], key=f'inv_eme_a_{active_month}', label_visibility="collapsed")
            m['investments']['stock_a'] = st.number_input("Stock Market", value=m['investments']['stock_a'], key=f'inv_sto_a_{active_month}', label_visibility="collapsed")
            m['investments']['re_a'] = st.number_input("Real Estate", value=m['investments']['re_a'], key=f'inv_re_a_{active_month}', label_visibility="collapsed")
            m['investments']['edu_a'] = st.number_input("Education Fund", value=m['investments']['edu_a'], key=f'inv_edu_a_{active_month}', label_visibility="collapsed")
            m['investments']['ret_a'] = st.number_input("Retirement", value=m['investments']['ret_a'], key=f'inv_ret_a_{active_month}', label_visibility="collapsed")
        
        st.divider()
        st.subheader("🥇 Gold/Silver (Physical)")
        col1, col2 = st.columns(2)
        with col1:
            m['investments']['metal_grams_p'] = st.number_input(
                "Grams - Planned",
                value=float(m['investments']['metal_grams_p']),
                key=f'inv_met_p_{active_month}',
                step=1.0,
                format="%.1f"
            )
        with col2:
            m['investments']['metal_grams_a'] = st.number_input(
                "Grams - Actual",
                value=float(m['investments']['metal_grams_a']),
                key=f'inv_met_a_{active_month}',
                step=1.0,
                format="%.1f"
            )
        
        if fs['gold_price_per_gram'] > 0:
            value = m['investments']['metal_grams_a'] * fs['gold_price_per_gram']
            st.success(f"💰 Value: **{value:,.2f} EGP** ({m['investments']['metal_grams_a']:.1f} g × {fs['gold_price_per_gram']:.2f} EGP/g)")
        
        m['investments']['notes'] = st.text_area("Notes", value=m['investments']['notes'], key=f'inv_notes_{active_month}', height=60)
    
    st.success("✅ All changes are auto-saved to your browser session")
    st.info("💡 Use 'Export Data' in sidebar to download your actuals as CSV")

# ====== TAB 3: DAILY TRACKING ======
with tab3:
    st.header(f"📆 Daily Tracking - {MONTHS[active_month]}")
    st.info("🚧 **Coming Soon!** Track daily expenses and see weekly insights.")
    
    st.write("This tab will include:")
    st.write("- Daily food, transport, entertainment inputs")
    st.write("- Weekly aggregation and variance analysis")
    st.write("- Spending pace alerts (e.g., 'Used 70% of budget by Week 2')")

# ====== TAB 4: PORTFOLIO ======
with tab4:
    st.header("📈 Investment Portfolio Overview")
    
    fs = st.session_state.fixed_settings
    
    # Calculate totals
    portfolio_totals = {
        'Emergency': 0,
        'Stocks': 0,
        'Real Estate': 0,
        'Education': 0,
        'Retirement': 0,
        'Metals': 0
    }
    
    for month_data in st.session_state.month_state:
        portfolio_totals['Emergency'] += month_data['investments']['emergency_a']
        portfolio_totals['Stocks'] += month_data['investments']['stock_a']
        portfolio_totals['Real Estate'] += month_data['investments']['re_a']
        portfolio_totals['Education'] += month_data['investments']['edu_a']
        portfolio_totals['Retirement'] += month_data['investments']['ret_a']
        portfolio_totals['Metals'] += month_data['investments']['metal_grams_a'] * fs['gold_price_per_gram']
    
    total_invested = sum(portfolio_totals.values())
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Pie chart
        df_portfolio = pd.DataFrame({
            'Category': list(portfolio_totals.keys()),
            'Amount': list(portfolio_totals.values())
        })
        df_portfolio = df_portfolio[df_portfolio['Amount'] > 0]  # Only show non-zero
        
        if not df_portfolio.empty:
            fig_pie = px.pie(
                df_portfolio,
                values='Amount',
                names='Category',
                title='Portfolio Allocation (2026 Contributions)',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No investments recorded yet")
    
    with col2:
        st.subheader("Annual Contributions")
        for key, value in portfolio_totals.items():
            if value > 0:
                pct = (value / total_invested * 100) if total_invested > 0 else 0
                st.metric(label=key, value=f"{value:,.0f} EGP", delta=f"{pct:.1f}%")
        
        st.divider()
        st.metric("💰 Total Invested", f"{total_invested:,.0f} EGP")

# ====== TAB 5: CHARTS ======
with tab5:
    st.header("📉 Financial Visualizations")
    
    # Prepare monthly data
    months_data = []
    for i in range(12):
        m = st.session_state.month_state[i]
        fs = st.session_state.fixed_settings
        
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
            'Net': income - expenses - investments
        })
    
    df_months = pd.DataFrame(months_data)
    
    # Chart 1: Income vs Expenses
    st.subheader("💰 Income vs Expenses")
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=df_months['Month'], y=df_months['Income'], name='Income', marker_color='#4CAF50'))
    fig1.add_trace(go.Bar(x=df_months['Month'], y=df_months['Expenses'], name='Expenses', marker_color='#FF6B6B'))
    fig1.update_layout(barmode='group', height=400)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.divider()
    
    # Chart 2: Cumulative Investments
    st.subheader("📈 Cumulative Investments")
    df_months['Cumulative'] = df_months['Investments'].cumsum()
    fig2 = px.line(df_months, x='Month', y='Cumulative', markers=True)
    fig2.update_traces(line_color='#667eea', line_width=3)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    # Chart 3: Monthly Net (surplus/deficit)
    st.subheader("💵 Monthly Net Balance")
    colors = ['#4CAF50' if x >= 0 else '#FF6B6B' for x in df_months['Net']]
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_months['Month'],
        y=df_months['Net'],
        marker_color=colors,
        text=df_months['Net'].apply(lambda x: f"{x:+,.0f}"),
        textposition='outside'
    ))
    fig3.add_hline(y=0, line_dash="dash", line_color="gray")
    fig3.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

# ====== FOOTER ======
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("💰 Sort My Money - Budget Dashboard 2026")
with col2:
    st.caption("Built with Streamlit | Free & Open Source")
with col3:
    st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
