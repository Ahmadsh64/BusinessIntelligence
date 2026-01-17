"""
Retail BI Web Application
Streamlit-based Business Intelligence Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Retail BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'BusinessIntelligence',
    'user': 'root',
    'password': '12345',  # Change this to your MySQL password
    'charset': 'utf8mb4'
}

@st.cache_resource
def get_db_connection():
    """Create database connection with caching (using cache_resource for non-serializable objects)"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None

@st.cache_data(ttl=3600)
def execute_query(query):
    """Execute SQL query and return DataFrame"""
    connection = get_db_connection()
    if connection:
        try:
            df = pd.read_sql(query, connection)
            # Don't close connection here - it's cached and shared
            return df
        except Exception as e:
            st.error(f"Query error: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# ==================== SIDEBAR FILTERS ====================
st.sidebar.header("🔍 Filters")

# Date range filter
st.sidebar.subheader("Date Range")
default_end = datetime.now()
default_start = default_end - timedelta(days=365)

date_start = st.sidebar.date_input(
    "Start Date",
    value=default_start,
    max_value=default_end
)
date_end = st.sidebar.date_input(
    "End Date",
    value=default_end,
    min_value=date_start,
    max_value=default_end
)

# Store filter
stores_query = "SELECT DISTINCT store_id, store_name, city FROM dim_store ORDER BY store_name"
df_stores = execute_query(stores_query)
selected_stores = st.sidebar.multiselect(
    "Select Stores",
    options=df_stores['store_id'].tolist(),
    format_func=lambda x: df_stores[df_stores['store_id'] == x]['store_name'].values[0] if len(df_stores[df_stores['store_id'] == x]) > 0 else str(x)
)

# Category filter
categories_query = "SELECT DISTINCT category FROM dim_product ORDER BY category"
df_categories = execute_query(categories_query)
selected_categories = st.sidebar.multiselect(
    "Select Categories",
    options=df_categories['category'].tolist()
)

# Region filter
regions_query = "SELECT DISTINCT region FROM dim_store ORDER BY region"
df_regions = execute_query(regions_query)
selected_regions = st.sidebar.multiselect(
    "Select Regions",
    options=df_regions['region'].tolist()
)

# Build WHERE clause
where_conditions = [f"d.date BETWEEN '{date_start}' AND '{date_end}'"]
if selected_stores:
    where_conditions.append(f"s.store_id IN ({','.join(map(str, selected_stores))})")
if selected_categories:
    cat_list = "','".join(selected_categories)
    where_conditions.append(f"p.category IN ('{cat_list}')")
if selected_regions:
    reg_list = "','".join(selected_regions)
    where_conditions.append(f"s.region IN ('{reg_list}')")

where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""

# ==================== MAIN DASHBOARD ====================
st.title("📊 Retail Business Intelligence Dashboard")
st.markdown("---")

# ==================== KPI CARDS ====================
st.header("💰 Key Performance Indicators (KPIs)")

kpi_query = f"""
SELECT 
    COUNT(DISTINCT f.sale_id) AS total_transactions,
    SUM(f.revenue) AS total_revenue,
    SUM(f.profit) AS total_profit,
    SUM(f.profit) / SUM(f.revenue) * 100 AS profit_margin,
    AVG(f.revenue) AS avg_order_value,
    SUM(f.quantity) AS total_quantity
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_store s ON f.store_id = s.store_id
JOIN dim_product p ON f.product_id = p.product_id
WHERE 1=1 {where_clause}
"""

df_kpi = execute_query(kpi_query)

if not df_kpi.empty and df_kpi['total_revenue'].iloc[0] is not None:
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Revenue",
            f"₪{df_kpi['total_revenue'].iloc[0]:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Total Profit",
            f"₪{df_kpi['total_profit'].iloc[0]:,.0f}",
            delta=None
        )
    
    with col3:
        profit_margin = df_kpi['profit_margin'].iloc[0]
        st.metric(
            "Profit Margin",
            f"{profit_margin:.1f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            "Avg Order Value",
            f"₪{df_kpi['avg_order_value'].iloc[0]:,.0f}",
            delta=None
        )
    
    with col5:
        st.metric(
            "Total Transactions",
            f"{int(df_kpi['total_transactions'].iloc[0]):,}",
            delta=None
        )

st.markdown("---")

# ==================== REVENUE TREND ====================
st.header("📈 Sales Trends")

trend_query = f"""
SELECT 
    d.year,
    d.month,
    d.month_name,
    SUM(f.revenue) AS revenue,
    SUM(f.profit) AS profit,
    COUNT(DISTINCT f.sale_id) AS transactions
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_store s ON f.store_id = s.store_id
JOIN dim_product p ON f.product_id = p.product_id
WHERE 1=1 {where_clause}
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
"""

df_trend = execute_query(trend_query)

if not df_trend.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue Trend
        fig_revenue = px.line(
            df_trend,
            x='month_name',
            y='revenue',
            color='year',
            title='Monthly Revenue Trend',
            labels={'revenue': 'Revenue (₪)', 'month_name': 'Month'},
            markers=True
        )
        fig_revenue.update_layout(height=400)
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        # Profit Trend
        fig_profit = px.line(
            df_trend,
            x='month_name',
            y='profit',
            color='year',
            title='Monthly Profit Trend',
            labels={'profit': 'Profit (₪)', 'month_name': 'Month'},
            markers=True
        )
        fig_profit.update_layout(height=400)
        st.plotly_chart(fig_profit, use_container_width=True)

# ==================== STORE PERFORMANCE ====================
st.header("🏪 Store Performance")

store_perf_query = f"""
SELECT 
    s.store_name,
    s.city,
    s.region,
    SUM(f.revenue) AS revenue,
    SUM(f.profit) AS profit,
    SUM(f.profit) / SUM(f.revenue) * 100 AS profit_margin,
    COUNT(DISTINCT f.sale_id) AS transactions
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_store s ON f.store_id = s.store_id
JOIN dim_product p ON f.product_id = p.product_id
WHERE 1=1 {where_clause}
GROUP BY s.store_id, s.store_name, s.city, s.region
ORDER BY revenue DESC
LIMIT 15
"""

df_store_perf = execute_query(store_perf_query)

if not df_store_perf.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue by Store
        fig_store_revenue = px.bar(
            df_store_perf,
            x='revenue',
            y='store_name',
            orientation='h',
            title='Top Stores by Revenue',
            labels={'revenue': 'Revenue (₪)', 'store_name': 'Store'},
            color='revenue',
            color_continuous_scale='Blues'
        )
        fig_store_revenue.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_store_revenue, use_container_width=True)
    
    with col2:
        # Profit Margin by Store
        fig_store_margin = px.bar(
            df_store_perf,
            x='profit_margin',
            y='store_name',
            orientation='h',
            title='Profit Margin by Store',
            labels={'profit_margin': 'Profit Margin (%)', 'store_name': 'Store'},
            color='profit_margin',
            color_continuous_scale='Greens'
        )
        fig_store_margin.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_store_margin, use_container_width=True)
    
    # Store Performance Table
    st.subheader("Store Performance Details")
    display_df = df_store_perf[['store_name', 'city', 'region', 'revenue', 'profit', 'profit_margin', 'transactions']].copy()
    display_df.columns = ['Store', 'City', 'Region', 'Revenue (₪)', 'Profit (₪)', 'Profit Margin (%)', 'Transactions']
    display_df['Revenue (₪)'] = display_df['Revenue (₪)'].apply(lambda x: f"{x:,.0f}")
    display_df['Profit (₪)'] = display_df['Profit (₪)'].apply(lambda x: f"{x:,.0f}")
    display_df['Profit Margin (%)'] = display_df['Profit Margin (%)'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ==================== PRODUCT PERFORMANCE ====================
st.header("📦 Product & Category Analysis")

product_query = f"""
SELECT 
    p.category,
    p.brand,
    p.product_name,
    SUM(f.quantity) AS total_quantity,
    SUM(f.revenue) AS revenue,
    SUM(f.profit) AS profit,
    COUNT(DISTINCT f.sale_id) AS sales_count
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_store s ON f.store_id = s.store_id
JOIN dim_product p ON f.product_id = p.product_id
WHERE 1=1 {where_clause}
GROUP BY p.category, p.brand, p.product_name, p.product_id
ORDER BY revenue DESC
LIMIT 20
"""

df_products = execute_query(product_query)

if not df_products.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        # Top Products by Revenue
        fig_top_products = px.bar(
            df_products.head(10),
            x='revenue',
            y='product_name',
            orientation='h',
            title='Top 10 Products by Revenue',
            labels={'revenue': 'Revenue (₪)', 'product_name': 'Product'},
            color='revenue',
            color_continuous_scale='Purples'
        )
        fig_top_products.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_top_products, use_container_width=True)
    
    with col2:
        # Category Performance
        category_query = f"""
        SELECT 
            p.category,
            SUM(f.revenue) AS revenue,
            SUM(f.profit) AS profit,
            SUM(f.quantity) AS quantity
        FROM fact_sales f
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_id = p.product_id
        WHERE 1=1 {where_clause}
        GROUP BY p.category
        ORDER BY revenue DESC
        """
        df_categories = execute_query(category_query)
        
        if not df_categories.empty:
            fig_category = px.pie(
                df_categories,
                values='revenue',
                names='category',
                title='Revenue by Category',
                hole=0.4
            )
            fig_category.update_layout(height=400)
            st.plotly_chart(fig_category, use_container_width=True)

# ==================== CUSTOMER ANALYSIS ====================
st.header("👥 Customer Insights")

customer_query = f"""
SELECT 
    c.age_group,
    c.gender,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    SUM(f.revenue) AS revenue,
    AVG(f.revenue) AS avg_revenue_per_customer
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_store s ON f.store_id = s.store_id
JOIN dim_product p ON f.product_id = p.product_id
JOIN dim_customer c ON f.customer_id = c.customer_id
WHERE 1=1 {where_clause}
GROUP BY c.age_group, c.gender
ORDER BY c.age_group, c.gender
"""

df_customers = execute_query(customer_query)

if not df_customers.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue by Age Group
        age_revenue = df_customers.groupby('age_group')['revenue'].sum().reset_index()
        fig_age = px.bar(
            age_revenue,
            x='age_group',
            y='revenue',
            title='Revenue by Age Group',
            labels={'revenue': 'Revenue (₪)', 'age_group': 'Age Group'},
            color='revenue',
            color_continuous_scale='Oranges'
        )
        fig_age.update_layout(height=350)
        st.plotly_chart(fig_age, use_container_width=True)
    
    with col2:
        # Revenue by Gender
        gender_revenue = df_customers.groupby('gender')['revenue'].sum().reset_index()
        fig_gender = px.pie(
            gender_revenue,
            values='revenue',
            names='gender',
            title='Revenue by Gender',
            hole=0.4
        )
        fig_gender.update_layout(height=350)
        st.plotly_chart(fig_gender, use_container_width=True)

# ==================== BUSINESS INSIGHTS ====================
st.header("💡 Business Insights")

# Load insights from file
try:
    with open('insights/business_insights.md', 'r', encoding='utf-8') as f:
        insights_content = f.read()
    st.markdown(insights_content)
except:
    st.info("Business insights will be generated after data analysis")

# ==================== RAW DATA EXPLORER ====================
with st.expander("🔍 Explore Raw Data"):
    st.subheader("Data Explorer")
    
    table_options = ['fact_sales', 'dim_store', 'dim_product', 'dim_customer', 'dim_date']
    selected_table = st.selectbox("Select Table", table_options)
    
    if selected_table:
        limit = st.slider("Number of rows", 10, 1000, 100)
        query = f"SELECT * FROM {selected_table} LIMIT {limit}"
        df_raw = execute_query(query)
        if not df_raw.empty:
            st.dataframe(df_raw, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**Retail BI Dashboard** | Built with Streamlit & Plotly")

