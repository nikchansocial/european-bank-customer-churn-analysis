import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="ECB Customer Churn Intelligence",
    page_icon="🏦",
    layout="wide"
)

# ECB Color Palette
ECB_NAVY    = "#003366"
ECB_YELLOW  = "#FFCC00"
ECB_RED     = "#CC0000"
ECB_GREEN   = "#006633"
ECB_GRAY    = "#F0F4F8"
ECB_MID     = "#336699"

@st.cache_data
def load_data():
    df = pd.read_csv('data/European_Bank.csv')
    df.drop(columns=['Surname', 'CustomerId', 'Year'], inplace=True)
    df['AgeGroup'] = pd.cut(df['Age'],
        bins=[0,29,45,60,120],
        labels=['<30','30-45','46-60','60+'])
    df['CreditBand'] = pd.cut(df['CreditScore'],
        bins=[299,579,669,739,850],
        labels=['Low','Medium','High','Very High'])
    df['TenureGroup'] = pd.cut(df['Tenure'],
        bins=[-1,2,6,10],
        labels=['New','Mid-term','Long-term'])
    df['BalanceSegment'] = pd.cut(df['Balance'],
        bins=[-1,0,50000,300000],
        labels=['Zero','Low','High'])
    threshold = df['Balance'].quantile(0.75)
    df['IsHighValue'] = (df['Balance'] >= threshold).astype(int)
    return df

df = load_data()

# ── SIDEBAR ──
with st.sidebar:
    st.markdown(
        f"""
        <div style='background-color:{ECB_NAVY}; padding:16px; border-radius:8px; margin-bottom:16px;'>
            <p style='color:{ECB_YELLOW}; font-size:18px; font-weight:bold; margin:0;'>🏦 ECB Churn Intelligence</p>
            <p style='color:white; font-size:11px; margin:4px 0 0 0;'>Customer Retention Analytics · 2025</p>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("### 🔍 Filter Customers")
    geo = st.multiselect("Country",
          df['Geography'].unique(),
          default=list(df['Geography'].unique()))
    age = st.multiselect("Age Group",
          df['AgeGroup'].unique(),
          default=list(df['AgeGroup'].unique()))
    gender = st.radio("Gender", ["All", "Male", "Female"])
    member = st.radio("Member Status", ["All", "Active", "Inactive"])
    balance_seg = st.multiselect("Balance Segment",
          df['BalanceSegment'].unique(),
          default=list(df['BalanceSegment'].unique()))

    st.markdown("---")
    st.markdown(
        "<p style='font-size:11px; color:gray;'>Data: European Central Bank<br>10,000 customers · France, Germany, Spain</p>",
        unsafe_allow_html=True
    )

# ── APPLY FILTERS ──
mask = (df['Geography'].isin(geo) &
        df['AgeGroup'].isin(age) &
        df['BalanceSegment'].isin(balance_seg))
if gender != "All":
    mask &= df['Gender'] == gender
if member != "All":
    mask &= df['IsActiveMember'] == (1 if member == "Active" else 0)
filtered = df[mask]

# ── HEADER ──
st.markdown(
    f"""
    <div style='background-color:{ECB_NAVY}; padding:24px 28px; border-radius:10px; margin-bottom:24px;'>
        <h1 style='color:{ECB_YELLOW}; margin:0; font-size:26px;'>🏦 European Bank — Customer Churn Intelligence Dashboard</h1>
        <p style='color:white; margin:6px 0 0 0; font-size:14px;'>
        Identifying high-risk customer segments to support targeted retention strategies across France, Germany & Spain
        </p>
    </div>
    """, unsafe_allow_html=True
)

# ── PROBLEM STATEMENT BANNER ──
churn_r   = filtered['Exited'].mean() * 100
total_c   = int(filtered['Exited'].sum())
hv_r      = filtered[filtered['IsHighValue']==1]['Exited'].mean() * 100
risk      = filtered[(filtered['IsHighValue']==1) & (filtered['Exited']==1)]['Balance'].sum() / 1e6
inactive_c= filtered[filtered['IsActiveMember']==0]['Exited'].mean() * 100

col_alert = st.columns([2,1,1,1,1])
col_alert[0].markdown(
    f"""
    <div style='background:{ECB_RED}; color:white; padding:14px 18px; border-radius:8px; height:80px;'>
        <div style='font-size:11px; opacity:0.85;'>⚠ OVERALL CHURN RATE</div>
        <div style='font-size:28px; font-weight:bold;'>{churn_r:.1f}%</div>
        <div style='font-size:11px; opacity:0.75;'>{total_c:,} customers lost</div>
    </div>
    """, unsafe_allow_html=True
)
col_alert[1].markdown(
    f"""
    <div style='background:{ECB_NAVY}; color:white; padding:14px 18px; border-radius:8px; height:80px;'>
        <div style='font-size:11px; opacity:0.85;'>💰 BALANCE AT RISK</div>
        <div style='font-size:24px; font-weight:bold;'>£{risk:.1f}M</div>
        <div style='font-size:11px; opacity:0.75;'>High-value customers</div>
    </div>
    """, unsafe_allow_html=True
)
col_alert[2].markdown(
    f"""
    <div style='background:{ECB_MID}; color:white; padding:14px 18px; border-radius:8px; height:80px;'>
        <div style='font-size:11px; opacity:0.85;'>⭐ HIGH-VALUE CHURN</div>
        <div style='font-size:24px; font-weight:bold;'>{hv_r:.1f}%</div>
        <div style='font-size:11px; opacity:0.75;'>Premium segment</div>
    </div>
    """, unsafe_allow_html=True
)
col_alert[3].markdown(
    f"""
    <div style='background:#8B4513; color:white; padding:14px 18px; border-radius:8px; height:80px;'>
        <div style='font-size:11px; opacity:0.85;'>😴 INACTIVE CHURN</div>
        <div style='font-size:24px; font-weight:bold;'>{inactive_c:.1f}%</div>
        <div style='font-size:11px; opacity:0.75;'>Disengaged members</div>
    </div>
    """, unsafe_allow_html=True
)
col_alert[4].markdown(
    f"""
    <div style='background:{ECB_GREEN}; color:white; padding:14px 18px; border-radius:8px; height:80px;'>
        <div style='font-size:11px; opacity:0.85;'>👥 CUSTOMERS ANALYSED</div>
        <div style='font-size:24px; font-weight:bold;'>{len(filtered):,}</div>
        <div style='font-size:11px; opacity:0.75;'>After filters applied</div>
    </div>
    """, unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ──
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍 Geographic Risk",
    "👥 Demographic Analysis",
    "💼 Product & Tenure",
    "💰 Financial Risk",
    "⭐ Retention Recommendations"
])

plot_cfg = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color=ECB_NAVY,
    title_font_color=ECB_NAVY,
    title_font_size=14
)

# ── TAB 1: Geographic Risk ──
with tab1:
    st.markdown(f"<h3 style='color:{ECB_NAVY};'>Which countries are losing the most customers?</h3>", unsafe_allow_html=True)
    st.caption("Use this to identify where retention campaigns should be prioritised geographically.")

    col1, col2 = st.columns(2)

    geo_data = filtered.groupby('Geography')['Exited'].mean().reset_index()
    geo_data['Exited'] = (geo_data['Exited'] * 100).round(1)
    geo_data.columns = ['Country', 'Churn Rate (%)']
    geo_data['Color'] = geo_data['Churn Rate (%)'].apply(
        lambda x: ECB_RED if x > 25 else (ECB_YELLOW if x > 18 else ECB_GREEN))

    fig1 = go.Figure(go.Bar(
        x=geo_data['Country'], y=geo_data['Churn Rate (%)'],
        marker_color=geo_data['Color'],
        text=geo_data['Churn Rate (%)'].apply(lambda x: f'{x}%'),
        textposition='outside'
    ))
    fig1.update_layout(title='Churn Rate by Country', yaxis_title='Churn Rate (%)',
                       **plot_cfg)
    col1.plotly_chart(fig1, use_container_width=True)

    cross = filtered.groupby(['Geography','Gender'])['Exited'].mean().reset_index()
    cross['Exited'] = (cross['Exited'] * 100).round(1)
    cross.columns = ['Country','Gender','Churn Rate (%)']
    fig2 = px.bar(cross, x='Country', y='Churn Rate (%)', color='Gender',
                  barmode='group', text_auto='.1f',
                  color_discrete_map={'Female': ECB_RED, 'Male': ECB_NAVY},
                  title='Churn by Country & Gender')
    fig2.update_layout(**plot_cfg)
    col2.plotly_chart(fig2, use_container_width=True)

    st.markdown(f"<h4 style='color:{ECB_NAVY};'>Age Risk Heatmap by Country</h4>", unsafe_allow_html=True)
    st.caption("Darkest cells = highest churn risk. Focus retention on these exact age-country combinations.")
    pivot = filtered.pivot_table('Exited','AgeGroup','Geography', aggfunc='mean', observed=True)*100
    fig3, ax = plt.subplots(figsize=(9,4))
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd',
                linewidths=0.5, ax=ax, cbar_kws={'label':'Churn Rate (%)'})
    ax.set_title('Churn Rate Heatmap: Age × Country', color=ECB_NAVY, fontweight='bold')
    fig3.patch.set_alpha(0)
    st.pyplot(fig3)

# ── TAB 2: Demographic Analysis ──
with tab2:
    st.markdown(f"<h3 style='color:{ECB_NAVY};'>Which customer profiles churn the most?</h3>", unsafe_allow_html=True)
    st.caption("Identify demographic groups that need personalised retention offers.")

    col1, col2 = st.columns(2)

    age_data = filtered.groupby('AgeGroup', observed=True)['Exited'].mean().reset_index()
    age_data['Exited'] = (age_data['Exited']*100).round(1)
    age_data['Color'] = age_data['Exited'].apply(
        lambda x: ECB_RED if x > 40 else (ECB_YELLOW if x > 20 else ECB_GREEN))
    fig4 = go.Figure(go.Bar(
        x=age_data['AgeGroup'].astype(str),
        y=age_data['Exited'],
        marker_color=age_data['Color'],
        text=age_data['Exited'].apply(lambda x: f'{x}%'),
        textposition='outside'
    ))
    fig4.update_layout(title='Churn Rate by Age Group',
                       xaxis_title='Age Group', yaxis_title='Churn Rate (%)',
                       **plot_cfg)
    col1.plotly_chart(fig4, use_container_width=True)

    gender_data = filtered.groupby('Gender')['Exited'].mean().reset_index()
    gender_data['Exited'] = (gender_data['Exited']*100).round(1)
    fig5 = px.pie(gender_data, values='Exited', names='Gender',
                  color_discrete_map={'Female': ECB_RED, 'Male': ECB_NAVY},
                  title='Churn Share by Gender',
                  hole=0.4)
    fig5.update_layout(**plot_cfg)
    col2.plotly_chart(fig5, use_container_width=True)

    st.markdown(f"<h4 style='color:{ECB_NAVY};'>Age × Gender churn deep dive</h4>", unsafe_allow_html=True)
    age_gender = filtered.groupby(['AgeGroup','Gender'], observed=True)['Exited'].mean().reset_index()
    age_gender['Exited'] = (age_gender['Exited']*100).round(1)
    age_gender.columns = ['Age Group','Gender','Churn Rate (%)']
    fig6 = px.bar(age_gender, x='Age Group', y='Churn Rate (%)', color='Gender',
                  barmode='group', text_auto='.1f',
                  color_discrete_map={'Female': ECB_RED, 'Male': ECB_NAVY},
                  title='Churn Rate: Age Group × Gender')
    fig6.update_layout(**plot_cfg)
    st.plotly_chart(fig6, use_container_width=True)

# ── TAB 3: Product & Tenure ──
with tab3:
    st.markdown(f"<h3 style='color:{ECB_NAVY};'>Do product holdings and loyalty affect churn?</h3>", unsafe_allow_html=True)
    st.caption("Understand if customers with more products or longer tenure are more or less likely to leave.")

    col1, col2 = st.columns(2)

    prod_data = filtered.groupby('NumOfProducts')['Exited'].mean().reset_index()
    prod_data['Exited'] = (prod_data['Exited']*100).round(1)
    prod_data['Color'] = prod_data['Exited'].apply(
        lambda x: ECB_RED if x > 50 else (ECB_YELLOW if x > 25 else ECB_GREEN))
    fig7 = go.Figure(go.Bar(
        x=prod_data['NumOfProducts'].astype(str),
        y=prod_data['Exited'],
        marker_color=prod_data['Color'],
        text=prod_data['Exited'].apply(lambda x: f'{x}%'),
        textposition='outside'
    ))
    fig7.update_layout(title='⚠ Churn by Number of Products',
                       xaxis_title='Products Held', yaxis_title='Churn Rate (%)',
                       **plot_cfg)
    col1.plotly_chart(fig7, use_container_width=True)

    tenure_data = filtered.groupby('TenureGroup', observed=True)['Exited'].mean().reset_index()
    tenure_data['Exited'] = (tenure_data['Exited']*100).round(1)
    tenure_data.columns = ['Tenure','Churn Rate (%)']
    fig8 = px.bar(tenure_data, x='Tenure', y='Churn Rate (%)',
                  color='Churn Rate (%)',
                  color_continuous_scale=[[0, ECB_GREEN],[0.5, ECB_YELLOW],[1, ECB_RED]],
                  text_auto='.1f',
                  title='Churn Rate by Customer Tenure')
    fig8.update_layout(**plot_cfg)
    col2.plotly_chart(fig8, use_container_width=True)

    st.markdown(f"<h4 style='color:{ECB_NAVY};'>Active vs Inactive member churn</h4>", unsafe_allow_html=True)
    active_data = filtered.groupby('IsActiveMember')['Exited'].mean().reset_index()
    active_data['IsActiveMember'] = active_data['IsActiveMember'].map({1:'Active', 0:'Inactive'})
    active_data['Exited'] = (active_data['Exited']*100).round(1)
    active_data.columns = ['Member Status','Churn Rate (%)']
    fig9 = px.bar(active_data, x='Member Status', y='Churn Rate (%)',
                  color='Member Status',
                  color_discrete_map={'Active': ECB_GREEN, 'Inactive': ECB_RED},
                  text_auto='.1f',
                  title='Engagement vs Churn: Active vs Inactive Members')
    fig9.update_layout(**plot_cfg)
    st.plotly_chart(fig9, use_container_width=True)

# ── TAB 4: Financial Risk ──
with tab4:
    st.markdown(f"<h3 style='color:{ECB_NAVY};'>What is the financial impact of churn?</h3>", unsafe_allow_html=True)
    st.caption("Quantify revenue at risk and identify financially vulnerable churning segments.")

    col1, col2, col3 = st.columns(3)
    hv_count  = int(filtered[(filtered['IsHighValue']==1) & (filtered['Exited']==1)].shape[0])
    avg_bal   = filtered[(filtered['IsHighValue']==1) & (filtered['Exited']==1)]['Balance'].mean()
    col1.metric("High-Value Customers Lost", f"{hv_count:,}")
    col2.metric("Avg Balance Lost per Customer", f"£{avg_bal:,.0f}")
    col3.metric("Total Balance at Risk", f"£{risk:.2f}M")

    col1, col2 = st.columns(2)

    bal_data = filtered.groupby('BalanceSegment', observed=True)['Exited'].mean().reset_index()
    bal_data['Exited'] = (bal_data['Exited']*100).round(1)
    bal_data.columns = ['Balance Segment','Churn Rate (%)']
    fig10 = px.bar(bal_data, x='Balance Segment', y='Churn Rate (%)',
                   color='Balance Segment',
                   color_discrete_map={'Zero': ECB_MID,'Low': ECB_RED,'High': ECB_NAVY},
                   text_auto='.1f',
                   title='Churn Rate by Balance Segment')
    fig10.update_layout(**plot_cfg)
    col1.plotly_chart(fig10, use_container_width=True)

    hv_geo = filtered[filtered['IsHighValue']==1].groupby('Geography')['Exited'].mean().reset_index()
    hv_geo['Exited'] = (hv_geo['Exited']*100).round(1)
    hv_geo.columns = ['Country','Churn Rate (%)']
    fig11 = px.bar(hv_geo, x='Country', y='Churn Rate (%)',
                   color='Country',
                   color_discrete_map={'France': ECB_MID,'Germany': ECB_RED,'Spain': ECB_GREEN},
                   text_auto='.1f',
                   title='High-Value Customer Churn by Country')
    fig11.update_layout(**plot_cfg)
    col2.plotly_chart(fig11, use_container_width=True)

    st.markdown(f"<h4 style='color:{ECB_NAVY};'>Balance vs Salary — Who is churning?</h4>", unsafe_allow_html=True)
    sample = filtered.sample(min(2000, len(filtered)), random_state=42).copy()
    sample['Status'] = sample['Exited'].map({0:'Retained', 1:'Churned'})
    fig12 = px.scatter(sample, x='Balance', y='EstimatedSalary',
                       color='Status',
                       color_discrete_map={'Retained': ECB_GREEN,'Churned': ECB_RED},
                       opacity=0.5,
                       title='Financial Profile: Churned vs Retained Customers')
    fig12.update_layout(**plot_cfg)
    st.plotly_chart(fig12, use_container_width=True)

# ── TAB 5: Recommendations ──
with tab5:
    st.markdown(f"<h3 style='color:{ECB_NAVY};'>What should the bank do now?</h3>", unsafe_allow_html=True)
    st.caption("Actionable retention strategies based on the churn patterns discovered.")

    rec_data = [
        ("🔴 Germany Emergency Retention", "32.4% churn — highest risk country",
         "Launch a dedicated Germany retention campaign. Offer personalised relationship managers to 46–60 age group. Investigate local service quality issues.",
         ECB_RED),
        ("🟡 Female Customer Engagement", "25.1% churn vs 16.5% for males",
         "Design female-focused financial products (savings goals, family planning tools). Improve digital banking UX. Run targeted loyalty programmes.",
         "#CC7700"),
        ("🔴 46–60 Age Group Crisis", "51.1% churn — majority are leaving",
         "This group likely has maturing loans and pension planning needs. Offer retirement planning packages, wealth management, and dedicated advisors.",
         ECB_RED),
        ("⚠ Product Over-bundling Alert", "3–4 products = 83–100% churn",
         "Customers with 3+ products are overwhelmed or mis-sold. Audit product bundling strategy. Simplify offerings. Focus on quality over quantity.",
         "#CC7700"),
        ("💤 Inactive Member Re-engagement", "26.9% inactive churn vs lower active",
         "Identify inactive members early. Send personalised re-engagement emails. Offer cashback or fee waivers. Create activity milestones with rewards.",
         ECB_NAVY),
        ("💰 High-Value Retention Priority", "£88.6M balance at risk",
         "Assign dedicated relationship managers to high-value customers. Offer exclusive products, preferential rates, and VIP service tiers.",
         ECB_MID),
    ]

    for i in range(0, len(rec_data), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i+j < len(rec_data):
                title, subtitle, body, color = rec_data[i+j]
                col.markdown(
                    f"""
                    <div style='border-left: 5px solid {color}; background:{ECB_GRAY};
                                padding:16px 20px; border-radius:6px; margin-bottom:12px;'>
                        <p style='color:{color}; font-weight:bold; font-size:15px; margin:0;'>{title}</p>
                        <p style='color:{ECB_NAVY}; font-size:12px; margin:4px 0 8px 0;'><em>{subtitle}</em></p>
                        <p style='color:#333; font-size:13px; margin:0; line-height:1.6;'>{body}</p>
                    </div>
                    """, unsafe_allow_html=True
                )

    st.markdown("---")
    st.markdown(
        f"<p style='text-align:center; color:{ECB_NAVY}; font-size:12px;'>"
        "ECB Customer Churn Intelligence · Built with Streamlit · Unified Mentor Project · 2025"
        "</p>", unsafe_allow_html=True
    )
