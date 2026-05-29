import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="ECB Customer Intelligence Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# DESIGN SYSTEM
# ==================================================

PRIMARY = "#0F172A"
ACCENT = "#2563EB"

SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"

BACKGROUND = "#F8FAFC"
CARD = "#FFFFFF"
BORDER = "#E2E8F0"

TEXT = "#1E293B"
SUBTEXT = "#64748B"

# ==================================================
# GLOBAL CSS
# ==================================================

st.markdown("""
<style>

/* Main App */

.stApp{
    background-color:#F8FAFC;
}

/* Container */

.block-container{
    max-width:1450px;
    padding-top:1rem;
    padding-bottom:2rem;
}

/* Sidebar */

[data-testid="stSidebar"]{
    background:white;
    border-right:1px solid #E2E8F0;
}

[data-testid="stExpander"]{
    border:none !important;
    box-shadow:none !important;
    background:transparent !important;
}

/* Metric Cards */

[data-testid="metric-container"]{
    background:white;
    border:1px solid #E2E8F0;
    padding:15px;
    border-radius:16px;
    box-shadow:0px 2px 6px rgba(0,0,0,0.05);
}

/* Tabs */

.stTabs [data-baseweb="tab"]{
    font-size:15px;
    font-weight:600;
}

/* Headers */

.section-header{
    font-size:24px;
    font-weight:700;
    color:#0F172A;
    margin-bottom:5px;
}

.section-sub{
    color:#64748B;
    font-size:14px;
    margin-bottom:20px;
}

.insight-banner{
    background:linear-gradient(
        135deg,
        #0F172A,
        #1E293B
    );

    color:white;
    padding:24px;
    border-radius:18px;
    margin-top:15px;
    margin-bottom:25px;
}

.priority-card{
    background:white;
    border:1px solid #E2E8F0;
    border-radius:16px;
    padding:20px;
    margin-bottom:15px;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# DATA
# ==================================================

@st.cache_data
def load_data():

    df = pd.read_csv("data/European_Bank.csv")

    df.drop(
        columns=[
            "Surname",
            "CustomerId",
            "Year"
        ],
        inplace=True
    )

    df["AgeGroup"] = pd.cut(
        df["Age"],
        bins=[0,29,45,60,120],
        labels=[
            "<30",
            "30-45",
            "46-60",
            "60+"
        ]
    )

    df["CreditBand"] = pd.cut(
        df["CreditScore"],
        bins=[299,579,669,739,850],
        labels=[
            "Low",
            "Medium",
            "High",
            "Very High"
        ]
    )

    df["TenureGroup"] = pd.cut(
        df["Tenure"],
        bins=[-1,2,6,10],
        labels=[
            "New",
            "Mid-Term",
            "Long-Term"
        ]
    )

    df["BalanceSegment"] = pd.cut(
        df["Balance"],
        bins=[-1,0,50000,300000],
        labels=[
            "Zero",
            "Low",
            "High"
        ]
    )

    threshold = df["Balance"].quantile(0.75)

    df["IsHighValue"] = (
        df["Balance"] >= threshold
    ).astype(int)

    return df


df = load_data()

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0F172A,#2563EB);
    padding:18px;border-radius:16px;color:white;">
    <h3 style="margin:0;">🏦 ECB Intelligence</h3>
    <p style="margin:4px 0 0 0;">Executive Retention Platform</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚡ Quick Filters")

    with st.expander("🌍 Geography", expanded=True):
        geo = st.multiselect(
            "Country",
            df["Geography"].unique(),
            default=list(df["Geography"].unique())
        )

    with st.expander("👥 Customer Profile", expanded=True):
        age = st.multiselect(
            "Age Group",
            df["AgeGroup"].unique(),
            default=list(df["AgeGroup"].unique())
        )
        gender = st.radio("Gender", ["All","Male","Female"])
        member = st.radio("Member Status", ["All","Active","Inactive"])

    with st.expander("💰 Financial", expanded=False):
        balance_seg = st.multiselect(
            "Balance Segment",
            df["BalanceSegment"].unique(),
            default=list(df["BalanceSegment"].unique())
        )

    st.markdown("---")
    st.markdown("### 📊 Dataset")
    st.caption("10,000 Customers")
    st.caption("France • Germany • Spain")


# ==================================================
# FILTERING
# ==================================================

mask = (

    df["Geography"].isin(geo)

    &

    df["AgeGroup"].isin(age)

    &

    df["BalanceSegment"].isin(balance_seg)

)

if gender != "All":
    mask &= (
        df["Gender"] == gender
    )

if member != "All":

    mask &= (
        df["IsActiveMember"]
        ==
        (
            1
            if member == "Active"
            else 0
        )
    )

filtered = df[mask]

# ==================================================
# KPI CALCULATIONS
# ==================================================

churn_rate = (
    filtered["Exited"].mean() * 100
)

total_lost = int(
    filtered["Exited"].sum()
)

high_value_churn = (
    filtered[
        filtered["IsHighValue"] == 1
    ]["Exited"].mean()
    * 100
)

balance_risk = (

    filtered[
        (filtered["Exited"] == 1)
        &
        (filtered["IsHighValue"] == 1)
    ]["Balance"]

    .sum()

    / 1e6

)

inactive_churn = (

    filtered[
        filtered["IsActiveMember"] == 0
    ]["Exited"]

    .mean()

    * 100

)

# ==================================================
# PHASE 3 EXECUTIVE INTELLIGENCE
# ==================================================

risk_score = min(
    round((churn_rate * 2) + (high_value_churn * 0.8)),
    100
)

if risk_score >= 75:
    risk_label = "HIGH"
elif risk_score >= 50:
    risk_label = "MEDIUM"
else:
    risk_label = "LOW"

geo_risk = filtered.groupby("Geography")["Exited"].mean().sort_values(ascending=False)
top_country = geo_risk.index[0]
top_country_rate = geo_risk.iloc[0] * 100

age_risk = filtered.groupby("AgeGroup", observed=True)["Exited"].mean().sort_values(ascending=False)
top_age = age_risk.index[0]
top_age_rate = age_risk.iloc[0] * 100

portfolio_churn = df["Exited"].mean() * 100
filter_delta = churn_rate - portfolio_churn

industry_benchmark = 15

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🎯 Portfolio Health")
    st.metric("Risk Score", f"{risk_score}/100")
    st.metric("Current Churn", f"{churn_rate:.1f}%")
    st.metric("Balance At Risk", f"£{balance_risk:.1f}M")

    st.markdown("### 🔍 Current View")
    st.caption(f"Customers: {len(filtered):,}")
    st.caption(f"Countries: {len(geo)} selected")
    st.caption(f"Risk Level: {risk_label}")

    st.markdown("### ⚡ Quick Actions")
    st.button("Reset Filters", disabled=True)
    st.button("High Risk View", disabled=True)
    st.button("High Value Customers", disabled=True)


# ==================================================
# HEADER
# ==================================================

st.markdown("""
<div style="
background:white;
padding:28px;
border-radius:18px;
border:1px solid #E2E8F0;
">

<h1 style="
margin-bottom:0;
color:#0F172A;
">
🏦 ECB Customer Intelligence Platform
</h1>

<p style="
color:#64748B;
margin-top:8px;
">
Executive Analytics for Customer Churn Risk & Retention Strategy
</p>

</div>
""", unsafe_allow_html=True)

st.write("")


# ==================================================
# HERO KPI
# ==================================================

st.markdown(f"""
<div style="
background:linear-gradient(135deg,#0F172A,#1E293B);
padding:28px;
border-radius:18px;
margin-bottom:20px;
color:white;
">
<div style="font-size:14px;opacity:0.8;">FINANCIAL EXPOSURE</div>
<div style="font-size:52px;font-weight:700;margin-top:5px;">
£{balance_risk:.1f}M
</div>
<div style="font-size:16px;opacity:0.85;">Balance At Risk</div>
</div>
""", unsafe_allow_html=True)

k1,k2,k3,k4 = st.columns(4)
k1.metric("Churn Rate", f"{churn_rate:.1f}%")
k2.metric("High Value Churn", f"{high_value_churn:.1f}%")
k3.metric("Inactive Churn", f"{inactive_churn:.1f}%")
k4.metric("Customers Analysed", f"{len(filtered):,}")


st.markdown("### 🎯 Portfolio Health Score")

gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={"text":"Portfolio Health"},
        gauge={
            "axis":{"range":[0,100]},
            "bar":{"color":"#2563EB"},
            "steps":[
                {"range":[0,50],"color":"#DCFCE7"},
                {"range":[50,75],"color":"#FEF3C7"},
                {"range":[75,100],"color":"#FEE2E2"}
            ]
        }
    )
)
gauge.update_layout(height=350, margin=dict(l=20,r=20,t=40,b=20), font=dict(size=18))
st.plotly_chart(gauge, width="stretch", key="risk_gauge")

r1,r2,r3,r4 = st.columns(4)
r1.metric("Highest Risk Country", top_country, f"{top_country_rate:.1f}%")
r2.metric("Highest Risk Age Group", str(top_age), f"{top_age_rate:.1f}%")
r3.metric("Churn vs Benchmark", f"{churn_rate:.1f}%", f"{churn_rate-industry_benchmark:+.1f}%")
r4.metric("Filter Impact", f"{filter_delta:+.1f}%")

# ==================================================
# EXECUTIVE INSIGHT
# ==================================================

st.markdown(f"""
<div class="insight-banner">

<h3>
🤖 AI Executive Briefing
</h3>

<h4>Risk Level</h4>
<b>{risk_label}</b><br><br>

<h4>Primary Driver</h4>
{top_country} ({top_country_rate:.1f}%)<br><br>

<h4>Secondary Driver</h4>
{top_age} ({top_age_rate:.1f}%)<br><br>

<h4>Financial Exposure</h4>
£{balance_risk:.1f}M<br><br>

<h4>Recommended Action</h4>
Protect high-value customers in {top_country} immediately.

</div>
""", unsafe_allow_html=True)

st.markdown("### Strategic Findings")

f1,f2,f3 = st.columns(3)
f1.metric("🌍 Highest Risk Geography", top_country, f"{top_country_rate:.1f}%")
f2.metric("👥 Highest Risk Segment", str(top_age), f"{top_age_rate:.1f}%")
f3.metric("💰 Financial Exposure", f"£{balance_risk:.1f}M")

# ==================================================
# TABS
# ==================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([

    "📊 Executive Overview",

    "👥 Customer Intelligence",

    "🌍 Geographic Intelligence",

    "💰 Financial Exposure",

    "🎯 Action Center"

])

PLOT_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(
        color=TEXT
    ),
    margin=dict(
        l=20,
        r=20,
        t=50,
        b=20
    )
)

# ==================================================
# TAB 1 — EXECUTIVE OVERVIEW
# ==================================================

with tab1:

    st.markdown(
        '<div class="section-header">Executive Risk Overview</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-sub">Board-level summary of customer churn exposure.</div>',
        unsafe_allow_html=True
    )

    # Heatmap First (Strongest Chart)

    st.subheader("🔥 Age × Geography Risk Matrix")

    pivot = filtered.pivot_table(
        values="Exited",
        index="AgeGroup",
        columns="Geography",
        aggfunc="mean",
        observed=True
    ) * 100

    fig_hm, ax = plt.subplots(figsize=(12,5))

    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        linewidths=.5,
        cbar_kws={
            "label":"Churn Rate (%)"
        },
        ax=ax
    )

    ax.set_xlabel("")
    ax.set_ylabel("")

    st.pyplot(fig_hm)

    st.divider()

    st.markdown(f"""
<div style="background:#EFF6FF;padding:24px;border-radius:16px;border:1px solid #BFDBFE;">
<h4 style="margin-top:0;">Executive Summary</h4>

        • Overall churn currently stands at {churn_rate:.1f}%

        • Estimated balance exposure equals £{balance_risk:.1f}M

        • High-value customer churn rate is {high_value_churn:.1f}%

        • Inactive customers remain significantly more vulnerable than active members.</div>""", unsafe_allow_html=True)

# ==================================================
# TAB 2 — CUSTOMER INTELLIGENCE
# ==================================================

with tab2:

    st.markdown(
        '<div class="section-header">Customer Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-sub">Identify who is most likely to leave.</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)

    # AGE ANALYSIS

    age_data = (
        filtered
        .groupby("AgeGroup", observed=True)["Exited"]
        .mean()
        .reset_index()
    )

    age_data["Exited"] *= 100

    fig3 = px.bar(
        age_data,
        x="AgeGroup",
        y="Exited",
        text_auto=".1f",
        color="Exited",
        color_continuous_scale="Reds",
        title="Churn by Age Group"
    )

    fig3.update_layout(**PLOT_LAYOUT)

    c1.plotly_chart(
        fig3,
        width="stretch",
        key="age_churn"
    )

    # GENDER ANALYSIS
    # PIE CHART REMOVED

    gender_data = (
        filtered
        .groupby("Gender")["Exited"]
        .mean()
        .reset_index()
    )

    gender_data["Exited"] *= 100

    fig4 = px.bar(
        gender_data,
        x="Gender",
        y="Exited",
        text_auto=".1f",
        color="Gender",
        color_discrete_map={
            "Male":ACCENT,
            "Female":DANGER
        },
        title="Gender Churn Comparison"
    )

    fig4.update_layout(**PLOT_LAYOUT)

    c2.plotly_chart(
        fig4,
        width="stretch",
        key="gender_churn"
    )

    st.divider()

    # AGE x GENDER

    age_gender = (
        filtered
        .groupby(
            ["AgeGroup","Gender"],
            observed=True
        )["Exited"]
        .mean()
        .reset_index()
    )

    age_gender["Exited"] *= 100

    fig5 = px.bar(
        age_gender,
        x="AgeGroup",
        y="Exited",
        color="Gender",
        barmode="group",
        text_auto=".1f",
        color_discrete_map={
            "Male":ACCENT,
            "Female":DANGER
        },
        title="Age × Gender Churn Analysis"
    )

    fig5.update_layout(**PLOT_LAYOUT)

    st.plotly_chart(
        fig5,
        width="stretch",
        key="age_gender"
    )

    st.divider()

    left, right = st.columns(2)

    # PRODUCTS

    prod_data = (
        filtered
        .groupby("NumOfProducts")["Exited"]
        .mean()
        .reset_index()
    )

    prod_data["Exited"] *= 100

    fig6 = px.bar(
        prod_data,
        x="NumOfProducts",
        y="Exited",
        text_auto=".1f",
        color="Exited",
        color_continuous_scale="Reds",
        title="Product Holdings vs Churn"
    )

    fig6.update_layout(**PLOT_LAYOUT)

    left.plotly_chart(
        fig6,
        width="stretch",
        key="product_churn"
    )

    # TENURE

    tenure_data = (
        filtered
        .groupby(
            "TenureGroup",
            observed=True
        )["Exited"]
        .mean()
        .reset_index()
    )

    tenure_data["Exited"] *= 100

    fig7 = px.bar(
        tenure_data,
        x="TenureGroup",
        y="Exited",
        text_auto=".1f",
        color="Exited",
        color_continuous_scale="Reds",
        title="Tenure vs Churn"
    )

    fig7.update_layout(**PLOT_LAYOUT)

    right.plotly_chart(
        fig7,
        width="stretch",
        key="tenure_churn"
    )

    st.info(
        """
        Key Customer Insights

        • Customers aged 46–60 remain the highest-risk segment.

        • Female customers exhibit higher churn behaviour.

        • Product complexity appears linked to churn.

        • Longer tenure alone does not guarantee retention.
        """
    )

# ==================================================
# TAB 3 — GEOGRAPHIC INTELLIGENCE
# ==================================================

with tab3:

    st.markdown(
        '<div class="section-header">Geographic Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-sub">Understand where churn risk is concentrated geographically.</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    # COUNTRY RANKING

    geo_rank = (
        filtered
        .groupby("Geography")["Exited"]
        .mean()
        .reset_index()
    )

    geo_rank["Exited"] *= 100

    fig8 = px.bar(
        geo_rank,
        x="Geography",
        y="Exited",
        text_auto=".1f",
        color="Exited",
        color_continuous_scale="Reds",
        title="Country Churn Ranking"
    )

    fig8.update_layout(**PLOT_LAYOUT)

    col1.plotly_chart(
        fig8,
        width="stretch",
        key="geo_ranking"
    )

    # COUNTRY x GENDER

    geo_gender = (
        filtered
        .groupby(
            ["Geography","Gender"]
        )["Exited"]
        .mean()
        .reset_index()
    )

    geo_gender["Exited"] *= 100

    fig9 = px.bar(
        geo_gender,
        x="Geography",
        y="Exited",
        color="Gender",
        barmode="group",
        text_auto=".1f",
        color_discrete_map={
            "Male":ACCENT,
            "Female":DANGER
        },
        title="Country × Gender Churn"
    )

    fig9.update_layout(**PLOT_LAYOUT)

    col2.plotly_chart(
        fig9,
        width="stretch",
        key="geo_gender"
    )

    st.divider()

    st.subheader("🌍 Regional Risk Matrix")

    geo_heat = (
        filtered
        .pivot_table(
            values="Exited",
            index="AgeGroup",
            columns="Geography",
            aggfunc="mean",
            observed=True
        ) * 100
    )

    fig_geo, ax = plt.subplots(figsize=(12,5))

    sns.heatmap(
        geo_heat,
        annot=True,
        fmt=".1f",
        cmap="Reds",
        linewidths=.5,
        ax=ax
    )

    ax.set_xlabel("")
    ax.set_ylabel("")

    st.pyplot(fig_geo)

    st.info(
        """
        Geographic Insight

        Germany remains the most vulnerable market.
        Combined with the 46–60 age segment,
        churn concentration becomes significantly elevated.

        Retention resources should be prioritised
        geographically before broad deployment.
        """
    )

# ==================================================
# TAB 4 — FINANCIAL EXPOSURE
# ==================================================

with tab4:

    st.markdown(
        '<div class="section-header">Financial Exposure</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-sub">Quantify revenue and customer value at risk.</div>',
        unsafe_allow_html=True
    )

    # KPI ROW

    hv_count = int(

        filtered[
            (filtered["IsHighValue"] == 1)
            &
            (filtered["Exited"] == 1)
        ].shape[0]

    )

    avg_balance_lost = (

        filtered[
            (filtered["IsHighValue"] == 1)
            &
            (filtered["Exited"] == 1)
        ]["Balance"]

        .mean()

    )

    k1,k2,k3 = st.columns(3)

    k1.metric(
        "High Value Customers Lost",
        f"{hv_count:,}"
    )

    k2.metric(
        "Average Balance Lost",
        f"£{avg_balance_lost:,.0f}"
    )

    k3.metric(
        "Balance At Risk",
        f"£{balance_risk:.2f}M"
    )

    st.divider()

    left,right = st.columns(2)

    # BALANCE SEGMENT

    balance_data = (
        filtered
        .groupby(
            "BalanceSegment",
            observed=True
        )["Exited"]
        .mean()
        .reset_index()
    )

    balance_data["Exited"] *= 100

    fig10 = px.bar(
        balance_data,
        x="BalanceSegment",
        y="Exited",
        text_auto=".1f",
        color="BalanceSegment",
        color_discrete_map={
            "Zero":"#CBD5E1",
            "Low":WARNING,
            "High":DANGER
        },
        title="Balance Segment Risk"
    )

    fig10.update_layout(**PLOT_LAYOUT)

    left.plotly_chart(
        fig10,
        width="stretch",
        key="balance_segment"
    )

    # HIGH VALUE GEO

    hv_geo = (
        filtered[
            filtered["IsHighValue"] == 1
        ]
        .groupby("Geography")["Exited"]
        .mean()
        .reset_index()
    )

    hv_geo["Exited"] *= 100

    fig11 = px.bar(
        hv_geo,
        x="Geography",
        y="Exited",
        text_auto=".1f",
        color="Exited",
        color_continuous_scale="Reds",
        title="High Value Churn by Country"
    )

    fig11.update_layout(**PLOT_LAYOUT)

    right.plotly_chart(
        fig11,
        width="stretch",
        key="high_value_geo"
    )

    st.divider()

    st.subheader("💎 Risk Quadrant Analysis")

    sample = filtered.sample(
        min(2500, len(filtered)),
        random_state=42
    ).copy()

    sample["Status"] = sample["Exited"].map(
        {
            0:"Retained",
            1:"Churned"
        }
    )

    median_balance = sample["Balance"].median()
    median_salary = sample["EstimatedSalary"].median()

    fig12 = px.scatter(
        sample,
        x="Balance",
        y="EstimatedSalary",
        color="Status",
        opacity=0.55,
        color_discrete_map={
            "Retained":SUCCESS,
            "Churned":DANGER
        },
        title="Customer Risk Quadrants"
    )

    fig12.add_vline(
        x=median_balance,
        line_dash="dash"
    )

    fig12.add_hline(
        y=median_salary,
        line_dash="dash"
    )

    fig12.add_annotation(
        x=median_balance*1.5,
        y=median_salary*1.6,
        text="VIP Retention Zone",
        showarrow=False
    )

    fig12.add_annotation(
        x=median_balance*0.4,
        y=median_salary*1.6,
        text="Upsell Zone",
        showarrow=False
    )

    fig12.add_annotation(
        x=median_balance*1.5,
        y=median_salary*0.4,
        text="High-Risk Zone",
        showarrow=False
    )

    fig12.update_layout(**PLOT_LAYOUT)

    st.plotly_chart(
        fig12,
        width="stretch",
        key="risk_quadrant"
    )

    st.info(
        f"""
        Financial Summary

        • Total estimated exposure: £{balance_risk:.1f}M

        • {hv_count:,} high-value customers have already churned

        • Average balance lost per high-value customer:
          £{avg_balance_lost:,.0f}

        • VIP customer protection should be prioritised
          over mass retention campaigns.
        """
    )

# ==================================================
# TAB 5 — ACTION CENTER
# ==================================================

with tab5:

    st.markdown(
        '<div class="section-header">Retention Strategy Center</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-sub">Executive action plan based on detected churn patterns.</div>',
        unsafe_allow_html=True
    )

    # ==================================================
    # PRIORITY MATRIX
    # ==================================================

    st.subheader("🚨 Priority Action Matrix")

    st.error(
        f"""
Immediate Actions This Week

1. Focus retention efforts on {top_country}

2. Protect customers in age group {top_age}

3. Secure approximately £{balance_risk:.1f}M in deposits

4. Re-engage inactive customers immediately
"""
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown("""
        <div class="priority-card">

        <h4 style="color:#EF4444;">
        HIGH IMPACT • IMMEDIATE ACTION
        </h4>

        <b>Germany Retention Program</b>

        <ul>
        <li>Highest churn market</li>
        <li>46–60 age segment at risk</li>
        <li>Deploy dedicated relationship managers</li>
        <li>Review service quality metrics</li>
        </ul>

        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="priority-card">

        <h4 style="color:#EF4444;">
        HIGH IMPACT • CUSTOMER VALUE
        </h4>

        <b>VIP Customer Protection</b>

        <ul>
        <li>Identify top balance customers</li>
        <li>Offer premium retention packages</li>
        <li>Dedicated account support</li>
        <li>Preferential banking services</li>
        </ul>

        </div>
        """, unsafe_allow_html=True)

    with c2:

        st.markdown("""
        <div class="priority-card">

        <h4 style="color:#F59E0B;">
        MEDIUM IMPACT
        </h4>

        <b>Female Customer Engagement</b>

        <ul>
        <li>Improve digital experience</li>
        <li>Targeted loyalty campaigns</li>
        <li>Personalized product journeys</li>
        <li>Financial planning solutions</li>
        </ul>

        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="priority-card">

        <h4 style="color:#10B981;">
        QUICK WIN
        </h4>

        <b>Inactive Member Recovery</b>

        <ul>
        <li>Automated engagement campaigns</li>
        <li>Fee waiver incentives</li>
        <li>Cashback programs</li>
        <li>Reactivation rewards</li>
        </ul>

        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ==================================================
    # STRATEGIC ROADMAP
    # ==================================================

    st.subheader("🗺️ Strategic Roadmap")

    roadmap1, roadmap2, roadmap3 = st.columns(3)

    roadmap1.markdown("""
    ### 30 Days

    - Launch churn monitoring
    - Germany intervention
    - Identify VIP customers
    - Build risk watchlists
    """)

    roadmap2.markdown("""
    ### 90 Days

    - Retention campaigns
    - Loyalty program redesign
    - Advisor allocation
    - Product rationalisation
    """)

    roadmap3.markdown("""
    ### 180 Days

    - Personalised banking
    - Predictive retention engine
    - Customer lifecycle program
    - Portfolio optimisation
    """)

    st.divider()

    # ==================================================
    # EXPECTED IMPACT
    # ==================================================

    st.subheader("📈 Expected Business Impact")

    impact1, impact2, impact3, impact4 = st.columns(4)

    impact1.metric(
        "Potential Churn Reduction",
        "8–12%"
    )

    impact2.metric(
        "Balance Protected",
        f"£{balance_risk:.1f}M"
    )

    impact3.metric(
        "High Value Customers",
        f"{hv_count:,}"
    )

    impact4.metric(
        "Retention Priority",
        "Critical"
    )

    st.divider()

    # ==================================================
    # EXECUTIVE SUMMARY
    # ==================================================

    st.markdown(
        """
        ### Executive Summary
        """
    )

    st.success(
        f"""
        Key Finding

        Current churn exposure stands at {churn_rate:.1f}%.

        High-value customer balances worth approximately
        £{balance_risk:.1f}M remain vulnerable.

        Germany, customers aged 46–60,
        inactive members and multi-product customers
        represent the most urgent retention priorities.

        Recommended focus:
        Protect high-value customers first,
        then deploy targeted retention programs
        to high-risk demographic segments.
        """
    )

# ==================================================
# FOOTER
# ==================================================

st.markdown("---")

st.markdown(
f"""
<div style="text-align:center;">
<h4 style="margin-bottom:5px;color:#0F172A;">
ECB Customer Intelligence Platform
</h4>
<p style="color:#64748B;">
Executive Retention Analytics Dashboard
</p>
<p style="color:#94A3B8;font-size:13px;">
Developed by Nikhil Chandrakar
</p>
<p style="color:#94A3B8;font-size:12px;">
PGDM Finance & Business Analytics
</p>
</div>
""",
unsafe_allow_html=True
)
