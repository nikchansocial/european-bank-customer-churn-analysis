"""
ECB Customer Intelligence Platform
====================================
Production-grade Streamlit dashboard for European Bank Customer Churn Analysis.

Improvements over v1:
- Fully cached data pipeline (zero redundant computation)
- Plotly-only charts (no seaborn/matplotlib memory leaks)
- Narrative-driven layout: story flows top → bottom
- Insight-first chart titles (answer first, data second)
- Annotated charts with plain-language callouts
- Colour-blind-safe palette with consistent semantic colours
- Clear section summaries after every chart cluster
- Interactive tooltip context on every chart
- Removed duplicate KPI rows and redundant metrics
- Footer with methodology note
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ──────────────────────────────────────────────────
# PAGE CONFIG  (must be the very first st call)
# ──────────────────────────────────────────────────

st.set_page_config(
    page_title="ECB Churn Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "European Bank Customer Churn Analytics — Nikhil Chandrakar"},
)

# ──────────────────────────────────────────────────
# DESIGN TOKENS  — single source of truth
# ──────────────────────────────────────────────────

# Semantic colour palette (WCAG AA contrast on white)
C_CHURN    = "#DC2626"   # red   — churn / danger
C_RETAIN   = "#059669"   # green — retained / safe
C_WARN     = "#D97706"   # amber — warning / medium risk
C_BRAND    = "#1D4ED8"   # blue  — primary brand
C_DARK     = "#0F172A"   # near-black header bg
C_SURFACE  = "#F8FAFC"   # page background
C_CARD     = "#FFFFFF"
C_BORDER   = "#E2E8F0"
C_TEXT     = "#1E293B"
C_MUTED    = "#64748B"

# Plotly layout shared across all charts
_PLOT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="'IBM Plex Sans', sans-serif", color=C_TEXT, size=13),
    margin=dict(l=20, r=20, t=55, b=30),
    title_font_size=15,
    title_font_color=C_TEXT,
    hoverlabel=dict(bgcolor="white", font_size=13, font_color=C_TEXT),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
)

# ──────────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap');

/* ── Base ── */
html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }
.stApp                       { background: #F8FAFC; }
.block-container             { max-width: 1440px; padding-top: 1.5rem; padding-bottom: 3rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"]    { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
[data-testid="stExpander"]   { border: none !important; box-shadow: none !important; background: transparent !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 18px 16px 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
[data-testid="stMetricValue"]     { font-size: 1.75rem !important; font-weight: 600; color: #0F172A; }
[data-testid="stMetricLabel"]     { font-size: 0.8rem !important; color: #64748B; font-weight: 500; letter-spacing: .03em; text-transform: uppercase; }
[data-testid="stMetricDeltaIcon"] { font-size: 0.85rem !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]  { gap: 4px; border-bottom: 2px solid #E2E8F0; }
.stTabs [data-baseweb="tab"]       { font-size: 14px; font-weight: 500; padding: 10px 18px; border-radius: 8px 8px 0 0; }
.stTabs [aria-selected="true"]     { color: #1D4ED8 !important; border-bottom: 2px solid #1D4ED8 !important; }

/* ── Custom components ── */
.page-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%);
    padding: 28px 32px;
    border-radius: 18px;
    margin-bottom: 24px;
    color: white;
}
.page-header h1  { margin: 0 0 6px; font-size: 1.55rem; font-weight: 600; letter-spacing: -.01em; }
.page-header p   { margin: 0; font-size: 0.9rem; opacity: 0.7; }

.section-label   { font-size: 0.72rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: #94A3B8; margin-bottom: 4px; }
.section-title   { font-size: 1.2rem; font-weight: 600; color: #0F172A; margin-bottom: 2px; }
.section-sub     { font-size: 0.875rem; color: #64748B; margin-bottom: 20px; }

.insight-box {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-left: 4px solid #1D4ED8;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 12px 0 20px;
    font-size: 0.9rem;
    color: #1E3A5F;
    line-height: 1.7;
}
.insight-box b   { color: #1D4ED8; }

.warning-box {
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    border-left: 4px solid #D97706;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 12px 0 20px;
    font-size: 0.9rem;
    color: #7C2D12;
    line-height: 1.7;
}

.kpi-hero {
    background: linear-gradient(135deg, #7F1D1D, #991B1B);
    border-radius: 16px;
    padding: 24px 28px;
    color: white;
    margin-bottom: 16px;
}
.kpi-hero .label  { font-size: 0.75rem; opacity: 0.8; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 6px; }
.kpi-hero .value  { font-size: 2.8rem; font-weight: 700; line-height: 1; }
.kpi-hero .sub    { font-size: 0.85rem; opacity: 0.75; margin-top: 6px; }

.action-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 14px;
    height: 100%;
}
.action-card h4  { margin: 0 0 10px; font-size: 0.95rem; font-weight: 600; }
.action-card ul  { margin: 0; padding-left: 18px; font-size: 0.875rem; color: #475569; line-height: 1.9; }

.priority-high   { border-top: 3px solid #DC2626; }
.priority-med    { border-top: 3px solid #D97706; }
.priority-low    { border-top: 3px solid #059669; }

.footnote        { font-size: 0.78rem; color: #94A3B8; margin-top: 4px; }

.risk-pill {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: .04em;
}
.risk-high   { background: #FEE2E2; color: #991B1B; }
.risk-med    { background: #FEF3C7; color: #92400E; }
.risk-low    { background: #D1FAE5; color: #065F46; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────
# DATA LAYER — cached, path-safe
# ──────────────────────────────────────────────────

DATA_PATH = Path(__file__).parent / "data" / "European_Bank.csv"

@st.cache_data(show_spinner="Loading customer data…")
def load_data() -> pd.DataFrame:
    """Load raw CSV and attach all derived columns once."""
    if not DATA_PATH.exists():
        st.error(f"Dataset not found at `{DATA_PATH}`. Please check the data/ folder.")
        st.stop()

    df = pd.read_csv(DATA_PATH)

    # Drop PII-adjacent columns
    df.drop(columns=[c for c in ["Surname", "CustomerId", "RowNumber", "Year"]
                     if c in df.columns], inplace=True)

    # ── Derived segments ──────────────────────────
    df["AgeGroup"] = pd.cut(
        df["Age"],
        bins=[0, 29, 45, 60, 120],
        labels=["Under 30", "30–45", "46–60", "Over 60"],
    )
    df["CreditBand"] = pd.cut(
        df["CreditScore"],
        bins=[299, 579, 669, 739, 850],
        labels=["Poor (300–579)", "Fair (580–669)", "Good (670–739)", "Excellent (740+)"],
    )
    df["TenureGroup"] = pd.cut(
        df["Tenure"],
        bins=[-1, 2, 6, 10],
        labels=["New (0–2 yrs)", "Mid-Term (3–6 yrs)", "Long-Term (7+ yrs)"],
    )
    df["BalanceSegment"] = pd.cut(
        df["Balance"],
        bins=[-1, 0, 50_000, 300_000],
        labels=["Zero balance", "Low (£1–50k)", "High (£50k+)"],
    )
    df["IsHighValue"] = (df["Balance"] >= df["Balance"].quantile(0.75)).astype(int)
    df["NumProducts_Label"] = df["NumOfProducts"].map(
        {1: "1 product", 2: "2 products", 3: "3 products", 4: "4 products"}
    ).fillna("Other")
    df["ChurnLabel"] = df["Exited"].map({0: "Retained", 1: "Churned"})
    df["ActiveLabel"] = df["IsActiveMember"].map({1: "Active", 0: "Inactive"})

    return df


@st.cache_data(show_spinner=False)
def compute_kpis(df: pd.DataFrame) -> dict:
    """Pre-compute all KPIs from the (filtered) DataFrame."""
    churned    = df[df["Exited"] == 1]
    high_value = df[df["IsHighValue"] == 1]
    hv_churned = df[(df["IsHighValue"] == 1) & (df["Exited"] == 1)]

    churn_rate       = df["Exited"].mean() * 100
    hv_churn_rate    = high_value["Exited"].mean() * 100  if len(high_value) else 0
    inactive_churn   = df[df["IsActiveMember"] == 0]["Exited"].mean() * 100
    balance_at_risk  = hv_churned["Balance"].sum() / 1e6
    avg_balance_lost = hv_churned["Balance"].mean() if len(hv_churned) else 0
    hv_lost_count    = len(hv_churned)

    # Risk score: weighted composite (0–100)
    risk_score = min(round(churn_rate * 2 + hv_churn_rate * 0.8), 100)
    risk_label = "HIGH" if risk_score >= 75 else ("MEDIUM" if risk_score >= 45 else "LOW")

    # Top-risk breakdowns
    geo_risk  = df.groupby("Geography")["Exited"].mean().sort_values(ascending=False)
    age_risk  = df.groupby("AgeGroup", observed=True)["Exited"].mean().sort_values(ascending=False)
    prod_risk = df.groupby("NumOfProducts")["Exited"].mean().sort_values(ascending=False)

    return dict(
        churn_rate       = churn_rate,
        hv_churn_rate    = hv_churn_rate,
        inactive_churn   = inactive_churn,
        balance_at_risk  = balance_at_risk,
        avg_balance_lost = avg_balance_lost,
        hv_lost_count    = hv_lost_count,
        total_customers  = len(df),
        total_churned    = int(df["Exited"].sum()),
        risk_score       = risk_score,
        risk_label       = risk_label,
        top_country      = geo_risk.index[0],
        top_country_rate = geo_risk.iloc[0] * 100,
        top_age          = str(age_risk.index[0]),
        top_age_rate     = age_risk.iloc[0] * 100,
        highest_risk_product = int(prod_risk.index[0]),
    )


# ──────────────────────────────────────────────────
# CHART HELPERS — pure functions, no st.* calls
# ──────────────────────────────────────────────────

def _bar(df_agg: pd.DataFrame, x: str, y: str,
         title: str, subtitle: str = "",
         color: str | None = None,
         color_map: dict | None = None,
         color_scale: str | None = None,
         orientation: str = "v",
         benchmark: float | None = None) -> go.Figure:
    """Opinionated bar chart with optional benchmark line."""
    full_title = f"<b>{title}</b><br><sup style='color:#64748B'>{subtitle}</sup>" if subtitle else f"<b>{title}</b>"

    if color_map:
        fig = px.bar(df_agg, x=x, y=y, color=color or x,
                     color_discrete_map=color_map,
                     orientation=orientation,
                     text_auto=".1f")
    elif color_scale:
        fig = px.bar(df_agg, x=x, y=y, color=y,
                     color_continuous_scale=color_scale,
                     orientation=orientation,
                     text_auto=".1f")
    else:
        fig = px.bar(df_agg, x=x, y=y,
                     color_discrete_sequence=[C_BRAND],
                     orientation=orientation,
                     text_auto=".1f")

    if benchmark is not None:
        fig.add_hline(y=benchmark, line_dash="dot", line_color=C_WARN, line_width=1.5,
                      annotation_text=f"  Avg {benchmark:.1f}%",
                      annotation_font_color=C_WARN,
                      annotation_position="top left")

    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{x}</b><br>Churn rate: %{y:.1f}%<extra></extra>")
    fig.update_layout(**_PLOT, title=full_title, yaxis_title="Churn Rate (%)",
                      coloraxis_showscale=False, showlegend=bool(color_map))
    fig.update_yaxes(gridcolor="#F1F5F9", gridwidth=1)
    fig.update_xaxes(showgrid=False)
    return fig


def _heatmap(pivot: pd.DataFrame, title: str, subtitle: str = "") -> go.Figure:
    """Annotated heatmap — pure Plotly (no Matplotlib/Seaborn)."""
    full_title = f"<b>{title}</b><br><sup style='color:#64748B'>{subtitle}</sup>"
    z_vals   = pivot.values.tolist()
    z_text   = [[f"{v:.1f}%" for v in row] for row in pivot.values]

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=[str(c) for c in pivot.columns],
        y=[str(i) for i in pivot.index],
        text=z_text,
        texttemplate="%{text}",
        colorscale=[[0, "#FFF7ED"], [0.5, "#F97316"], [1, "#7F1D1D"]],
        hovertemplate="<b>%{y}</b> in <b>%{x}</b><br>Churn rate: %{text}<extra></extra>",
        showscale=True,
        colorbar=dict(title="Churn %", ticksuffix="%"),
        textfont=dict(size=13, color="white"),
    ))
    fig.update_layout(**_PLOT, title=full_title, height=320)
    return fig


def _waterfall(labels: list, values: list, title: str) -> go.Figure:
    """Waterfall / funnel showing churn decomposition."""
    fig = go.Figure(go.Waterfall(
        name="",
        orientation="v",
        x=labels,
        y=values,
        connector={"line": {"color": C_BORDER}},
        increasing={"marker": {"color": C_CHURN}},
        decreasing={"marker": {"color": C_RETAIN}},
        totals={"marker": {"color": C_BRAND}},
        texttemplate="%{y:.1f}%",
        textposition="outside",
    ))
    fig.update_layout(**_PLOT, title=f"<b>{title}</b>", showlegend=False)
    return fig


def _scatter_quadrant(df: pd.DataFrame) -> go.Figure:
    """Risk quadrant scatter — retained vs churned customers."""
    sample = df.sample(min(2500, len(df)), random_state=42).copy()
    med_bal = sample["Balance"].median()
    med_sal = sample["EstimatedSalary"].median()

    fig = px.scatter(
        sample, x="Balance", y="EstimatedSalary",
        color="ChurnLabel",
        opacity=0.5,
        color_discrete_map={"Retained": C_RETAIN, "Churned": C_CHURN},
        title="<b>Where Are the At-Risk Customers?</b><br>"
              "<sup style='color:#64748B'>Balance vs estimated salary — each dot is one customer</sup>",
        labels={"Balance": "Account Balance (£)", "EstimatedSalary": "Estimated Annual Salary (£)"},
        hover_data={"Age": True, "NumOfProducts": True, "Tenure": True},
    )
    fig.add_vline(x=med_bal, line_dash="dot", line_color="#94A3B8", line_width=1)
    fig.add_hline(y=med_sal, line_dash="dot", line_color="#94A3B8", line_width=1)

    ann_style = dict(showarrow=False, font=dict(size=11, color="#475569"),
                     bgcolor="rgba(255,255,255,0.85)", borderpad=4)
    fig.add_annotation(x=med_bal * 1.6, y=med_sal * 1.65, text="⭐ VIP Zone", **ann_style)
    fig.add_annotation(x=med_bal * 0.3, y=med_sal * 1.65, text="📈 Upsell Zone", **ann_style)
    fig.add_annotation(x=med_bal * 1.6, y=med_sal * 0.35, text="⚠️ High Risk Zone", **ann_style)
    fig.add_annotation(x=med_bal * 0.3, y=med_sal * 0.35, text="🔵 Standard Zone", **ann_style)

    fig.update_traces(marker=dict(size=5))
    fig.update_layout(**_PLOT, height=450, legend_title="Status")
    return fig


def _funnel(df: pd.DataFrame) -> go.Figure:
    """Customer retention funnel by segment depth."""
    segments = {
        "All customers":            df["Exited"].mean() * 100,
        "Germany only":             df[df["Geography"] == "Germany"]["Exited"].mean() * 100,
        "Germany + Age 46–60":      df[(df["Geography"] == "Germany") & (df["AgeGroup"] == "46–60")]["Exited"].mean() * 100,
        "Germany + 46–60 + Inactive": df[
            (df["Geography"] == "Germany") &
            (df["AgeGroup"] == "46–60") &
            (df["IsActiveMember"] == 0)
        ]["Exited"].mean() * 100,
    }
    seg_df = pd.DataFrame(segments.items(), columns=["Segment", "Churn Rate (%)"])
    fig = px.funnel(
        seg_df, x="Churn Rate (%)", y="Segment",
        title="<b>Risk Amplifies at Intersection of Factors</b><br>"
              "<sup style='color:#64748B'>Churn rate climbs as risk factors stack up</sup>",
        color_discrete_sequence=[C_CHURN],
    )
    fig.update_layout(**_PLOT, height=320)
    return fig


def _gauge(score: int, label: str) -> go.Figure:
    colour = C_CHURN if score >= 75 else (C_WARN if score >= 45 else C_RETAIN)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"size": 36, "color": colour}},
        title={"text": "Portfolio Risk Score", "font": {"size": 14, "color": C_MUTED}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": C_BORDER},
            "bar": {"color": colour, "thickness": 0.3},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  45], "color": "#D1FAE5"},
                {"range": [45, 75], "color": "#FEF3C7"},
                {"range": [75, 100], "color": "#FEE2E2"},
            ],
        },
    ))
    fig.update_layout(height=260, margin=dict(l=30, r=30, t=40, b=10),
                      paper_bgcolor="white", font=dict(family="'IBM Plex Sans', sans-serif"))
    return fig


# ──────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────

df_all = load_data()

with st.sidebar:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0F172A,#1E3A5F);
    padding:16px 18px;border-radius:14px;color:white;margin-bottom:16px;">
    <div style="font-size:1rem;font-weight:600;margin-bottom:2px;">🏦 ECB Intelligence</div>
    <div style="font-size:0.78rem;opacity:0.65;">Customer Retention Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Filters")

    with st.expander("🌍 Geography", expanded=True):
        geo_opts = sorted(df_all["Geography"].unique())
        geo = st.multiselect("Country", geo_opts, default=geo_opts, key="geo")

    with st.expander("👤 Customer Profile", expanded=True):
        age_opts = list(df_all["AgeGroup"].cat.categories)
        age = st.multiselect("Age Group", age_opts, default=age_opts, key="age")
        gender = st.radio("Gender", ["All", "Male", "Female"], horizontal=True)
        member = st.radio("Membership", ["All", "Active", "Inactive"], horizontal=True)

    with st.expander("💳 Financials", expanded=False):
        bal_opts = list(df_all["BalanceSegment"].cat.categories)
        bal = st.multiselect("Balance Segment", bal_opts, default=bal_opts, key="bal")
        credit_opts = list(df_all["CreditBand"].cat.categories)
        credit = st.multiselect("Credit Band", credit_opts, default=credit_opts, key="credit")

    st.markdown("---")

    # ── Apply filters ──────────────────────────────
    mask = (
        df_all["Geography"].isin(geo)
        & df_all["AgeGroup"].isin(age)
        & df_all["BalanceSegment"].isin(bal)
        & df_all["CreditBand"].isin(credit)
    )
    if gender != "All":
        mask &= df_all["Gender"] == gender
    if member != "All":
        mask &= df_all["IsActiveMember"] == (1 if member == "Active" else 0)

    df = df_all[mask].copy()

    if df.empty:
        st.warning("No customers match these filters. Adjust above.")
        st.stop()

    kpis = compute_kpis(df)

    # ── Sidebar health summary ──────────────────────
    pill_class = f"risk-{'high' if kpis['risk_label'] == 'HIGH' else 'med' if kpis['risk_label'] == 'MEDIUM' else 'low'}"
    st.markdown(f"""
    <div style="font-size:0.78rem;font-weight:600;color:#94A3B8;
    text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">Portfolio Health</div>
    <span class="risk-pill {pill_class}">{kpis['risk_label']} RISK</span>
    """, unsafe_allow_html=True)
    st.metric("Risk Score",       f"{kpis['risk_score']}/100")
    st.metric("Churn Rate",       f"{kpis['churn_rate']:.1f}%")
    st.metric("Balance at Risk",  f"£{kpis['balance_at_risk']:.1f}M")
    st.caption(f"{len(df):,} customers · {len(geo)} {'country' if len(geo)==1 else 'countries'}")


# ──────────────────────────────────────────────────
# PAGE HEADER
# ──────────────────────────────────────────────────

st.markdown(f"""
<div class="page-header">
  <h1>🏦 ECB Customer Intelligence Platform</h1>
  <p>Executive analytics for customer churn risk &amp; retention strategy &nbsp;·&nbsp;
     Showing <strong style="opacity:0.9">{len(df):,}</strong> customers</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────
# TOP KPI STRIP
# ──────────────────────────────────────────────────

# Hero KPI — the number that matters most
hero, g1, g2 = st.columns([2, 1, 1])

with hero:
    st.markdown(f"""
    <div class="kpi-hero">
      <div class="label">⚠️ Estimated Balance at Risk</div>
      <div class="value">£{kpis['balance_at_risk']:.1f}M</div>
      <div class="sub">Deposits held by high-value customers who have already churned</div>
    </div>
    """, unsafe_allow_html=True)

with g1:
    st.plotly_chart(_gauge(kpis["risk_score"], kpis["risk_label"]),
                    use_container_width=True, key="gauge_top")
with g2:
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.metric("Overall Churn Rate",    f"{kpis['churn_rate']:.1f}%",
              delta=f"{kpis['churn_rate']-20:+.1f}% vs 20% benchmark",
              delta_color="inverse")
    st.metric("High-Value Churn",      f"{kpis['hv_churn_rate']:.1f}%",
              help="Churn rate among customers in the top 25% by balance")
    st.metric("Inactive-Member Churn", f"{kpis['inactive_churn']:.1f}%",
              help="Inactive members churn at a significantly higher rate than active members")
    st.metric("Customers Analysed",    f"{kpis['total_customers']:,}")

st.markdown("---")


# ──────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Overview",
    "👥 Customer Segments",
    "🌍 Geography",
    "💰 Financial Risk",
    "🎯 Action Plan",
])

avg_churn = kpis["churn_rate"]   # used as benchmark line on charts


# ══════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════

with tab1:

    st.markdown('<div class="section-label">Executive Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Who Is Churning, and Why Does It Matter?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">A board-level snapshot of churn exposure across all dimensions.</div>', unsafe_allow_html=True)

    # ── Decomposition funnel ────────────────────────
    st.markdown("#### Risk compounds when factors overlap")
    st.plotly_chart(_funnel(df), use_container_width=True, key="funnel_overview")

    st.markdown(f"""
    <div class="insight-box">
    <b>How to read this:</b> Each row adds one more risk factor.
    The overall churn rate is <b>{kpis['churn_rate']:.1f}%</b>. Among German customers it rises noticeably.
    Among German customers aged 46–60 it rises further. When you add inactive membership on top,
    you reach the highest-risk pocket in the entire portfolio — a segment requiring immediate intervention.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Risk matrix heatmap ─────────────────────────
    st.markdown("#### Age group × geography: where risk is concentrated")

    pivot_ov = (
        df.pivot_table(values="Exited", index="AgeGroup",
                       columns="Geography", aggfunc="mean", observed=True) * 100
    )
    st.plotly_chart(
        _heatmap(pivot_ov,
                 "Churn Rate Heatmap — Age × Country",
                 "Each cell shows % of customers in that group who churned. Darker = more urgent."),
        use_container_width=True, key="heatmap_overview"
    )

    st.markdown(f"""
    <div class="insight-box">
    <b>How to read this:</b> Each cell is the churn rate for customers of that age in that country.
    The darkest cells identify your <b>highest-priority retention targets</b>.
    Germany and the 46–60 age band consistently show the deepest red —
    these two factors together drive a disproportionate share of total attrition.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Active vs Inactive side-by-side ────────────
    st.markdown("#### Inactive members are dramatically more likely to leave")

    act_df = (
        df.groupby(["ActiveLabel", "Geography"])["Exited"]
        .mean().reset_index()
    )
    act_df["Exited"] *= 100

    fig_act = px.bar(
        act_df, x="Geography", y="Exited", color="ActiveLabel",
        barmode="group", text_auto=".1f",
        color_discrete_map={"Active": C_RETAIN, "Inactive": C_CHURN},
        title="<b>Inactive members churn 2–3× more than active members</b><br>"
              "<sup style='color:#64748B'>Churn rate by membership status and country</sup>",
        labels={"Exited": "Churn Rate (%)", "ActiveLabel": "Status"},
    )
    fig_act.add_hline(y=avg_churn, line_dash="dot", line_color=C_WARN, line_width=1.5,
                      annotation_text=f"  Average {avg_churn:.1f}%",
                      annotation_font_color=C_WARN,
                      annotation_position="top left")
    fig_act.update_layout(**_PLOT)
    fig_act.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(fig_act, use_container_width=True, key="active_vs_inactive")

    st.markdown("""
    <div class="insight-box">
    <b>Key takeaway:</b> Re-engaging inactive members is one of the highest-return actions available.
    The cost of a targeted re-engagement campaign is far lower than acquiring a replacement customer.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# TAB 2 — CUSTOMER SEGMENTS
# ══════════════════════════════════════════════════

with tab2:

    st.markdown('<div class="section-label">Customer Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Which Customer Profiles Are at Highest Risk?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Segment-level churn rates to prioritise outreach.</div>', unsafe_allow_html=True)

    # ── Age ─────────────────────────────────────────
    age_data = (
        df.groupby("AgeGroup", observed=True)["Exited"]
        .mean().reset_index()
    )
    age_data["Exited"] *= 100

    fig_age = _bar(
        age_data, x="AgeGroup", y="Exited",
        title="Customers aged 46–60 churn at nearly twice the portfolio rate",
        subtitle="Churn rate by age group — benchmark line shows portfolio average",
        color_scale="OrRd",
        benchmark=avg_churn,
    )
    st.plotly_chart(fig_age, use_container_width=True, key="age_churn")

    st.markdown(f"""
    <div class="insight-box">
    <b>Why this matters:</b> The 46–60 cohort is typically a bank's highest-balance segment.
    Losing them is doubly damaging — high churn rate <em>and</em> high average balance.
    Tailored retention packages (preferential rates, dedicated relationship managers) should target this group first.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Gender and credit quality")

    g_col1, g_col2 = st.columns(2)

    gender_data = (
        df.groupby("Gender")["Exited"]
        .mean().reset_index()
    )
    gender_data["Exited"] *= 100
    fig_gen = _bar(
        gender_data, x="Gender", y="Exited",
        title="Female customers churn more often",
        subtitle="Churn rate by gender",
        color_map={"Male": C_BRAND, "Female": C_CHURN},
        color="Gender",
        benchmark=avg_churn,
    )
    g_col1.plotly_chart(fig_gen, use_container_width=True, key="gender_churn")

    credit_data = (
        df.groupby("CreditBand", observed=True)["Exited"]
        .mean().reset_index()
    )
    credit_data["Exited"] *= 100
    fig_credit = _bar(
        credit_data, x="CreditBand", y="Exited",
        title="Churn risk does not track credit quality",
        subtitle="Churn rate by credit score band — counterintuitive finding",
        color_scale="Blues",
        benchmark=avg_churn,
    )
    g_col2.plotly_chart(fig_credit, use_container_width=True, key="credit_churn")

    st.markdown("""
    <div class="insight-box">
    <b>Counterintuitive finding:</b> Credit quality has little predictive power for churn.
    Even customers with excellent credit scores leave at rates close to the portfolio average.
    This suggests churn is driven by <em>engagement and satisfaction</em> rather than financial distress.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Products and tenure")

    p_col1, p_col2 = st.columns(2)

    prod_data = (
        df.groupby("NumProducts_Label", observed=True)["Exited"]
        .mean().reset_index()
    )
    prod_data["Exited"] *= 100
    # Sort by product count for readability
    prod_data = prod_data.sort_values("NumProducts_Label")
    fig_prod = _bar(
        prod_data, x="NumProducts_Label", y="Exited",
        title="3–4 product customers churn at an extreme rate",
        subtitle="Churn rate by number of products held — the 'over-sold' effect",
        color_scale="OrRd",
        benchmark=avg_churn,
    )
    p_col1.plotly_chart(fig_prod, use_container_width=True, key="product_churn")

    tenure_data = (
        df.groupby("TenureGroup", observed=True)["Exited"]
        .mean().reset_index()
    )
    tenure_data["Exited"] *= 100
    fig_ten = _bar(
        tenure_data, x="TenureGroup", y="Exited",
        title="Tenure does not strongly protect against churn",
        subtitle="Churn rate by years with the bank — long tenure does not guarantee loyalty",
        color_scale="Blues",
        benchmark=avg_churn,
    )
    p_col2.plotly_chart(fig_ten, use_container_width=True, key="tenure_churn")

    st.markdown("""
    <div class="warning-box">
    <b>⚠️ The 3–4 product spike:</b> Customers with 3 or 4 products have dramatically higher churn.
    This is a classic sign of over-selling — customers were sold products they didn't need
    and are now leaving as a result. Review the product bundling strategy for this segment.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Age × gender interaction")

    ag_data = (
        df.groupby(["AgeGroup", "Gender"], observed=True)["Exited"]
        .mean().reset_index()
    )
    ag_data["Exited"] *= 100
    fig_ag = px.bar(
        ag_data, x="AgeGroup", y="Exited", color="Gender",
        barmode="group", text_auto=".1f",
        color_discrete_map={"Male": C_BRAND, "Female": C_CHURN},
        title="<b>Female customers aged 46–60 are the single highest-risk sub-segment</b><br>"
              "<sup style='color:#64748B'>Churn rate by age group and gender combined</sup>",
        labels={"Exited": "Churn Rate (%)", "AgeGroup": "Age Group"},
    )
    fig_ag.add_hline(y=avg_churn, line_dash="dot", line_color=C_WARN, line_width=1.5,
                     annotation_text=f"  Average {avg_churn:.1f}%",
                     annotation_font_color=C_WARN, annotation_position="top left")
    fig_ag.update_layout(**_PLOT)
    fig_ag.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(fig_ag, use_container_width=True, key="age_gender_churn")


# ══════════════════════════════════════════════════
# TAB 3 — GEOGRAPHIC INTELLIGENCE
# ══════════════════════════════════════════════════

with tab3:

    st.markdown('<div class="section-label">Geographic Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Germany Is the Critical Market</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Understanding where churn is geographically concentrated.</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    # Country ranking
    geo_rank = (
        df.groupby("Geography")["Exited"]
        .agg(churn_rate=("mean"), n=("count"))
        .reset_index()
    )
    geo_rank["churn_rate"] *= 100
    geo_rank = geo_rank.sort_values("churn_rate", ascending=True)

    fig_geo = px.bar(
        geo_rank, y="Geography", x="churn_rate",
        orientation="h", text_auto=".1f",
        color="churn_rate",
        color_continuous_scale=[[0, "#D1FAE5"], [0.5, "#FEF3C7"], [1, "#FEE2E2"]],
        title="<b>Germany leads all markets in churn rate</b><br>"
              "<sup style='color:#64748B'>Churn rate by country — horizontal view aids comparison</sup>",
        labels={"churn_rate": "Churn Rate (%)", "Geography": ""},
    )
    fig_geo.add_vline(x=avg_churn, line_dash="dot", line_color=C_WARN, line_width=1.5,
                      annotation_text=f"  Avg {avg_churn:.1f}%",
                      annotation_font_color=C_WARN, annotation_position="top left")
    fig_geo.update_layout(**_PLOT, coloraxis_showscale=False, height=280)
    fig_geo.update_traces(textposition="outside", cliponaxis=False,
                          hovertemplate="<b>%{y}</b><br>Churn: %{x:.1f}%<br>Customers: %{customdata[0]:,}<extra></extra>",
                          customdata=geo_rank[["n"]].values)
    col_a.plotly_chart(fig_geo, use_container_width=True, key="geo_ranking")

    # Customer volume vs churn rate bubble
    geo_bubble = (
        df.groupby("Geography")
        .agg(churn_rate=("Exited", "mean"),
             total=("Exited", "count"),
             balance_risk=("Balance", lambda x: x[df.loc[x.index, "Exited"] == 1].sum() / 1e6))
        .reset_index()
    )
    geo_bubble["churn_rate"] *= 100

    fig_bubble = px.scatter(
        geo_bubble, x="churn_rate", y="balance_risk",
        size="total", color="Geography",
        text="Geography",
        title="<b>Germany: highest churn AND highest balance exposure</b><br>"
              "<sup style='color:#64748B'>Bubble size = number of customers · Position = risk × financial impact</sup>",
        labels={"churn_rate": "Churn Rate (%)", "balance_risk": "Balance at Risk (£M)"},
        color_discrete_sequence=[C_BRAND, C_CHURN, C_WARN],
    )
    fig_bubble.update_traces(textposition="top center")
    fig_bubble.update_layout(**_PLOT, showlegend=False, height=280)
    col_b.plotly_chart(fig_bubble, use_container_width=True, key="geo_bubble")

    st.markdown(f"""
    <div class="insight-box">
    <b>Germany is the priority market for two independent reasons:</b>
    it has the highest churn <em>rate</em> (top-left chart) <em>and</em> the highest
    balance at risk (bubble chart, upper-right quadrant). France and Spain should still be monitored,
    but retention resources should be concentrated in Germany first.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Country × age group risk matrix")

    pivot_geo = (
        df.pivot_table(values="Exited", index="AgeGroup",
                       columns="Geography", aggfunc="mean", observed=True) * 100
    )
    st.plotly_chart(
        _heatmap(pivot_geo,
                 "Germany + Age 46–60 is the highest-risk combination",
                 "Churn rate (%) by age group and country. Darker cells = higher urgency."),
        use_container_width=True, key="geo_heatmap"
    )

    st.markdown("---")
    st.markdown("#### Gender breakdown by country")

    gg = (
        df.groupby(["Geography", "Gender"])["Exited"]
        .mean().reset_index()
    )
    gg["Exited"] *= 100
    fig_gg = px.bar(
        gg, x="Geography", y="Exited", color="Gender",
        barmode="group", text_auto=".1f",
        color_discrete_map={"Male": C_BRAND, "Female": C_CHURN},
        title="<b>Female customers churn more in every country</b><br>"
              "<sup style='color:#64748B'>Churn rate by country and gender</sup>",
        labels={"Exited": "Churn Rate (%)", "Geography": "Country"},
    )
    fig_gg.add_hline(y=avg_churn, line_dash="dot", line_color=C_WARN, line_width=1.5)
    fig_gg.update_layout(**_PLOT)
    fig_gg.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(fig_gg, use_container_width=True, key="geo_gender")


# ══════════════════════════════════════════════════
# TAB 4 — FINANCIAL RISK
# ══════════════════════════════════════════════════

with tab4:

    st.markdown('<div class="section-label">Financial Exposure Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Quantifying What Is at Stake</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Translating churn rates into pounds and pence.</div>', unsafe_allow_html=True)

    # KPIs
    fin1, fin2, fin3, fin4 = st.columns(4)
    fin1.metric("Balance at Risk",          f"£{kpis['balance_at_risk']:.2f}M",
                help="Total balance held by high-value customers who have churned")
    fin2.metric("High-Value Customers Lost", f"{kpis['hv_lost_count']:,}",
                help="Count of top-quartile-balance customers who have already churned")
    fin3.metric("Avg Balance Per Lost VIP",  f"£{kpis['avg_balance_lost']:,.0f}",
                help="Average account balance of a churned high-value customer")
    fin4.metric("High-Value Churn Rate",     f"{kpis['hv_churn_rate']:.1f}%",
                help="% of top-25%-balance customers who have churned")

    st.markdown("---")

    col_f1, col_f2 = st.columns(2)

    # Balance segment risk
    bal_data = (
        df.groupby("BalanceSegment", observed=True)["Exited"]
        .mean().reset_index()
    )
    bal_data["Exited"] *= 100
    fig_bal = _bar(
        bal_data, x="BalanceSegment", y="Exited",
        title="High-balance customers churn at elevated rates",
        subtitle="Churn rate by account balance tier — the 'value paradox'",
        color_map={"Zero balance": "#CBD5E1", "Low (£1–50k)": C_WARN, "High (£50k+)": C_CHURN},
        color="BalanceSegment",
        benchmark=avg_churn,
    )
    col_f1.plotly_chart(fig_bal, use_container_width=True, key="bal_seg")

    # HV churn by geography
    hv_geo = (
        df[df["IsHighValue"] == 1]
        .groupby("Geography")["Exited"]
        .mean().reset_index()
    )
    hv_geo["Exited"] *= 100
    fig_hvg = _bar(
        hv_geo, x="Geography", y="Exited",
        title="Germany: highest VIP churn risk by country",
        subtitle="Churn rate among top-quartile-balance customers only",
        color_scale="OrRd",
        benchmark=kpis["hv_churn_rate"],
    )
    col_f2.plotly_chart(fig_hvg, use_container_width=True, key="hv_geo")

    st.markdown(f"""
    <div class="warning-box">
    <b>⚠️ The value paradox:</b> High-balance customers churn <em>more</em> than low-balance customers.
    This is counterintuitive — these customers have the most to lose by switching, yet they leave.
    This strongly suggests service quality, not product selection, is the root cause.
    These customers have options and will exercise them if not actively retained.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Customer risk quadrant — individual customer view")
    st.markdown('<p class="footnote">Hover over any dot to see customer details. 2,500-customer sample.</p>', unsafe_allow_html=True)

    st.plotly_chart(_scatter_quadrant(df), use_container_width=True, key="scatter_quad")

    st.markdown("""
    <div class="insight-box">
    <b>How to read the quadrants:</b><br>
    <b>⭐ VIP Zone</b> (top right) — high balance AND high salary. These are your most valuable customers.
    Red dots here represent the highest-priority retention cases.<br>
    <b>⚠️ High Risk Zone</b> (bottom right) — high balance but lower salary. May be managing money carefully; any fee increases could trigger exit.<br>
    <b>📈 Upsell Zone</b> (top left) — high salary but low balance. Opportunity to deepen the relationship.<br>
    <b>🔵 Standard Zone</b> (bottom left) — lower balance and salary. Monitor but lower financial impact per churned customer.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Balance distribution — churned vs retained customers")

    fig_dist = px.histogram(
        df, x="Balance", color="ChurnLabel",
        barmode="overlay", nbins=50, opacity=0.7,
        color_discrete_map={"Retained": C_RETAIN, "Churned": C_CHURN},
        title="<b>Churned customers skew towards higher balances</b><br>"
              "<sup style='color:#64748B'>Distribution of account balance — churned vs retained</sup>",
        labels={"Balance": "Account Balance (£)", "ChurnLabel": "Status"},
    )
    fig_dist.update_layout(**_PLOT)
    fig_dist.update_traces(hovertemplate="Balance: £%{x:,.0f}<br>Count: %{y}<extra></extra>")
    st.plotly_chart(fig_dist, use_container_width=True, key="bal_dist")


# ══════════════════════════════════════════════════
# TAB 5 — ACTION PLAN
# ══════════════════════════════════════════════════

with tab5:

    st.markdown('<div class="section-label">Retention Strategy</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What Should the Bank Do Next?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Prioritised, evidence-based actions derived directly from the data.</div>', unsafe_allow_html=True)

    # ── Immediate alerts ────────────────────────────
    st.error(
        f"🚨  **Immediate priorities (this week):**  "
        f"(1) Deploy relationship managers to {kpis['top_country']} "
        f"({kpis['top_country_rate']:.1f}% churn rate).  "
        f"(2) Identify and personally contact all high-value customers in the 46–60 age band.  "
        f"(3) Protect £{kpis['balance_at_risk']:.1f}M in deposits.  "
        f"(4) Launch inactive-member re-engagement within 14 days."
    )

    st.markdown("---")

    # ── Priority action cards ───────────────────────
    st.markdown("#### Priority action matrix")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"""
        <div class="action-card priority-high">
          <h4 style="color:{C_CHURN}">🔴 Critical — Immediate Action</h4>
          <b>Germany VIP Retention Program</b>
          <ul>
            <li>Highest churn market at {kpis['top_country_rate']:.1f}% — above all others</li>
            <li>46–60 age group amplifies risk 2×</li>
            <li>Assign dedicated relationship managers to top-250 balance holders</li>
            <li>Conduct exit-interview analysis on Germany churned customers</li>
            <li>Review fee structures vs competitor benchmarks in German market</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="action-card priority-high">
          <h4 style="color:{C_CHURN}">🔴 Critical — Financial Risk</h4>
          <b>High-Value Customer Shield</b>
          <ul>
            <li>{kpis['hv_lost_count']:,} top-quartile customers already churned</li>
            <li>Average balance lost per customer: £{kpis['avg_balance_lost']:,.0f}</li>
            <li>Introduce a VIP banking tier with premium benefits</li>
            <li>Quarterly proactive outreach calls for customers with £50k+ balance</li>
            <li>Offer preferential rates to at-risk VIP customers before they request exit</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="action-card priority-med">
          <h4 style="color:{C_WARN}">🟡 High Impact — 30 Days</h4>
          <b>Inactive Member Recovery Campaign</b>
          <ul>
            <li>Inactive members churn at {kpis['inactive_churn']:.1f}% — highest of any segment</li>
            <li>Launch automated re-engagement email series</li>
            <li>Waive dormancy fees for first 6 months after re-activation</li>
            <li>Offer cashback on first 3 transactions post re-engagement</li>
            <li>Create "Why did you stop?" survey for recently inactive members</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="action-card priority-low">
          <h4 style="color:{C_RETAIN}">🟢 Quick Win — Product Strategy</h4>
          <b>Fix the Over-Selling Problem</b>
          <ul>
            <li>3–4 product customers churn at extreme rates — over-selling signature</li>
            <li>Audit all customers with 3+ products for product-need fit</li>
            <li>Introduce a satisfaction check-in at 90-day mark after product #3</li>
            <li>Train advisors on value-fit assessment before cross-selling</li>
            <li>Consider simplified product bundles with clear value propositions</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Strategic roadmap ───────────────────────────
    st.markdown("#### Strategic roadmap — next 180 days")

    r1, r2, r3 = st.columns(3)

    r1.markdown(f"""
    <div class="action-card">
      <h4>📍 30 Days — Stop the Bleeding</h4>
      <ul>
        <li>Launch Germany retention programme</li>
        <li>Identify top 500 at-risk VIP customers</li>
        <li>Begin inactive-member re-engagement</li>
        <li>Audit 3–4 product customers</li>
        <li>Set up weekly churn monitoring dashboard</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    r2.markdown(f"""
    <div class="action-card">
      <h4>📍 90 Days — Structural Fix</h4>
      <ul>
        <li>Redesign loyalty programme for 46–60 segment</li>
        <li>Deploy VIP banking tier with premium benefits</li>
        <li>Introduce female-focused product journeys</li>
        <li>Begin competitor fee benchmarking in Germany</li>
        <li>Build churn prediction model (ML phase)</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    r3.markdown(f"""
    <div class="action-card">
      <h4>📍 180 Days — Sustainable Retention</h4>
      <ul>
        <li>Launch personalised banking recommendations</li>
        <li>Real-time churn alert system for advisors</li>
        <li>Customer lifetime value (CLV) scoring</li>
        <li>Portfolio optimisation — reduce over-sold segments</li>
        <li>Expand predictive model to all markets</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Expected impact ─────────────────────────────
    st.markdown("#### Expected impact if all actions are executed")

    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Target Churn Reduction", "8–12 pp",
              help="Percentage point reduction if all priority actions are completed")
    i2.metric("Balance Protected",      f"£{kpis['balance_at_risk']:.1f}M",
              help="Estimated deposits recoverable through VIP programme")
    i3.metric("VIP Customers Saved",    f"≈{int(kpis['hv_lost_count']*0.4):,}",
              help="Estimated high-value customers retained at 40% programme success rate")
    i4.metric("Retention Priority",     "Critical",
              delta="Act within 30 days", delta_color="off")

    st.success(
        f"**Summary finding:** Current overall churn stands at **{kpis['churn_rate']:.1f}%**. "
        f"An estimated **£{kpis['balance_at_risk']:.1f}M** in deposits is already at risk. "
        f"Germany, customers aged 46–60, inactive members, and customers with 3+ products "
        f"represent the four highest-urgency retention segments. "
        f"Protecting high-value customers in Germany should be the single first action — "
        f"it addresses the highest financial risk with the most targeted possible intervention."
    )

# ──────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────

st.markdown("---")
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            flex-wrap:wrap;gap:12px;padding:8px 0;">
  <div>
    <span style="font-size:0.9rem;font-weight:600;color:#0F172A;">
      ECB Customer Intelligence Platform
    </span><br>
    <span style="font-size:0.78rem;color:#94A3B8;">
      Developed by Nikhil Chandrakar · PGDM Finance &amp; Business Analytics
    </span>
  </div>
  <div style="font-size:0.75rem;color:#94A3B8;text-align:right;line-height:1.7;">
    Dataset: 10,000 synthetic European bank customers ·
    Showing {len(df):,} after filters<br>
    High-value = top 25% by balance · Benchmark = 20% industry churn estimate
  </div>
</div>
""", unsafe_allow_html=True)
