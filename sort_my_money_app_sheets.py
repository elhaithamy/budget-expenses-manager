import os
from datetime import datetime, date, timedelta
import streamlit as st
import pandas as pd

# Google Sheets
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Sort My Money - Budget 2026 (Google Sheets)",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']

DEFAULT_CATEGORIES_EXPENSE = [
    "housing", "insurance", "education", "transport", "comm",
    "food", "utilities", "entertainment", "seasonal", "misc"
]
DEFAULT_CATEGORIES_INCOME = ["salary", "freelance", "bonus", "other"]

# =========================
# HELPERS
# =========================
def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Monday

def month_name(d: date) -> str:
    return MONTHS[d.month - 1]

def get_sheet_id(url_or_id: str) -> str:
    s = (url_or_id or "").strip()
    if "/d/" in s:
        return s.split("/d/")[1].split("/")[0]
    return s  # assume already an id

# =========================
# GOOGLE SHEETS AUTH
# =========================
def get_gspread_client() -> gspread.Client:
    """
    Streamlit Cloud: put your service account JSON in st.secrets["gcp_service_account"]
    Docs: https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
    """
    if "gcp_service_account" not in st.secrets:
        st.error("Missing Streamlit secret: gcp_service_account")
        st.stop()

    sa_info = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    return gspread.authorize(creds)

# =========================
# SHEET SCHEMA
# =========================
CORE_TABS = {
    "transactions": ["tx_date", "week_start", "month", "tx_type", "category", "amount_egp", "notes"],
    "stock_values": ["as_of", "week_start", "month", "portfolio_value_egp", "notes"],
    "assets_snapshot": ["as_of", "asset", "quantity", "unit", "value_egp", "notes"],
    "settings": ["k", "v"],
    # Plan tabs (raw import from Excel)
    "plan_income_expenses": [],
    "plan_investments_savings": [],
    "plan_bottom_line": [],
    "plan_notes_assumptions": [],
}

DEFAULT_ASSETS = [
    # You can edit these later in the UI
    {"as_of": "2025-12-26", "asset": "Cash (EGP)", "quantity": 1, "unit": "EGP", "value_egp": 167200, "notes": ""},
    {"as_of": "2025-12-26", "asset": "Business", "quantity": 1, "unit": "EGP", "value_egp": 306791, "notes": ""},
    {"as_of": "2025-12-26", "asset": "Gold 24K (Sabika)", "quantity": 50, "unit": "gram", "value_egp": "", "notes": "Value manually"},
    {"as_of": "2025-12-26", "asset": "SAR Cash", "quantity": 2500, "unit": "SAR", "value_egp": "", "notes": "Value manually"},
    {"as_of": "2025-12-26", "asset": "Stocks (Total)", "quantity": 1, "unit": "EGP", "value_egp": "", "notes": "Update weekly/monthly"},
]

# =========================
# SHEET IO
# =========================
def open_spreadsheet(sheet_id: str):
    gc = get_gspread_client()
    return gc.open_by_key(sheet_id)

def ensure_worksheet(ss, title: str, header: list[str] | None):
    try:
        ws = ss.worksheet(title)
    except Exception:
        ws = ss.add_worksheet(title=title, rows=2000, cols=30)

    if header:
        # Ensure header row
        first_row = ws.row_values(1)
        if first_row != header:
            ws.clear()
            ws.update("A1", [header])
    return ws

def df_from_ws(ws, header=True) -> pd.DataFrame:
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    if header:
        cols = values[0]
        rows = values[1:]
        return pd.DataFrame(rows, columns=cols)
    else:
        return pd.DataFrame(values)

def append_row(ws, row: dict, header: list[str]):
    ordered = [row.get(h, "") for h in header]
    ws.append_row(ordered, value_input_option="USER_ENTERED")

# =========================
# INIT / POPULATE PLAN
# =========================
def populate_plan_tabs(ss):
    """
    Writes the Excel plan content into plan_* tabs.
    This uses embedded grids generated from your uploaded Budget Dashboard 2026.xlsx.
    """
    plan_grids = {"Income & Expenses": [["INCOME SECTION", "", "", "", "", ""], ["Item", "January 2026", "February 2026", "March 2026", "April 2026", "May 2026"], ["Previous Month Carryover (EGP)", "179,180", "", "", "", ""], ["Final January Salary (Old Job)", "45,000", "", "", "", ""], ["Initial Lump Sum (Feb 1) - Non-salary", "", "20,000", "", "", ""], ["Monthly Salary (Saudi - 20,000 SAR)", "", "254,000", "254,000", "254,000", "254,000"], ["Total Coming In", "224,180", "274,000", "254,000", "254,000", "254,000"], ["", "", "", "", "", ""], ["HOUSING & UTILITIES", "", "", "", "", ""], ["Item", "January 2026", "February 2026", "March 2026", "April 2026", "May 2026"], ["Home Expenses", "0", "2650", "2650", "2650", "2650"], ["Water Bill", "0", "100", "100", "100", "100"], ["Electricity Bill", "0", "100", "100", "100", "100"], ["Gas Bill", "0", "50", "50", "50", "50"], ["Iqama", "0", "0", "0", "0", "0"], ["Sub-Total", "0", "2900", "2900", "2900", "2900"], ["", "", "", "", "", ""], ["FAMILY SUPPORT", "", "", "", "", ""], ["Item", "January 2026", "February 2026", "March 2026", "April 2026", "May 2026"], ["Charity 400 SAR", "", "400", "400", "400", "400"], ["Mom Support 600 SAR", "", "600", "600", "600", "600"], ["Family Support Subtotal", "0", "1000", "1000", "1000", "1000"], ["", "", "", "", "", ""], ["PERSONAL EXPENSES", "", "", "", "", ""], ["Item", "January 2026", "February 2026", "March 2026", "April 2026", "May 2026"], ["Mobile Internet (100 SAR/month)", "100", "100", "100", "100", "100"], ["Food & Drink (750 SAR/month - from Mar)", "500", "750", "750", "750", "750"], ["Transportation - Uber/Careem (250 SAR)", "250", "250", "250", "250", "250"], ["Entertainment - Weekly Outings (240 SAR)", "250", "250", "250", "250", "250"], ["Personal Expenses Subtotal", "1100", "1350", "1350", "1350", "1350"], ["", "", "", "", "", ""], ["Start & SETUP", "", "", "", "", ""], ["Item", "January 2026", "February 2026", "March 2026", "April 2026", "May 2026"], ["Mobile Phone (1,000 SAR - Feb 1)", "0", "1000", "0", "0", "0"], ["Apartment Furnishing (phased)", "0", "10000", "15000", "15000", "15000"], ["Filipino Maid (900 SAR/month - from May)", "0", "0", "0", "0", "3000"], ["Start & Setup Subtotal", "0", "11000", "15000", "15000", "18000"], ["", "", "", "", "", ""], ["TOTAL SUMMARY", "", "", "", "", ""], ["Total Bills & Housing", "", "", "", "", ""], ["Total Spending (Excl. Investments)", "", "", "", "", ""], ["Total Outflow", "", "", "", "", ""]], "Investments & Savings": [["INVESTMENTS & SAVINGS SECTION", "", "", "", "", ""], ["Item", "January 2026", "February 2026", "March 2026", "April 2026", "May 2026"], ["", "", "", "", "", ""], ["EMERGENCY FUND (Expatriate Safety - 3 months coverage)", "", "", "", "", ""], ["Target Amount (120,000 SAR)", "", "", "", "", ""], ["Monthly Allocation", "30,000", "20,000", "0", "0", "0"], ["Running Balance", "30,000", "50,000", "50,000", "50,000", "50,000"], ["", "", "", "", "", ""], ["STOCKS & DIVIDEND INVESTMENTS", "", "", "", "", ""], ["Monthly Investment (10% of salary from Feb)", "0", "25,400", "25,400", "25,400", "25,400"], ["Running Total", "0", "25,400", "50,800", "76,200", "101,600"], ["", "", "", "", "", ""], ["NEW CAR - CAR INSTALLMENT", "", "", "", "", ""], ["Car Installment (1,000 SAR/month from May)", "0", "0", "0", "0", "1,000"], ["Running Total", "0", "0", "0", "0", "1,000"], ["", "", "", "", "", ""], ["GOLD/SILVER & PRECIOUS ASSETS", "", "", "", "", ""], ["Gold 50g (24k Bars) - Fixed Value", "340,000", "340,000", "340,000", "340,000", "340,000"], ["Foreign Currency Reserve (USD + SAR)", "85,000", "85,000", "85,000", "85,000", "85,000"], ["Total Precious Assets", "425,000", "425,000", "425,000", "425,000", "425,000"], ["", "", "", "", "", ""], ["CASH POSITION (IN EGP)", "", "", "", "", ""], ["Cash Carryover from Previous Month (EGP)", "179,180", "309,004", "459,608", "624,462", "797,216"], ["Monthly Cash Surplus", "221,004", "225,604", "200,854", "200,854", "199,954"], ["End of Month Cash Balance (EGP)", "309,004", "459,608", "624,462", "797,216", "971,170"]], "The Bottom Line": [["THE BOTTOM LINE SUMMARY", "", "", "", "", ""], ["", "", "", "", "", ""], ["Item", "January 2026", "February 2026", "March 2026", "April 2026", "May 2026"], ["", "", "", "", "", ""], ["INCOME", "", "", "", "", ""], ["Total Coming In (SAR)", "224,180", "274,000", "254,000", "254,000", "254,000"], ["", "", "", "", "", ""], ["OUTFLOWS", "", "", "", "", ""], ["Total Bills & Housing", "0", "33,655", "33,655", "33,655", "33,655"], ["Total Spending", "3,176", "48,396", "53,146", "53,146", "54,046"], ["Total Invested (Emergency + Stocks + Car)", "30,000", "45,400", "25,400", "25,400", "26,400"], ["", "", "", "", "", ""], ["MONTHLY RESULT", "", "", "", "", ""], ["Month Net Surplus (SAR)", "190,804", "146,804", "142,054", "142,054", "140,154"], ["Month Saved to Cash (EGP)", "221,004", "225,604", "200,854", "200,854", "199,954"], ["", "", "", "", "", ""], ["CUMULATIVE POSITION (EGP)", "", "", "", "", ""], ["Starting Cash (EGP)", "179,180", "309,004", "459,608", "624,462", "797,216"], ["Monthly Additions (EGP)", "128,820", "180,608", "200,854", "200,854", "199,954"], ["Ending Cash Balance (EGP)", "309,004", "459,608", "624,462", "797,216", "971,170"], ["", "", "", "", "", ""], ["PORTFOLIO SUMMARY (END OF MONTH)", "", "", "", "", ""], ["Cash on Hand (EGP)", "309,004", "459,608", "624,462", "797,216", "971,170"], ["Emergency Fund (SAR)", "30,000", "50,000", "50,000", "50,000", "50,000"], ["Stocks Investment (SAR)", "0", "25,400", "50,800", "76,200", "101,600"], ["Car Installments Paid (SAR)", "0", "0", "0", "0", "1,000"], ["Precious Assets (SAR)", "425,000", "425,000", "425,000", "425,000", "425,000"], ["TOTAL NET WORTH (Combined Assets)", "764,004", "959,008", "1,150,262", "1,348,416", "1,548,770"]], "Key Notes & Assumptions": [["KEY ASSUMPTIONS & NOTES", ""], ["", ""], ["EXCHANGE RATES USED", ""], ["SAR to EGP Conversion", "1 SAR = 12.7 EGP"], ["AED to SAR Conversion", "1 AED = 1.27 SAR"], ["", ""], ["COST CALCULATIONS", ""], ["Mobile Internet (Light User)", "75 SAR/month - Single SIM, non-heavy usage"], ["Food & Dining (1 Person)", "750 SAR/month - Basic meals, local restaurants"], ["Transportation (Uber/Careem)", "250 SAR/month - ~6-8 trips weekly in Khobar"], ["Entertainment & Outings", "240 SAR/month - Weekly social activities"], ["Filipino Maid Salary", "900 SAR/month - Moderate wage for Khobar, Eastern Province"], ["", ""], ["IMPORTANT NOTES", ""], ["Emergency Fund Target", "120,000 SAR (3-month coverage for 1 person + family obligations)"], ["Stock Investment Strategy", "10% of monthly salary from February onwards for dividend growth"], ["Car Purchase Timeline", "Begins May 2026 with 1,000 SAR monthly installment"], ["Apartment Setup", "Phased furnishing: 10k (Feb) + 15k (Mar-May) = 55,000 SAR total"], ["Family Arrival Prep", "By May: Strong cash position (971k EGP), secured housing, maid engaged"], ["Precious Assets", "Gold (50g 24k) + Foreign Currency maintained as inflation hedge & emergency reserve"], ["", ""], ["CASH POSITION NOTES", ""], ["Starting Cash", "179,180 EGP (December 2025 carryover)"], ["January Injection", "45,000 EGP (Final old job salary)"], ["February Injection", "20,000 EGP (Initial lump sum - non-recurring)"], ["Monthly Salary Base", "254,000 SAR = 3,225,800 SAR annually from Saudi job"], ["Ending Cash (May)", "971,170 EGP represents strong liquidity for family transition"], ["", ""], ["NEXT STEPS (June 2026 onwards)", ""], ["Monthly Sustainability", "Maintain 10% stocks + 1,000 SAR car installment from recurring income"], ["Family Expenses", "Estimated additional 2,650 SAR/month once family arrives (covered)"], ["Maid Continuity", "900 SAR/month ongoing from May through family transition"], ["Investment Growth", "Stocks portfolio expected to grow to 150k+ SAR by year-end 2026"]]}  # injected below

    mapping = {
        "Income & Expenses": "plan_income_expenses",
        "Investments & Savings": "plan_investments_savings",
        "The Bottom Line": "plan_bottom_line",
        "Key Notes & Assumptions": "plan_notes_assumptions",
    }

    for src_name, tab in mapping.items():
        ws = ensure_worksheet(ss, tab, header=None)
        grid = plan_grids.get(src_name, [])
        # Only overwrite if empty
        existing = ws.get_all_values()
        if existing and any(any(cell.strip() for cell in row) for row in existing):
            continue
        ws.clear()
        if grid:
            ws.update("A1", grid)

# =========================
# UI
# =========================
st.sidebar.title("💰 Sort My Money")
st.sidebar.caption("Budget 2026 • Google Sheets DB")

today = date.today()
st.sidebar.success(f"📅 Today: {today.strftime('%d %b %Y')}")
st.sidebar.info(f"📆 Week starts: {week_start(today).strftime('%d %b %Y')}")

sheet_input = st.sidebar.text_input(
    "Google Sheet link or ID",
    value=st.secrets.get("SHEET_ID", ""),
    placeholder="https://docs.google.com/spreadsheets/d/...."
)

sheet_id = get_sheet_id(sheet_input)

if not sheet_id:
    st.info("Enter your Google Sheet link/ID in the sidebar. For Streamlit Cloud, you can store it in Secrets as SHEET_ID.")
    st.stop()

# Open spreadsheet
try:
    ss = open_spreadsheet(sheet_id)
except Exception as e:
    st.error("Couldn't open the Google Sheet. Make sure you shared it with your service account email (Editor).")
    st.exception(e)
    st.stop()

# Ensure core tabs
ws_tx = ensure_worksheet(ss, "transactions", CORE_TABS["transactions"])
ws_stock = ensure_worksheet(ss, "stock_values", CORE_TABS["stock_values"])
ws_assets = ensure_worksheet(ss, "assets_snapshot", CORE_TABS["assets_snapshot"])
ws_settings = ensure_worksheet(ss, "settings", CORE_TABS["settings"])

# Plan tabs
ensure_worksheet(ss, "plan_income_expenses", header=None)
ensure_worksheet(ss, "plan_investments_savings", header=None)
ensure_worksheet(ss, "plan_bottom_line", header=None)
ensure_worksheet(ss, "plan_notes_assumptions", header=None)

with st.sidebar.expander("🧱 Initialize Sheet", expanded=False):
    if st.button("📥 Populate plan tabs from Excel", use_container_width=True):
        populate_plan_tabs(ss)
        st.success("Plan tabs populated.")
    if st.button("🌱 Seed assets snapshot", use_container_width=True):
        # only seed if empty (besides header)
        vals = ws_assets.get_all_values()
        if len(vals) <= 1:
            for row in DEFAULT_ASSETS:
                append_row(ws_assets, row, CORE_TABS["assets_snapshot"])
            st.success("Seeded assets.")
        else:
            st.info("assets_snapshot already has data — not overwriting.")

# Load dataframes
@st.cache_data(ttl=10)
def load_all(sheet_id: str):
    ss2 = open_spreadsheet(sheet_id)
    tx = df_from_ws(ss2.worksheet("transactions"))
    stock = df_from_ws(ss2.worksheet("stock_values"))
    assets = df_from_ws(ss2.worksheet("assets_snapshot"))
    settings = df_from_ws(ss2.worksheet("settings"))
    return tx, stock, assets, settings

tx_df, stock_df, assets_df, settings_df = load_all(sheet_id)

def clear_cache():
    load_all.clear()

def get_setting_value(k: str, default: str):
    if settings_df.empty:
        return default
    m = settings_df[settings_df["k"] == k]
    if m.empty:
        return default
    return str(m.iloc[0]["v"])

# Targets
with st.sidebar.expander("⚙️ Targets", expanded=False):
    base_salary = float(get_setting_value("base_salary", "15000") or 15000)
    target_savings_pct = float(get_setting_value("target_savings_pct", "40") or 40)

    base_salary = st.number_input("Base Salary (EGP)", value=base_salary, step=500.0)
    target_savings_pct = st.number_input("Savings Target %", value=target_savings_pct, step=5.0)

    if st.button("💾 Save Targets", use_container_width=True):
        # simple upsert by appending; last value wins
        ws_settings.append_row(["base_salary", str(base_salary)], value_input_option="USER_ENTERED")
        ws_settings.append_row(["target_savings_pct", str(target_savings_pct)], value_input_option="USER_ENTERED")
        clear_cache()
        st.success("Saved.")

# Month selector
active_month = st.sidebar.selectbox(
    "📊 Select Month",
    range(12),
    format_func=lambda x: MONTHS[x],
    index=today.month - 1
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🗓️ Weekly Inputs",
    "📈 Stocks Update",
    "🏦 Assets Snapshot",
    "📄 Plan (from Excel)"
])

# -------------------------
# Dashboard
# -------------------------
with tab1:
    st.header(f"📊 {MONTHS[active_month]} Overview")

    if not tx_df.empty:
        tx_df["amount_egp"] = pd.to_numeric(tx_df["amount_egp"], errors="coerce").fillna(0.0)
    if not stock_df.empty:
        stock_df["portfolio_value_egp"] = pd.to_numeric(stock_df["portfolio_value_egp"], errors="coerce").fillna(0.0)

    month = MONTHS[active_month]
    month_tx = tx_df[tx_df["month"] == month] if not tx_df.empty else pd.DataFrame()

    income_actual = month_tx[month_tx["tx_type"] == "income"]["amount_egp"].sum() if not month_tx.empty else 0.0
    expense_actual = month_tx[month_tx["tx_type"] == "expense"]["amount_egp"].sum() if not month_tx.empty else 0.0
    net = income_actual - expense_actual

    month_stock = stock_df[stock_df["month"] == month] if not stock_df.empty else pd.DataFrame()
    latest_stock_value = month_stock.tail(1)["portfolio_value_egp"].iloc[0] if not month_stock.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Income (Actual)", f"{income_actual:,.0f} EGP")
    c2.metric("💸 Expenses (Actual)", f"{expense_actual:,.0f} EGP")
    c3.metric("🧮 Net", f"{net:,.0f} EGP")
    c4.metric("📈 Stocks (Latest)", f"{latest_stock_value:,.0f} EGP")

    st.divider()

    st.subheader("🗓️ Weekly Summary (this month)")
    if not month_tx.empty:
        wk = month_tx.copy()
        weekly = wk.pivot_table(index="week_start", columns="tx_type", values="amount_egp", aggfunc="sum", fill_value=0.0).reset_index()
        if "income" not in weekly.columns:
            weekly["income"] = 0.0
        if "expense" not in weekly.columns:
            weekly["expense"] = 0.0
        weekly["net"] = weekly["income"] - weekly["expense"]
        st.dataframe(weekly.sort_values("week_start"), use_container_width=True)
    else:
        st.info("No transactions for this month yet. Use **Weekly Inputs**.")

# -------------------------
# Weekly Inputs
# -------------------------
with tab2:
    st.header("🗓️ Weekly Inputs")
    st.caption("Add weekly expenses and freelance income (stores rows in Google Sheets).")

    with st.form("weekly_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tx_date = st.date_input("Date", value=today)
            tx_kind = st.selectbox("Type", ["expense", "income"])
            category = st.selectbox(
                "Category",
                DEFAULT_CATEGORIES_EXPENSE if tx_kind == "expense" else DEFAULT_CATEGORIES_INCOME,
                index=0 if tx_kind == "expense" else 1  # freelance default
            )
        with col2:
            amount = st.number_input("Amount (EGP)", min_value=0.0, step=50.0, value=0.0)
            notes = st.text_input("Notes (optional)", value="")

        submitted = st.form_submit_button("➕ Add entry")
        if submitted:
            row = {
                "tx_date": tx_date.isoformat(),
                "week_start": week_start(tx_date).isoformat(),
                "month": month_name(tx_date),
                "tx_type": tx_kind,
                "category": category,
                "amount_egp": float(amount),
                "notes": notes
            }
            append_row(ws_tx, row, CORE_TABS["transactions"])
            clear_cache()
            st.success("Saved ✅")

    st.divider()
    st.subheader("This week so far")
    if not tx_df.empty:
        ws = week_start(today).isoformat()
        cur = tx_df[tx_df["week_start"] == ws].copy()
        if not cur.empty:
            cur["amount_egp"] = pd.to_numeric(cur["amount_egp"], errors="coerce").fillna(0.0)
            st.dataframe(cur[["tx_date", "tx_type", "category", "amount_egp", "notes"]].tail(50), use_container_width=True, hide_index=True)
        else:
            st.info("No entries yet for this week.")
    else:
        st.info("No data yet.")

# -------------------------
# Stocks Update
# -------------------------
with tab3:
    st.header("📈 Stocks Update (Manual)")
    st.caption("Once a week (or anytime), record your total stock portfolio value in EGP.")

    with st.form("stocks_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            as_of = st.date_input("As of date", value=today)
        with col2:
            value_egp = st.number_input("Portfolio value (EGP)", min_value=0.0, step=100.0, value=0.0)
        notes = st.text_input("Notes (optional)", value="")
        submitted = st.form_submit_button("💾 Save stock value")
        if submitted:
            row = {
                "as_of": as_of.isoformat(),
                "week_start": week_start(as_of).isoformat(),
                "month": month_name(as_of),
                "portfolio_value_egp": float(value_egp),
                "notes": notes
            }
            append_row(ws_stock, row, CORE_TABS["stock_values"])
            clear_cache()
            st.success("Saved ✅")

    st.divider()
    if not stock_df.empty:
        stock_df["portfolio_value_egp"] = pd.to_numeric(stock_df["portfolio_value_egp"], errors="coerce").fillna(0.0)
        st.subheader("History")
        st.dataframe(stock_df.tail(50), use_container_width=True, hide_index=True)

# -------------------------
# Assets Snapshot
# -------------------------
with tab4:
    st.header("🏦 Assets Snapshot")
    st.caption("Update gold grams / SAR amount / business value / stocks value whenever you want (append-only snapshots).")

    with st.form("assets_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            as_of = st.date_input("As of date", value=today)
            asset = st.text_input("Asset name", value="Gold 24K (Sabika)")
            quantity = st.number_input("Quantity", step=1.0, value=0.0)
            unit = st.text_input("Unit", value="gram")
        with col2:
            value_egp = st.text_input("Value in EGP (optional)", value="")
            notes = st.text_input("Notes (optional)", value="")
        submitted = st.form_submit_button("💾 Save snapshot")
        if submitted:
            row = {
                "as_of": as_of.isoformat(),
                "asset": asset,
                "quantity": quantity,
                "unit": unit,
                "value_egp": value_egp,
                "notes": notes
            }
            append_row(ws_assets, row, CORE_TABS["assets_snapshot"])
            clear_cache()
            st.success("Saved ✅")

    st.divider()
    if not assets_df.empty:
        st.subheader("Latest snapshots")
        st.dataframe(assets_df.tail(50), use_container_width=True, hide_index=True)
    else:
        st.info("No asset snapshots yet. Use 'Seed assets snapshot' in sidebar to start.")

# -------------------------
# Plan (raw)
# -------------------------
with tab5:
    st.header("📄 Plan (Imported from Excel)")
    st.caption("These tabs are a copy of your Excel plan sections, stored in the same Google Sheet.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Income & Expenses")
        st.dataframe(df_from_ws(ss.worksheet("plan_income_expenses"), header=False), use_container_width=True)
    with col2:
        st.subheader("Investments & Savings")
        st.dataframe(df_from_ws(ss.worksheet("plan_investments_savings"), header=False), use_container_width=True)

    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Bottom Line")
        st.dataframe(df_from_ws(ss.worksheet("plan_bottom_line"), header=False), use_container_width=True)
    with col4:
        st.subheader("Key Notes & Assumptions")
        st.dataframe(df_from_ws(ss.worksheet("plan_notes_assumptions"), header=False), use_container_width=True)

st.divider()
st.caption("💡 Tip: In Streamlit Cloud, set secrets: gcp_service_account + SHEET_ID for zero-config deploy.")
