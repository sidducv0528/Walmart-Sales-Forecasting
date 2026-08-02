import os
import re
import textwrap
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Walmart Sales Forecasting", page_icon="🛒",
                    layout="wide", initial_sidebar_state="expanded")


def html(content):
    """Render a raw-HTML string via st.markdown, safely.

    Multi-line HTML written inside indented Python blocks inherits that
    indentation as literal leading whitespace in the string. CommonMark
    (Streamlit's markdown parser) treats 4+ leading spaces on a line as
    an INDENTED CODE BLOCK -- so instead of parsing the HTML, it prints
    the raw tags as visible text. Stripping all leading whitespace from
    every line before handing it to st.markdown avoids that entirely.
    """
    st.markdown(re.sub(r"(?m)^[ \t]+", "", content), unsafe_allow_html=True)

# ==================================================================
# GLOBAL CSS
# Only styles OUR OWN custom elements (kpi cards, brand text, footer).
# Native widgets (selectbox, slider, etc.) are left alone and themed
# via .streamlit/config.toml instead -- trying to override BaseWeb
# internals with generic CSS is what caused the black-box bug before.
# Uses Streamlit's own CSS variables so it follows whatever theme the
# user has picked (Settings -> Theme in the top-right menu).
# ==================================================================
st.markdown("""
<style>
.kpi-card {
    border-radius: 14px; padding: 18px 20px; height: 108px;
    display: flex; flex-direction: column; justify-content: center;
    border: 1px solid rgba(49, 51, 63, 0.15);
}
.kpi-icon { font-size: 22px; }
.kpi-title { font-size: 13px; font-weight: 600; margin-top: 2px; }
.kpi-value { font-size: 26px; font-weight: 800; margin-top: 2px; color: var(--text-color); }
.kpi-sub { font-size: 12px; opacity: 0.65; }

.brand-title { font-size: 26px; font-weight: 800; color: #0071CE; line-height: 1.1; }
.brand-sub { font-size: 13px; font-weight: 700; color: #FFC220; margin-top: -4px; }

.footer-banner {
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(49, 51, 63, 0.15);
    border-radius: 12px; padding: 14px 20px; display: flex;
    justify-content: space-between; align-items: center; margin-top: 6px;
}
.stat-box {
    background: linear-gradient(135deg, #e8f1fc, #dce9fb); border-radius: 12px;
    padding: 16px; margin-top: 10px;
}
.stat-box * { color: #1a1f36 !important; }
.section-tag {
    font-size: 11px; font-weight: 700; letter-spacing: 1px; opacity: 0.55;
    margin-top: 6px;
}
.hero {
    background: linear-gradient(120deg, #0071CE 0%, #0059a3 100%);
    border-radius: 16px; padding: 26px 28px; margin-bottom: 18px;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 14px;
}
.hero * { color: #ffffff !important; }
.hero-title { font-size: 28px; font-weight: 800; margin: 0; }
.hero-sub { font-size: 14px; opacity: 0.9; margin-top: 2px; }
.hero-badges { display: flex; gap: 8px; flex-wrap: wrap; }
.hero-badge {
    background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.35);
    border-radius: 20px; padding: 5px 12px; font-size: 12px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_white"

# ------------------------------------------------------------------
# BRAND MARK
# An original icon (rising bars inside a rounded storefront frame) --
# not a reproduction of any company's trademarked logo. Pairs with the
# Walmart-blue / gold accent colors already used across the dashboard.
# ------------------------------------------------------------------
BRAND_MARK_SVG = """
<svg width="38" height="38" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <rect x="1" y="1" width="38" height="38" rx="10" fill="#0071CE"/>
  <rect x="9"  y="21" width="5" height="10" rx="1.5" fill="#ffffff"/>
  <rect x="17.5" y="15" width="5" height="16" rx="1.5" fill="#ffffff"/>
  <rect x="26" y="9"  width="5" height="22" rx="1.5" fill="#FFC220"/>
  <path d="M9 17 L17 11 L23 14 L31 6" stroke="#FFC220" stroke-width="2.2"
        fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M26 6 L31 6 L31 11" stroke="#FFC220" stroke-width="2.2"
        fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def money(v):
    if abs(v) >= 1e9:
        return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.2f}M"
    if abs(v) >= 1e3:
        return f"${v/1e3:.1f}K"
    return f"${v:,.0f}"


def kpi_card(col, icon, title, value, sub, bg, fg):
    with col:
        html(f"""
        <div class="kpi-card" style="background-color:{bg};">
            <span class="kpi-icon">{icon}</span>
            <span class="kpi-title" style="color:{fg};">{title}</span>
            <span class="kpi-value">{value}</span>
            <span class="kpi-sub">{sub}</span>
        </div>
        """)


def chart_card(title):
    """Returns a native bordered container with a title inside it.
    Everything rendered inside `with chart_card(...):` stays visually
    grouped -- unlike raw <div> tags split across st.markdown calls,
    which do NOT nest and produce stray empty boxes."""
    box = st.container(border=True)
    box.markdown(f"**{title}**")
    return box


def clean_fig(fig, height=320):
    fig.update_layout(template=PLOTLY_TEMPLATE, height=height,
                       margin=dict(l=10, r=10, t=10, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


# ==================================================================
# DATA (with a clear error message instead of a raw traceback if a
# CSV is missing from the folder)
# ==================================================================
# Resolve paths relative to THIS FILE's location, not the process's working
# directory. Streamlit Cloud runs the app with the working directory set to
# the repo root regardless of which subfolder app.py lives in, so bare
# filenames like "walmart_cleaned.csv" silently fail to resolve if app.py
# isn't at the repo root. Building paths off __file__ makes this work no
# matter where the app folder sits in the repo.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REQUIRED_FILES = ["walmart_cleaned.csv", "forecast_next_12_weeks.csv",
                   "model_evaluation_metrics.csv", "actual_vs_predicted_holdout.csv"]


@st.cache_data
def load_data():
    paths = {f: os.path.join(BASE_DIR, f) for f in REQUIRED_FILES}
    missing = [f for f, p in paths.items() if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(missing)
    history = pd.read_csv(paths["walmart_cleaned.csv"], parse_dates=["Date"])
    forecast = pd.read_csv(paths["forecast_next_12_weeks.csv"], parse_dates=["Date"])
    evaluation = pd.read_csv(paths["model_evaluation_metrics.csv"])
    holdout = pd.read_csv(paths["actual_vs_predicted_holdout.csv"], parse_dates=["Date"])
    return history, forecast, evaluation, holdout


try:
    history, forecast, evaluation, holdout = load_data()
except FileNotFoundError as e:
    st.error(
        "**Missing data files.** This app needs the following CSVs in the "
        f"same folder as `app.py`:\n\n" + "\n".join(f"- `{f}`" for f in e.args[0]) +
        "\n\nMake sure they were extracted alongside `app.py` (not left inside a zip "
        "or a different folder), then rerun `streamlit run app.py`."
    )
    st.stop()

history["Year"] = history["Date"].dt.year
history["MonthStart"] = history["Date"].dt.to_period("M").dt.to_timestamp()
stores_all = sorted(history["Store"].unique())
years_all = sorted(history["Year"].unique())

# ==================================================================
# SIDEBAR
# ==================================================================
with st.sidebar:
    html(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom: 4px;">
        {BRAND_MARK_SVG}
        <div>
            <span class="brand-title">Walmart</span><br>
            <span class="brand-sub">Sales Forecasting</span>
        </div>
    </div>
    """)
    st.write("")

    html('<div class="section-tag">NAVIGATION</div>')
    page = option_menu(
        menu_title=None,
        options=["Home", "EDA Dashboard", "Store Analysis", "Sales Forecasting",
                 "All Stores Forecast", "About Project"],
        icons=["house-fill", "bar-chart-line-fill", "shop", "graph-up-arrow",
               "table", "info-circle-fill"],
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": "transparent"},
            "icon": {"font-size": "15px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "2px 0",
                         "border-radius": "8px", "padding": "9px 12px"},
            "nav-link-selected": {"background-color": "#e7f0fd", "color": "#0071CE", "font-weight": "700"},
        },
    )

    st.write("")
    html('<div class="section-tag">FILTERS</div>')

    sel_store = st.selectbox("Select Store", ["All Stores"] + [str(s) for s in stores_all])
    sel_year = st.selectbox("Select Year", ["All Years"] + [str(y) for y in years_all])
    sel_holiday = st.selectbox("Holiday Flag", ["All", "Holiday", "Non-Holiday"])

    min_d, max_d = history["Date"].min().to_pydatetime(), history["Date"].max().to_pydatetime()
    date_range = st.slider("Select Date Range", min_value=min_d, max_value=max_d,
                            value=(min_d, max_d), format="DD-MM-YYYY")

    st.caption("Tip: switch Light/Dark from the ⋮ menu (top right) → Settings → Theme. "
               "That's Streamlit's native toggle and re-themes every widget consistently.")

    st.markdown("---")
    html("""
    <div style="text-align:center; padding-top: 2px; line-height: 2;">
        <a href="https://github.com/sidducv0528" target="_blank" style="text-decoration:none; margin: 0 6px; color:#0071CE; font-weight:600; font-size:13px;">
            🔗 GitHub
        </a>
        <a href="https://linkedin.com/in/siddu-data/" target="_blank" style="text-decoration:none; margin: 0 6px; color:#0071CE; font-weight:600; font-size:13px;">
            💼 LinkedIn
        </a>
        <br>
        <a href="mailto:sidducv0528@gmail.com" style="text-decoration:none; margin: 0 6px; color:#0071CE; font-weight:600; font-size:13px;">
            ✉️ sidducv0528@gmail.com
        </a>
    </div>
    """)

# Apply filters -> filtered history used across Home / EDA / Store Analysis
filtered = history.copy()
if sel_store != "All Stores":
    filtered = filtered[filtered["Store"] == int(sel_store)]
if sel_year != "All Years":
    filtered = filtered[filtered["Year"] == int(sel_year)]
if sel_holiday == "Holiday":
    filtered = filtered[filtered["Holiday_Flag"] == 1]
elif sel_holiday == "Non-Holiday":
    filtered = filtered[filtered["Holiday_Flag"] == 0]
filtered = filtered[(filtered["Date"] >= date_range[0]) & (filtered["Date"] <= date_range[1])]

with st.sidebar:
    html(f"""
    <div class="stat-box">
        <div style="font-size:12px;font-weight:700;color:#0071CE;">📊 Total Records</div>
        <div style="font-size:24px;font-weight:800;">{len(filtered):,}</div>
        <div style="font-size:12px;">Total Stores: {filtered['Store'].nunique()}</div>
    </div>
    """)

# ==================================================================
# PAGE: HOME
# ==================================================================
if page == "Home":
    html(f"""
    <div class="hero">
        <div style="display:flex; align-items:center; gap:16px;">
            {BRAND_MARK_SVG}
            <div>
                <p class="hero-title">Walmart Sales Forecasting Dashboard</p>
                <p class="hero-sub">Explore weekly sales data and forecast the next 12 weeks with a SARIMA model, store by store.</p>
            </div>
        </div>
        <div class="hero-badges">
            <span class="hero-badge">🐍 Python</span>
            <span class="hero-badge">📈 SARIMAX</span>
            <span class="hero-badge">⚡ Streamlit</span>
            <span class="hero-badge">45 Stores</span>
        </div>
    </div>
    """)

    if filtered.empty:
        st.warning("No data matches the current filters. Try widening the date range or store/year selection.")
        st.stop()

    total_sales = filtered["Weekly_Sales"].sum()
    avg_weekly = filtered["Weekly_Sales"].mean()
    n_stores = filtered["Store"].nunique()
    n_weeks = filtered["Date"].nunique()
    n_holiday = int(filtered["Holiday_Flag"].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    kpi_card(c1, "🛒", "Total Sales", money(total_sales), "Total Weekly Sales", "#e8f1fc", "#0071CE")
    kpi_card(c2, "📈", "Average Weekly Sales", money(avg_weekly), "Across Filtered Stores", "#e7f8ef", "#1a9d5c")
    kpi_card(c3, "🏬", "Total Stores", f"{n_stores}", "Walmart Stores", "#f1ecfb", "#7c4fd6")
    kpi_card(c4, "📅", "Total Weeks", f"{n_weeks}", "Weeks of Data", "#fdf1e2", "#d98a1a")
    kpi_card(c5, "🎁", "Holiday Weeks", f"{n_holiday}", "Holiday Observations", "#fce9ea", "#d94f5c")

    st.write("")
    col1, col2, col3 = st.columns([1.3, 1, 1.1])

    with col1:
        with chart_card("Weekly Sales Trend (All Stores)"):
            trend = filtered.groupby("Date", as_index=False)["Weekly_Sales"].sum()
            fig = go.Figure(go.Scatter(x=trend["Date"], y=trend["Weekly_Sales"], mode="lines",
                                        line=dict(color="#0071CE", width=1.5)))
            fig.update_layout(xaxis_title="Date", yaxis_title="Weekly Sales")
            st.plotly_chart(clean_fig(fig), width='stretch')

    with col2:
        with chart_card("Holiday vs Non-Holiday Sales"):
            hol = filtered.groupby("Holiday_Flag")["Weekly_Sales"].sum()
            labels = ["Non-Holiday" if i == 0 else "Holiday" for i in hol.index]
            fig = go.Figure(go.Pie(labels=labels, values=hol.values, hole=0.62,
                                    marker=dict(colors=["#0071CE", "#FFA000"]), textinfo="none"))
            fig.update_layout(legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(clean_fig(fig), width='stretch')

    with col3:
        with chart_card("Top 10 Stores by Total Sales"):
            top10 = filtered.groupby("Store")["Weekly_Sales"].sum().sort_values(ascending=False).head(10)
            fig = go.Figure(go.Bar(x=top10.values[::-1], y=[f"Store {s}" for s in top10.index[::-1]],
                                    orientation="h", marker_color="#2fb872"))
            fig.update_layout(xaxis_title="Total Sales")
            st.plotly_chart(clean_fig(fig), width='stretch')

    col4, col5 = st.columns([1.2, 1.2])
    with col4:
        with chart_card("Dataset Preview"):
            st.dataframe(filtered.drop(columns=["Year", "MonthStart"]).head(5),
                         width='stretch', hide_index=True)
            st.caption(f"Showing first 5 of {len(filtered):,} rows")

    with col5:
        with chart_card("Monthly Sales Trend (All Stores)"):
            monthly = filtered.groupby("MonthStart", as_index=False)["Weekly_Sales"].sum()
            fig = go.Figure(go.Scatter(x=monthly["MonthStart"], y=monthly["Weekly_Sales"],
                                        mode="lines+markers", line=dict(color="#8659e0", width=2),
                                        marker=dict(size=5)))
            fig.update_layout(xaxis_title="Month", yaxis_title="Sales")
            st.plotly_chart(clean_fig(fig), width='stretch')

    html("""
    <div class="footer-banner">
        <div>🎯 <b>Project Objective:</b> To analyze Walmart sales data and forecast future sales for better inventory planning and decision making.</div>
        <div style="opacity:0.6;">Built with ❤️ Streamlit</div>
    </div>
    """)

# ==================================================================
# PAGE: EDA DASHBOARD
# ==================================================================
elif page == "EDA Dashboard":
    st.title("Exploratory Data Analysis")
    st.caption("Business questions answered from the Walmart weekly sales dataset.")

    sample = history.sample(min(1500, len(history)), random_state=1)

    col1, col2 = st.columns(2)
    with col1:
        with chart_card("Unemployment vs Weekly Sales — Store Correlation"):
            store_corr = history.groupby("Store").apply(
                lambda x: x["Weekly_Sales"].corr(x["Unemployment"])).sort_values()
            fig = go.Figure(go.Bar(
                x=store_corr.values, y=[f"Store {s}" for s in store_corr.index], orientation="h",
                marker_color=np.where(store_corr.values < 0, "#d94f5c", "#2fb872")
            ))
            fig.update_layout(xaxis_title="Correlation")
            st.plotly_chart(clean_fig(fig, height=900), width='stretch')
            overall_corr = history["Weekly_Sales"].corr(history["Unemployment"])
            st.caption(f"Overall correlation: {overall_corr:.4f} — weak overall, but a subset of stores are more sensitive.")

    with col2:
        with chart_card("Seasonality — Average Sales by Month"):
            monthly_avg = history.groupby(history["Date"].dt.month)["Weekly_Sales"].mean()
            fig = go.Figure(go.Bar(x=monthly_avg.index, y=monthly_avg.values, marker_color="#0071CE"))
            fig.update_layout(xaxis_title="Month", yaxis_title="Avg Weekly Sales")
            st.plotly_chart(clean_fig(fig, height=380), width='stretch')
            holiday_avg = history.groupby("Holiday_Flag")["Weekly_Sales"].mean()
            lift = (holiday_avg[1] / holiday_avg[0] - 1) * 100
            st.caption(f"Holiday weeks sell {lift:.1f}% more on average. Peaks in Nov/Dec (Thanksgiving, Christmas).")

        with chart_card("Temperature vs Weekly Sales"):
            fig2 = go.Figure(go.Scatter(x=sample["Temperature"], y=sample["Weekly_Sales"], mode="markers",
                                         marker=dict(color="#7c4fd6", opacity=0.35, size=5)))
            fig2.update_layout(xaxis_title="Temperature", yaxis_title="Weekly Sales")
            st.plotly_chart(clean_fig(fig2, height=340), width='stretch')
            temp_corr = history["Weekly_Sales"].corr(history["Temperature"])
            st.caption(f"Correlation: {temp_corr:.4f} — temperature has minimal effect on sales.")

    col3, col4 = st.columns(2)
    with col3:
        with chart_card("CPI vs Weekly Sales"):
            fig = go.Figure(go.Scatter(x=sample["CPI"], y=sample["Weekly_Sales"], mode="markers",
                                        marker=dict(color="#d98a1a", opacity=0.35, size=5)))
            fig.update_layout(xaxis_title="CPI", yaxis_title="Weekly Sales")
            st.plotly_chart(clean_fig(fig, height=340), width='stretch')
            cpi_corr = history["Weekly_Sales"].corr(history["CPI"])
            st.caption(f"Overall correlation: {cpi_corr:.4f} — weak overall; a few stores are more price-sensitive.")

    with col4:
        with chart_card("Best vs Worst Performing Store"):
            store_totals = history.groupby("Store")["Weekly_Sales"].sum().sort_values(ascending=False)
            best_store, worst_store = store_totals.idxmax(), store_totals.idxmin()
            gap_pct = (store_totals.max() / store_totals.min() - 1) * 100
            b1, b2 = st.columns(2)
            b1.metric("Best Store", f"Store {best_store}", money(store_totals.max()))
            b2.metric("Worst Store", f"Store {worst_store}", money(store_totals.min()))
            st.caption(f"The best store sold {gap_pct:.1f}% more than the worst over the full period — "
                       "supports store-level planning over a one-size-fits-all approach.")

# ==================================================================
# PAGE: STORE ANALYSIS
# ==================================================================
elif page == "Store Analysis":
    st.title("Store Analysis")
    default_idx = stores_all.index(int(sel_store)) if sel_store != "All Stores" else 0
    pick_store = st.selectbox("Choose a store to inspect", stores_all, index=default_idx)
    sdf = history[history["Store"] == pick_store].sort_values("Date")

    total_sales = sdf["Weekly_Sales"].sum()
    store_totals_sorted = history.groupby("Store")["Weekly_Sales"].sum().sort_values(ascending=False)
    rank = int(np.where(store_totals_sorted.index == pick_store)[0][0]) + 1
    holiday_lift = (sdf.loc[sdf.Holiday_Flag == 1, "Weekly_Sales"].mean() /
                     sdf.loc[sdf.Holiday_Flag == 0, "Weekly_Sales"].mean() - 1) * 100

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "💰", "Total Sales", money(total_sales), f"Store {pick_store}", "#e8f1fc", "#0071CE")
    kpi_card(c2, "📊", "Avg Weekly Sales", money(sdf["Weekly_Sales"].mean()), "Per week", "#e7f8ef", "#1a9d5c")
    kpi_card(c3, "🏆", "Sales Rank", f"#{rank} / 45", "Among all stores", "#f1ecfb", "#7c4fd6")
    kpi_card(c4, "🎄", "Holiday Lift", f"{holiday_lift:.1f}%", "Holiday vs Non-holiday", "#fdf1e2", "#d98a1a")

    with chart_card(f"Store {pick_store} — Weekly Sales History"):
        fig = go.Figure(go.Scatter(x=sdf["Date"], y=sdf["Weekly_Sales"], mode="lines", line=dict(color="#0071CE")))
        st.plotly_chart(clean_fig(fig, height=340), width='stretch')

    col1, col2 = st.columns(2)
    with col1:
        with chart_card("Sensitivity to Economic Factors"):
            u_corr = sdf["Weekly_Sales"].corr(sdf["Unemployment"])
            c_corr = sdf["Weekly_Sales"].corr(sdf["CPI"])
            t_corr = sdf["Weekly_Sales"].corr(sdf["Temperature"])
            fig = go.Figure(go.Bar(x=["Unemployment", "CPI", "Temperature"], y=[u_corr, c_corr, t_corr],
                                    marker_color=["#d94f5c", "#d98a1a", "#7c4fd6"]))
            fig.update_layout(yaxis_title="Correlation with Weekly Sales")
            st.plotly_chart(clean_fig(fig), width='stretch')

    with col2:
        with chart_card("Monthly Seasonality — This Store"):
            m_avg = sdf.groupby(sdf["Date"].dt.month)["Weekly_Sales"].mean()
            fig = go.Figure(go.Bar(x=m_avg.index, y=m_avg.values, marker_color="#2fb872"))
            fig.update_layout(xaxis_title="Month", yaxis_title="Avg Weekly Sales")
            st.plotly_chart(clean_fig(fig), width='stretch')

# ==================================================================
# PAGE: SALES FORECASTING (single store, SARIMAX)
# ==================================================================
elif page == "Sales Forecasting":
    st.title("Sales Forecasting")
    default_idx = stores_all.index(int(sel_store)) if sel_store != "All Stores" else 0
    store = st.selectbox("Select Store", stores_all, index=default_idx)

    store_hist = history[history["Store"] == store].sort_values("Date")
    store_fcst = forecast[forecast["Store"] == store].sort_values("Date")
    store_eval = evaluation[evaluation["Store"] == store].iloc[0]
    store_hold = holdout[holdout["Store"] == store].sort_values("Date")

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "📏", "MAE", f"${store_eval['MAE']:,.0f}", "Mean Absolute Error", "#e8f1fc", "#0071CE")
    kpi_card(c2, "📐", "RMSE", f"${store_eval['RMSE']:,.0f}", "Root Mean Sq. Error", "#f1ecfb", "#7c4fd6")
    kpi_card(c3, "🎯", "MAPE", f"{store_eval['MAPE (%)']:.2f}%", "Mean Abs. % Error", "#fdf1e2", "#d98a1a")
    mape = store_eval["MAPE (%)"]
    verdict = "Excellent" if mape < 10 else "Good" if mape < 20 else "Needs Improvement"
    vcolor = "#e7f8ef" if verdict == "Excellent" else "#fdf1e2" if verdict == "Good" else "#fce9ea"
    kpi_card(c4, "✅", "Accuracy", verdict, "Model rating", vcolor, "#1a9d5c")

    with chart_card(f"Store {store} — Historical Sales & 12-Week Forecast"):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=store_hist["Date"], y=store_hist["Weekly_Sales"], mode="lines",
                                  name="Historical", line=dict(color="#0071CE")))
        fig.add_trace(go.Scatter(x=store_fcst["Date"], y=store_fcst["Forecasted_Sales"], mode="lines+markers",
                                  name="Forecast (next 12 weeks)", line=dict(color="#d94f5c", dash="dash")))
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(clean_fig(fig, height=380), width='stretch')

    col1, col2 = st.columns(2)
    with col1:
        with chart_card("Actual vs Predicted (held-out test, last 12 weeks)"):
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=store_hold["Date"], y=store_hold["Actual_Sales"], mode="lines+markers",
                                       name="Actual", line=dict(color="#0071CE")))
            fig2.add_trace(go.Scatter(x=store_hold["Date"], y=store_hold["Predicted_Sales"], mode="lines+markers",
                                       name="Predicted", line=dict(color="#d98a1a")))
            fig2.update_layout(hovermode="x unified")
            st.plotly_chart(clean_fig(fig2), width='stretch')

    with col2:
        with chart_card("Next 12 Weeks — Forecasted Sales"):
            st.dataframe(store_fcst[["Date", "Forecasted_Sales"]].rename(
                columns={"Forecasted_Sales": "Forecasted Sales ($)"}
            ).style.format({"Forecasted Sales ($)": "{:,.0f}"}), width='stretch', hide_index=True)
            st.download_button("Download this store's forecast (CSV)", store_fcst.to_csv(index=False),
                                file_name=f"store_{store}_forecast.csv", mime="text/csv")

# ==================================================================
# PAGE: ALL STORES FORECAST
# ==================================================================
elif page == "All Stores Forecast":
    st.title("All Stores Forecast — Model Performance")

    c1, c2, c3 = st.columns(3)
    kpi_card(c1, "📉", "Avg MAPE", f"{evaluation['MAPE (%)'].mean():.2f}%", "All 45 stores", "#e8f1fc", "#0071CE")
    kpi_card(c2, "🏅", "Best Store MAPE", f"{evaluation['MAPE (%)'].min():.2f}%",
              f"Store {evaluation.loc[evaluation['MAPE (%)'].idxmin(), 'Store']}", "#e7f8ef", "#1a9d5c")
    kpi_card(c3, "⚠️", "Worst Store MAPE", f"{evaluation['MAPE (%)'].max():.2f}%",
              f"Store {evaluation.loc[evaluation['MAPE (%)'].idxmax(), 'Store']}", "#fce9ea", "#d94f5c")

    with chart_card("MAPE by Store (sorted)"):
        ev_sorted = evaluation.sort_values("MAPE (%)")
        colors = np.where(ev_sorted["MAPE (%)"] < 10, "#2fb872",
                           np.where(ev_sorted["MAPE (%)"] < 20, "#d98a1a", "#d94f5c"))
        fig = go.Figure(go.Bar(x=ev_sorted["Store"].astype(str), y=ev_sorted["MAPE (%)"], marker_color=colors))
        fig.update_layout(xaxis_title="Store", yaxis_title="MAPE (%)")
        st.plotly_chart(clean_fig(fig, height=380), width='stretch')
        st.caption("🟢 Excellent (<10%)   🟠 Good (<20%)   🔴 Needs Improvement (≥20%)")

    col1, col2 = st.columns(2)
    with col1:
        with chart_card("Top 5 Best Forecasted Stores"):
            st.dataframe(evaluation.sort_values("MAPE (%)").head(5), width='stretch', hide_index=True)
    with col2:
        with chart_card("Top 5 Worst Forecasted Stores"):
            st.dataframe(evaluation.sort_values("MAPE (%)", ascending=False).head(5),
                         width='stretch', hide_index=True)

    with chart_card("Full Evaluation Table — All Stores"):
        st.dataframe(evaluation, width='stretch', hide_index=True)
        d1, d2 = st.columns(2)
        d1.download_button("Download evaluation metrics (CSV)", evaluation.to_csv(index=False),
                            file_name="model_evaluation_metrics.csv", mime="text/csv")
        d2.download_button("Download all-store 12-week forecast (CSV)", forecast.to_csv(index=False),
                            file_name="forecast_next_12_weeks.csv", mime="text/csv")

# ==================================================================
# PAGE: ABOUT PROJECT
# ==================================================================
else:
    st.title("About This Project")
    with chart_card(""):
        st.markdown(textwrap.dedent("""
        ### Walmart Store Sales Forecasting — Capstone Project

        **Objective:** Forecast weekly sales for the next 12 weeks across all 45 Walmart stores
        and evaluate model reliability per store.

        **Dataset:** 6,435 weekly records (45 stores × 143 weeks, Feb 2010 – Oct 2012), including
        `Weekly_Sales`, `Holiday_Flag`, `Temperature`, `Fuel_Price`, `CPI`, and `Unemployment`.

        **Model:** SARIMAX(1,1,1)(1,1,1,52) — seasonal order captures the 52-week yearly cycle
        (holiday-driven demand spikes in November/December).

        **Evaluation:** Last 12 weeks of each store's history held out as a test set; MAE, RMSE,
        and MAPE computed per store. Models with MAPE < 10% are rated Excellent, < 20% Good,
        else Needs Improvement.

        **Key EDA findings:**
        - Unemployment and CPI have a weak overall correlation with weekly sales, though a small
          subset of stores are more sensitive to local economic conditions.
        - Clear seasonality: sales peak in November–December due to Thanksgiving/Christmas.
        - Temperature has minimal effect on weekly sales.
        - Large performance gap between best and worst performing stores, suggesting store-level
          inventory planning is more effective than a one-size-fits-all approach.

        Built by Siddu — B.Sc. Mathematics, Statistics & Data Science.

        ---
        **Connect with me:** [GitHub](https://github.com/sidducv0528) · [LinkedIn](https://linkedin.com/in/siddu-data/) · [Kaggle](https://kaggle.com/sidduv0528) · [Email](mailto:sidducv0528@gmail.com)
        """))
