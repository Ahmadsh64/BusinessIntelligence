"""
Retail BI Web Application - Flask Backend
Provides REST API endpoints for the BI Dashboard
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'BusinessIntelligence',
    'user': 'root',
    'password': '12345',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Create database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(query):
    """Execute SQL query and return DataFrame"""
    connection = get_db_connection()
    if connection:
        try:
            df = pd.read_sql(query, connection)
            connection.close()
            return df
        except Exception as e:
            print(f"Query error: {e}")
            connection.close()
            return pd.DataFrame()
    return pd.DataFrame()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    """Get KPI metrics"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions)
    
    query = f"""
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
    
    df = execute_query(query)
    if not df.empty and df['total_revenue'].iloc[0] is not None:
        return jsonify(df.iloc[0].to_dict())
    return jsonify({})

@app.route('/api/sales-trend', methods=['GET'])
def get_sales_trend():
    """Get monthly sales trend"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions)
    
    query = f"""
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
    
    df = execute_query(query)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/store-performance', methods=['GET'])
def get_store_performance():
    """Get store performance data"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions)
    
    query = f"""
    SELECT 
        s.store_id,
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
    
    df = execute_query(query)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/product-performance', methods=['GET'])
def get_product_performance():
    """Get product performance data"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions)
    
    query = f"""
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
    
    df = execute_query(query)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/category-revenue', methods=['GET'])
def get_category_revenue():
    """Get revenue by category"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions)
    
    query = f"""
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
    
    df = execute_query(query)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/customer-insights', methods=['GET'])
def get_customer_insights():
    """Get customer insights"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions)
    
    query = f"""
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
    
    df = execute_query(query)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/filters', methods=['GET'])
def get_filters():
    """Get filter options"""
    stores_query = "SELECT DISTINCT store_id, store_name, city FROM dim_store ORDER BY store_name"
    categories_query = "SELECT DISTINCT category FROM dim_product ORDER BY category"
    regions_query = "SELECT DISTINCT region FROM dim_store ORDER BY region"
    
    df_stores = execute_query(stores_query)
    df_categories = execute_query(categories_query)
    df_regions = execute_query(regions_query)
    
    return jsonify({
        'stores': df_stores.to_dict(orient='records'),
        'categories': df_categories['category'].tolist(),
        'regions': df_regions['region'].tolist()
    })

def build_where_clause(date_start, date_end, stores, categories, regions):
    """Build WHERE clause from filter parameters"""
    where_conditions = [f"d.date BETWEEN '{date_start}' AND '{date_end}'"]
    
    if stores:
        store_list = stores.split(',')
        where_conditions.append(f"s.store_id IN ({','.join(store_list)})")
    
    if categories:
        cat_list = categories.split(',')
        cat_list = [f"'{cat}'" for cat in cat_list]
        where_conditions.append(f"p.category IN ({','.join(cat_list)})")
    
    if regions:
        reg_list = regions.split(',')
        reg_list = [f"'{reg}'" for reg in reg_list]
        where_conditions.append(f"s.region IN ({','.join(reg_list)})")
    
    return " AND " + " AND ".join(where_conditions) if where_conditions else ""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

