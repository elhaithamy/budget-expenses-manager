import os
import sqlite3
from datetime import date, timedelta
import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Sort My Money - Budget 2026",
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
# DATE HELPERS
# =========================
def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Monday

def month_name(d: date) -> str:
    return MONTHS[d.month - 1]

# =========================
# DB HELPERS
# =========================
def ensure_parent_dir(path: str):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

def get_conn(db_path: str) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db(conn: sqlite3.Connection):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_date TEXT NOT NULL,
        week_start TEXT NOT NULL,
        month TEXT NOT NULL,
        tx_type TEXT NOT NULL,          -- income | expense
        category TEXT NOT NULL,
        amount_egp REAL NOT NULL,
        notes TEXT DEFAULT ''
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS stock_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        as_of TEXT NOT NULL,
        week_start TEXT NOT NULL,
        month TEXT NOT NULL,
        portfolio_value_egp REAL NOT NULL,
        notes TEXT DEFAULT ''
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        as_of TEXT NOT NULL,
        asset TEXT NOT NULL,
        quantity REAL,
        unit TEXT,
        value_egp REAL,
        notes TEXT DEFAULT ''
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS plan_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_sheet TEXT NOT NULL,
        section TEXT NOT NULL,
        item TEXT NOT NULL,
        month TEXT NOT NULL,
        amount REAL NOT NULL
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        k TEXT PRIMARY KEY,
        v TEXT NOT NULL
    );
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_week ON transactions(week_start);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_month ON transactions(month);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_week ON stock_values(week_start);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_asof ON assets(as_of);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_month ON plan_lines(month);")
    conn.commit()

def upsert_setting(conn: sqlite3.Connection, k: str, v: str):
    conn.execute(
        "INSERT INTO settings(k, v) VALUES(?, ?) "
        "ON CONFLICT(k) DO UPDATE SET v=excluded.v;",
        (k, v)
    )
    conn.commit()

def get_setting(conn: sqlite3.Connection, k: str, default: str = "") -> str:
    cur = conn.execute("SELECT v FROM settings WHERE k=?", (k,))
    row = cur.fetchone()
    return row[0] if row else default

def insert_transaction(conn: sqlite3.Connection, tx_date: date, tx_type: str, category: str, amount_egp: float, notes: str):
    ws = week_start(tx_date).isoformat()
    conn.execute(
        "INSERT INTO transactions(tx_date, week_start, month, tx_type, category, amount_egp, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?);",
        (tx_date.isoformat(), ws, month_name(tx_date), tx_type, category, float(amount_egp), notes or "")
    )
    conn.commit()

def insert_stock_value(conn: sqlite3.Connection, as_of: date, portfolio_value_egp: float, notes: str):
    ws = week_start(as_of).isoformat()
    conn.execute(
        "INSERT INTO stock_values(as_of, week_start, month, portfolio_value_egp, notes) "
        "VALUES (?, ?, ?, ?, ?);",
        (as_of.isoformat(), ws, month_name(as_of), float(portfolio_value_egp), notes or "")
    )
    conn.commit()

def upsert_asset_snapshot(conn: sqlite3.Connection, as_of: date, asset: str, quantity, unit: str, value_egp, notes: str):
    # We store snapshots (append-only) to keep history.
    conn.execute(
        "INSERT INTO assets(as_of, asset, quantity, unit, value_egp, notes) VALUES (?,?,?,?,?,?);",
        (as_of.isoformat(), asset, quantity, unit, value_egp, notes or "")
    )
    conn.commit()

@st.cache_data(ttl=5)
def load_df(db_path: str, sql: str) -> pd.DataFrame:
    conn = get_conn(db_path)
    init_db(conn)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

def clear_caches():
    load_df.clear()

# =========================
# SIDEBAR: DB LOCATION
# =========================
st.sidebar.title("💰 Sort My Money")
st.sidebar.caption("Budget Dashboard 2026 (SQLite + Weekly Logging)")

today = date.today()
st.sidebar.success(f"📅 Today: {today.strftime('%d %b %Y')}")
st.sidebar.info(f"📆 Week of {week_start(today).strftime('%d %b %Y')}")

st.sidebar.divider()

default_db_path = os.path.join(os.getcwd(), "budget_2026.db")
if "db_path" not in st.session_state:
    st.session_state.db_path = default_db_path

st.sidebar.subheader("🗄️ Database Location")
db_path = st.sidebar.text_input(
    "SQLite DB path (put inside your Google Drive synced folder)",
    value=st.session_state.db_path,
)
st.session_state.db_path = db_path

conn = get_conn(db_path)
init_db(conn)

st.sidebar.divider()
st.sidebar.subheader("⚙️ Targets")
base_salary = float(get_setting(conn, "base_salary", "15000") or "15000")
target_savings_pct = float(get_setting(conn, "target_savings_pct", "40") or "40")
base_salary = st.sidebar.number_input("Base Salary (EGP)", value=base_salary, step=500.0)
target_savings_pct = st.sidebar.number_input("Savings Target %", value=target_savings_pct, step=5.0)
if st.sidebar.button("💾 Save Targets", use_container_width=True):
    upsert_setting(conn, "base_salary", str(base_salary))
    upsert_setting(conn, "target_savings_pct", str(target_savings_pct))
    st.sidebar.success("Saved.")
conn.close()

st.sidebar.divider()
active_month = st.sidebar.selectbox(
    "📊 Select Month",
    range(12),
    format_func=lambda x: MONTHS[x],
    index=today.month - 1
)

# =========================
# LOAD DATA
# =========================
df_tx = load_df(db_path, "SELECT * FROM transactions;")
df_stock = load_df(db_path, "SELECT * FROM stock_values;")
df_assets = load_df(db_path, "SELECT * FROM assets;")
df_plan = load_df(db_path, "SELECT * FROM plan_lines;")

for col in ["tx_date", "week_start"]:
    if col in df_tx.columns and not df_tx.empty:
        df_tx[col] = pd.to_datetime(df_tx[col])

for col in ["as_of", "week_start"]:
    if col in df_stock.columns and not df_stock.empty:
        df_stock[col] = pd.to_datetime(df_stock[col])

if "as_of" in df_assets.columns and not df_assets.empty:
    df_assets["as_of"] = pd.to_datetime(df_assets["as_of"])

# =========================
# UI TABS
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🗓️ Weekly Inputs",
    "📈 Stocks",
    "🏦 Assets",
    "🧾 Plan (from Excel)"
])

# =========================
# TAB 1: DASHBOARD
# =========================
with tab1:
    st.header(f"📊 {MONTHS[active_month]} Overview")
    month = MONTHS[active_month]
    month_tx = df_tx[df_tx["month"] == month] if not df_tx.empty else pd.DataFrame()

    income_actual = month_tx[month_tx["tx_type"] == "income"]["amount_egp"].sum() if not month_tx.empty else 0.0
    expense_actual = month_tx[month_tx["tx_type"] == "expense"]["amount_egp"].sum() if not month_tx.empty else 0.0
    net = income_actual - expense_actual

    month_stock = df_stock[df_stock["month"] == month] if not df_stock.empty else pd.DataFrame()
    latest_stock_value = month_stock.sort_values("as_of").tail(1)["portfolio_value_egp"].iloc[0] if not month_stock.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Income (Actual)", f"{income_actual:,.0f} EGP")
    c2.metric("💸 Expenses (Actual)", f"{expense_actual:,.0f} EGP")
    c3.metric("🧮 Net", f"{net:,.0f} EGP")
    c4.metric("📈 Stocks (Latest)", f"{latest_stock_value:,.0f} EGP")

    st.divider()

    if not month_tx.empty:
        wk = month_tx.copy()
        wk["week_start"] = pd.to_datetime(wk["week_start"]).dt.date
        weekly = wk.pivot_table(
            index="week_start",
            columns="tx_type",
            values="amount_egp",
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()
        weekly["net"] = weekly.get("income", 0.0) - weekly.get("expense", 0.0)

        st.subheader("🗓️ Weekly Summary")
        st.dataframe(weekly.sort_values("week_start"), use_container_width=True)

        st.subheader("📉 Weekly Net")
        fig = px.bar(weekly, x="week_start", y="net")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transactions yet for this month. Use **Weekly Inputs** to start logging.")

# =========================
# TAB 2: WEEKLY INPUTS
# =========================
with tab2:
    st.header("🗓️ Weekly Updates (Expenses + Freelance Income)")
    st.caption("Add rows any time; the app aggregates weekly/monthly automatically.")

    with st.form("weekly_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tx_date = st.date_input("Date", value=today)
            tx_kind = st.selectbox("Type", ["expense", "income"])
            if tx_kind == "expense":
                category = st.selectbox("Expense category", DEFAULT_CATEGORIES_EXPENSE)
            else:
                category = st.selectbox("Income category", DEFAULT_CATEGORIES_INCOME, index=1)  # freelance default
        with col2:
            amount = st.number_input("Amount (EGP)", min_value=0.0, step=50.0, value=0.0)
            notes = st.text_input("Notes (optional)", value="")

        submitted = st.form_submit_button("➕ Add entry")
        if submitted:
            conn = get_conn(db_path)
            init_db(conn)
            insert_transaction(conn, tx_date, tx_kind, category, amount, notes)
            conn.close()
            clear_caches()
            st.success("Saved ✅")

# =========================
# TAB 3: STOCKS
# =========================
with tab3:
    st.header("📈 Stocks (Manual Weekly Valuation)")
    st.caption("Once a week, enter your total portfolio value in EGP.")

    with st.form("stocks_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            as_of = st.date_input("As of date", value=today, key="stocks_as_of")
        with col2:
            value_egp = st.number_input("Portfolio value (EGP)", min_value=0.0, step=100.0, value=0.0)
        notes = st.text_input("Notes (optional)", value="", key="stocks_notes")

        submitted = st.form_submit_button("💾 Save weekly stock value")
        if submitted:
            conn = get_conn(db_path)
            init_db(conn)
            insert_stock_value(conn, as_of, value_egp, notes)
            conn.close()
            clear_caches()
            st.success("Saved ✅")

    st.divider()
    if not df_stock.empty:
        df_plot = df_stock.sort_values("as_of").copy()
        fig = px.line(df_plot, x="as_of", y="portfolio_value_egp", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_stock.sort_values("as_of", ascending=False).head(25), use_container_width=True, hide_index=True)
    else:
        st.info("No stock values yet.")

# =========================
# TAB 4: ASSETS (Gold, SAR, Business, Stocks)
# =========================
with tab4:
    st.header("🏦 Assets (Snapshots)")
    st.caption("This stores snapshots in the database. You can add a new snapshot whenever you want (weekly/monthly).")

    # Show latest snapshot per asset
    if df_assets.empty:
        st.warning("No assets found in DB yet.")
    else:
        latest = (df_assets.sort_values("as_of")
                  .groupby("asset", as_index=False)
                  .tail(1)
                  .sort_values("asset"))
        st.subheader("Latest per asset")
        st.dataframe(
            latest[["as_of", "asset", "quantity", "unit", "value_egp", "notes"]].sort_values("asset"),
            use_container_width=True,
            hide_index=True
        )

    st.divider()
    st.subheader("Add a new asset snapshot")
    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            as_of = st.date_input("As of", value=today, key="asset_as_of")
            asset = st.selectbox("Asset", ["Gold 24K (Sabika)", "SAR Cash", "Business Investment", "Stocks (Portfolio Value)", "Cash (EGP)"])
        with col2:
            quantity = st.number_input("Quantity (optional)", value=0.0, step=1.0)
            unit = st.text_input("Unit (optional)", value="")
            value_egp = st.number_input("Value in EGP (optional)", min_value=0.0, step=100.0, value=0.0)
        notes = st.text_input("Notes", value="", key="asset_notes")

        submitted = st.form_submit_button("💾 Save snapshot")
        if submitted:
            q = None if quantity == 0 else float(quantity)
            u = unit.strip() if unit.strip() else None
            v = None if value_egp == 0 else float(value_egp)

            conn = get_conn(db_path)
            init_db(conn)
            upsert_asset_snapshot(conn, as_of, asset, q, u, v, notes)
            conn.close()
            clear_caches()
            st.success("Saved ✅")

# =========================
# TAB 5: PLAN (from your Excel import)
# =========================
with tab5:
    st.header("🧾 2026 Plan (Imported from Excel)")
    if df_plan.empty:
        st.info("No plan lines found in DB.")
    else:
        month = MONTHS[active_month]
        plan_month = df_plan[df_plan["month"] == f"{month} 2026"].copy()
        st.subheader(f"Plan for {month} 2026")
        st.dataframe(
            plan_month.sort_values(["source_sheet","section","item"]),
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        st.subheader("Search the plan")
        q = st.text_input("Search keyword (item/section)")
        if q:
            res = df_plan[df_plan["item"].str.contains(q, case=False, na=False) |
                          df_plan["section"].str.contains(q, case=False, na=False)]
            st.dataframe(res.sort_values(["month","source_sheet","section"]), use_container_width=True, hide_index=True)
