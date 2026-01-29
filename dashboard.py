import streamlit as st
import pandas as pd
import numpy as np
import mysql.connector

# -----------------------
# Database Connection
# -----------------------
@st.cache_data
def get_data_from_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="marketing_campaign"
    )

    query = "SELECT * FROM customer_marketing_raw"
    df = pd.read_sql(query, conn)
    conn.close()

    # -----------------------
    # Feature Engineering
    # -----------------------
    CURRENT_YEAR = pd.Timestamp.now().year
    df['Age'] = CURRENT_YEAR - df['Year_Birth']
    df['TotalChildren'] = df['Kidhome'] + df['Teenhome']
    df['TotalSpend'] = (
        df['MntWines'] + df['MntFruits'] + df['MntMeatProducts'] +
        df['MntFishProducts'] + df['MntSweetProducts'] + df['MntGoldProds']
    )
    df['TotalPurchases'] = (
        df['NumWebPurchases'] + df['NumCatalogPurchases'] +
        df['NumStorePurchases'] + df['NumDealsPurchases']
    )

    # -----------------------
    # Rule-Based Segmentation
    # -----------------------
    df['HighIncome'] = np.where(df['Income'] > 75000, 1, 0)
    df['YoungCustomer'] = np.where(df['Age'] < 30, 1, 0)
    df['CampaignResponder'] = np.where(df['Response'] == 1, 1, 0)
    df['HighWebEngagement'] = np.where(df['NumWebVisitsMonth'] > 5, 1, 0)
    df['FamilyCustomer'] = np.where(df['TotalChildren'] > 0, 1, 0)
    spend_threshold = df['TotalSpend'].quantile(0.9)
    df['HighSpender'] = np.where(df['TotalSpend'] > spend_threshold, 1, 0)

    return df

df = get_data_from_db()

# -----------------------
# Streamlit Sidebar Filters
# -----------------------
st.sidebar.header("Filter Customers")

age_filter = st.sidebar.slider("Age Range", int(df['Age'].min()), int(df['Age'].max()), (20,60))
income_filter = st.sidebar.slider("Income Range", int(df['Income'].min()), int(df['Income'].max()), (20000,100000))
country_filter = st.sidebar.multiselect("Country", options=df['Country'].unique(), default=df['Country'].unique())
marital_filter = st.sidebar.multiselect("Marital Status", options=df['Marital_Status'].unique(), default=df['Marital_Status'].unique())

df_filtered = df[
    (df['Age'] >= age_filter[0]) & (df['Age'] <= age_filter[1]) &
    (df['Income'] >= income_filter[0]) & (df['Income'] <= income_filter[1]) &
    (df['Country'].isin(country_filter)) &
    (df['Marital_Status'].isin(marital_filter))
]

# -----------------------
# Dashboard KPIs
# -----------------------
st.title(" Marketing Campaign Dashboard (DB)")

st.markdown(f"Total Customers in Selection: **{df_filtered.shape[0]}**")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Total Spend", f"₹{df_filtered['TotalSpend'].mean():,.0f}")
col2.metric("Avg Total Purchases", f"{df_filtered['TotalPurchases'].mean():.0f}")
col3.metric("Response Rate", f"{df_filtered['Response'].mean()*100:.2f}%")
col4.metric("High-Value Customers", f"{df_filtered['HighSpender'].sum()}")

# -----------------------
# Segment Overview
# -----------------------
st.subheader("Segment Overview")
segments = ['HighIncome','YoungCustomer','CampaignResponder','HighWebEngagement','FamilyCustomer','HighSpender']
segment_summary = df_filtered[segments].sum().reset_index()
segment_summary.columns = ['Segment','Count']
st.bar_chart(segment_summary.set_index('Segment'))

# -----------------------
# Spending by Product
# -----------------------
st.subheader("Average Spend by Product")
products = ['MntWines','MntFruits','MntMeatProducts','MntFishProducts','MntSweetProducts','MntGoldProds']
spend_summary = df_filtered[products].mean().reset_index()
spend_summary.columns = ['Product','AvgSpend']
st.bar_chart(spend_summary.set_index('Product'))

# -----------------------
# Response Rate by Segment
# -----------------------
st.subheader("Response Rate by Segment")
response_rate = {}
for seg in segments:
    response_rate[seg] = df_filtered[df_filtered[seg]==1]['Response'].mean()

response_df = pd.DataFrame.from_dict(response_rate, orient='index', columns=['ResponseRate'])
response_df['ResponseRate'] = response_df['ResponseRate']*100
st.bar_chart(response_df)
