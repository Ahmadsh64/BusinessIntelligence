"""
Retail BI Web Application - Flask Backend
Provides REST API endpoints for the BI Dashboard
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, Response
from flask_cors import CORS
from functools import wraps
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error, IntegrityError
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import json
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.cluster import KMeans
from io import StringIO, BytesIO
from fpdf import FPDF
import os
try:
    from prophet import Prophet
except Exception:
    Prophet = None
try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception:
    ARIMA = None

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'  # Change this in production!
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'  # Change this in production!

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'BusinessIntelligence'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '12345'),
    'charset': os.environ.get('DB_CHARSET', 'utf8mb4')
}

# SQLAlchemy engine (for pandas read_sql)
SQLALCHEMY_DB_URI = (
    f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
)
_sqlalchemy_engine = create_engine(SQLALCHEMY_DB_URI, pool_pre_ping=True)

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
    try:
        with _sqlalchemy_engine.connect() as connection:
            return pd.read_sql(query, connection)
    except Exception as e:
        print(f"Query error: {e}")
        return pd.DataFrame()

def get_export_sales_df(date_start, date_end, stores, categories, regions):
    """Fetch sales data for export based on filters."""
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    query = f"""
    SELECT 
        d.date,
        s.store_name,
        s.city,
        s.region,
        p.product_name,
        p.category,
        c.customer_name,
        c.age_group,
        f.quantity,
        f.revenue,
        f.profit
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_store s ON f.store_id = s.store_id
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_customer c ON f.customer_id = c.customer_id
    WHERE 1=1 {where_clause}
    ORDER BY d.date DESC
    LIMIT 10000
    """
    return execute_query(query)

def table_exists(table_name):
    """Check if a table exists in the database."""
    connection = get_db_connection()
    if not connection:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (DB_CONFIG['database'], table_name)
        )
        exists = cursor.fetchone()[0] > 0
        cursor.close()
        connection.close()
        return exists
    except Error as e:
        print(f"Table check error: {e}")
        connection.close()
        return False

def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    connection = get_db_connection()
    if not connection:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND column_name = %s
            """,
            (DB_CONFIG['database'], table_name, column_name)
        )
        exists = cursor.fetchone()[0] > 0
        cursor.close()
        connection.close()
        return exists
    except Error as e:
        print(f"Column check error: {e}")
        connection.close()
        return False

# ==================== AUTHENTICATION ====================

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'error': 'אין לך הרשאות לגישה לדף זה'}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_store_id():
    """Get current user's store_id from session"""
    return session.get('store_id', None)

def get_current_user_role():
    """Get current user's role from session"""
    return session.get('role', None)

def get_current_user_id():
    """Get current user's user_id from session"""
    return session.get('user_id', None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='נא למלא את כל השדות')
        
        # Check user credentials
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT user_id, store_id, username, password_hash, role FROM users WHERE username = %s AND is_active = TRUE",
                    (username,)
                )   
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password_hash'], password):
                    # Login successful
                    session['user_id'] = user['user_id']
                    session['username'] = user['username']
                    session['store_id'] = user['store_id']
                    session['role'] = user['role']
                    
                    # Update last login
                    cursor.execute(
                        "UPDATE users SET last_login = NOW() WHERE user_id = %s",
                        (user['user_id'],)
                    )
                    connection.commit()
                    
                    cursor.close()
                    connection.close()
                    
                    return redirect(url_for('index'))
                else:
                    cursor.close()
                    connection.close()
                    return render_template('login.html', error='שם משתמש או סיסמה לא נכונים')
            except Error as e:
                print(f"Database error: {e}")
                connection.close()
                return render_template('login.html', error='שגיאה בהתחברות למסד הנתונים')
        
        return render_template('login.html', error='שגיאה בהתחברות')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login (for AJAX requests)"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'נא למלא את כל השדות'}), 400
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT user_id, store_id, username, password_hash, role FROM users WHERE username = %s AND is_active = TRUE",
                (username,)
            )
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Generate JWT token
                token = jwt.encode({
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'store_id': user['store_id'],
                    'role': user['role'],
                    'exp': datetime.utcnow() + timedelta(days=1)
                }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
                
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = NOW() WHERE user_id = %s",
                    (user['user_id'],)
                )
                connection.commit()
                
                cursor.close()
                connection.close()
                
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'user_id': user['user_id'],
                        'username': user['username'],
                        'store_id': user['store_id'],
                        'role': user['role']
                    }
                })
            else:
                cursor.close()
                connection.close()
                return jsonify({'error': 'שם משתמש או סיסמה לא נכונים'}), 401
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה בהתחברות למסד הנתונים'}), 500
    
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Return empty favicon to avoid 404 errors"""
    return '', 204

@app.route('/about')
@login_required
def about():
    """About page"""
    return render_template('about.html')

@app.route('/insights')
@login_required
def insights():
    """Business insights page"""
    return render_template('insights.html')

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin page for user management"""
    return render_template('admin_users.html')

@app.route('/api/business-insights', methods=['GET'])
def get_business_insights():
    """Get dynamic business insights"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    
    where_clause = build_where_clause(date_start, date_end, '', '', '', restrict_to_store=True)
    
    # Get top performing store
    top_store_query = f"""
    SELECT s.store_name, SUM(f.revenue) AS revenue, SUM(f.profit) AS profit
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_store s ON f.store_id = s.store_id
    WHERE 1=1 {where_clause}
    GROUP BY s.store_id, s.store_name
    ORDER BY revenue DESC
    LIMIT 1
    """
    
    # Get top category
    top_category_query = f"""
    SELECT p.category, SUM(f.revenue) AS revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE 1=1 {where_clause}
    GROUP BY p.category
    ORDER BY revenue DESC
    LIMIT 1
    """
    
    df_top_store = execute_query(top_store_query)
    df_top_category = execute_query(top_category_query)
    
    insights = []
    
    if not df_top_store.empty:
        insights.append({
            'title': '🏆 סניף מוביל',
            'description': f"הסניף המוביל הוא {df_top_store.iloc[0]['store_name']} עם הכנסות של ₪{df_top_store.iloc[0]['revenue']:,.0f}",
            'metric': f"רווח: ₪{df_top_store.iloc[0]['profit']:,.0f}"
        })
    
    if not df_top_category.empty:
        insights.append({
            'title': '📦 קטגוריה מובילה',
            'description': f"הקטגוריה המובילה היא {df_top_category.iloc[0]['category']}",
            'metric': f"הכנסות: ₪{df_top_category.iloc[0]['revenue']:,.0f}"
        })
    
    return jsonify({'insights': insights})

@app.route('/api/export-csv', methods=['GET'])
@login_required
def export_csv():
    """Export data to CSV"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')

    df = get_export_sales_df(date_start, date_end, stores, categories, regions)
    
    if df.empty:
        return jsonify({'error': 'No data to export'}), 400
    
    # Create CSV
    output = StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=retail_bi_export_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

@app.route('/api/export-excel', methods=['GET'])
@login_required
def export_excel():
    """Export data to Excel"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')

    df = get_export_sales_df(date_start, date_end, stores, categories, regions)
    if df.empty:
        return jsonify({'error': 'No data to export'}), 400

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales Report')
    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename=retail_bi_report_{datetime.now().strftime("%Y%m%d")}.xlsx'}
    )

@app.route('/api/export-pdf', methods=['GET'])
@login_required
def export_pdf():
    """Export data to PDF"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')

    df = get_export_sales_df(date_start, date_end, stores, categories, regions)
    if df.empty:
        return jsonify({'error': 'No data to export'}), 400

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Sales Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=9)

    max_rows = 200
    for _, row in df.head(max_rows).iterrows():
        pdf.cell(0, 6, txt=f"{row['date']} | {row['store_name']} | {row['product_name']} | {row['quantity']} | ₪{row['revenue']}", ln=True)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=retail_bi_report_{datetime.now().strftime("%Y%m%d")}.pdf'}
    )

@app.route('/api/kpis', methods=['GET'])
@login_required
def get_kpis():
    """Get KPI metrics"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    
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
@login_required
def get_sales_trend():
    """Get monthly sales trend"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    
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
@login_required
def get_store_performance():
    """Get store performance data"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    
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
@login_required
def get_product_performance():
    """Get product performance data"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    
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
@login_required
def get_category_revenue():
    """Get revenue by category"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    
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
@login_required
def get_customer_insights():
    """Get customer insights"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    
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

@app.route('/api/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users (admin only)"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.role,
                    u.store_id,
                    s.store_name,
                    s.city,
                    u.created_at,
                    u.last_login,
                    u.is_active
                FROM users u
                LEFT JOIN dim_store s ON u.store_id = s.store_id
                ORDER BY u.created_at DESC
            """)
            users = cursor.fetchall()
            cursor.close()
            connection.close()
            
            # Convert datetime to string for JSON
            for user in users:
                if user['created_at']:
                    user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if user['last_login']:
                    user['last_login'] = user['last_login'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({'users': users})
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה בטעינת משתמשים'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Create new user (admin only)"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    store_id = data.get('store_id')
    role = data.get('role', 'store_manager')
    
    if not username or not password:
        return jsonify({'error': 'שם משתמש וסיסמה נדרשים'}), 400
    
    # Validate role
    if role not in ['admin', 'store_manager']:
        return jsonify({'error': 'תפקיד לא תקין'}), 400
    
    # If store_manager, store_id is required
    if role == 'store_manager' and not store_id:
        return jsonify({'error': 'סניף נדרש למנהל סניף'}), 400
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            password_hash = generate_password_hash(password)
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, store_id, role)
                VALUES (%s, %s, %s, %s)
            """, (username, password_hash, store_id if store_id else None, role))
            connection.commit()
            
            user_id = cursor.lastrowid
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': 'משתמש נוצר בהצלחה',
                'user_id': user_id
            }), 201
        except IntegrityError:
            connection.close()
            return jsonify({'error': 'שם משתמש כבר קיים'}), 400
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה ביצירת משתמש'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Update user (admin only)"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    store_id = data.get('store_id')
    role = data.get('role')
    is_active = data.get('is_active')
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Build update query dynamically
            updates = []
            params = []
            
            if username:
                updates.append("username = %s")
                params.append(username)
            
            if password:
                password_hash = generate_password_hash(password)
                updates.append("password_hash = %s")
                params.append(password_hash)
            
            if store_id is not None:
                updates.append("store_id = %s")
                params.append(store_id)
            
            if role:
                updates.append("role = %s")
                params.append(role)
            
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)
            
            if not updates:
                cursor.close()
                connection.close()
                return jsonify({'error': 'אין נתונים לעדכון'}), 400
            
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
            
            cursor.execute(query, params)
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': 'משתמש עודכן בהצלחה'
            })
        except IntegrityError:
            connection.close()
            return jsonify({'error': 'שם משתמש כבר קיים'}), 400
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה בעדכון משתמש'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    # Prevent deleting yourself
    if user_id == session.get('user_id'):
        return jsonify({'error': 'לא ניתן למחוק את המשתמש שלך'}), 400
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': 'משתמש נמחק בהצלחה'
            })
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה במחיקת משתמש'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """Change current user's password"""
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'נא למלא את כל השדות'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'סיסמה חייבת להכיל לפחות 6 תווים'}), 400
    
    user_id = session.get('user_id')
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT password_hash FROM users WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user or not check_password_hash(user['password_hash'], old_password):
                cursor.close()
                connection.close()
                return jsonify({'error': 'סיסמה ישנה לא נכונה'}), 400
            
            # Update password
            new_password_hash = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                (new_password_hash, user_id)
            )
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': 'סיסמה שונתה בהצלחה'
            })
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה בשינוי סיסמה'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/user-settings', methods=['GET', 'PUT'])
@login_required
def user_settings():
    """Get or update user preferences (theme, etc.)"""
    if not table_exists('user_settings'):
        return jsonify({'theme': 'light', 'note': 'טבלת user_settings לא קיימת.'})

    user_id = get_current_user_id()
    if request.method == 'GET':
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT theme, chart_style FROM user_settings WHERE user_id = %s",
                    (user_id,)
                )
                row = cursor.fetchone()
                cursor.close()
                connection.close()
                if not row:
                    return jsonify({'theme': 'light', 'chart_style': 'default'})
                return jsonify(row)
            except Error as e:
                print(f"Database error: {e}")
                connection.close()
                return jsonify({'error': 'שגיאה בשליפת הגדרות'}), 500
        return jsonify({'error': 'שגיאה בהתחברות'}), 500

    data = request.get_json() or {}
    theme = (data.get('theme') or 'light').lower()
    chart_style = data.get('chart_style') or 'default'
    if theme not in ['light', 'dark']:
        return jsonify({'error': 'ערך theme לא תקין'}), 400

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO user_settings (user_id, theme, chart_style)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    theme = VALUES(theme),
                    chart_style = VALUES(chart_style),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, theme, chart_style)
            )
            connection.commit()
            cursor.close()
            connection.close()
            return jsonify({'success': True, 'theme': theme, 'chart_style': chart_style})
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה בעדכון הגדרות'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get notifications for current user"""
    user_id = session.get('user_id')
    user_role = session.get('role')
    user_store_id = session.get('store_id')
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Build query based on user role
            if user_role == 'admin':
                query = """
                    SELECT 
                        n.notification_id,
                        n.type,
                        n.title,
                        n.message,
                        n.severity,
                        n.is_read,
                        n.created_at,
                        s.store_name
                    FROM notifications n
                    LEFT JOIN dim_store s ON n.store_id = s.store_id
                    WHERE n.user_id IS NULL OR n.user_id = %s
                    ORDER BY n.created_at DESC
                    LIMIT 50
                """
                cursor.execute(query, (user_id,))
            else:
                # Store managers see only their store notifications
                query = """
                    SELECT 
                        n.notification_id,
                        n.type,
                        n.title,
                        n.message,
                        n.severity,
                        n.is_read,
                        n.created_at,
                        s.store_name
                    FROM notifications n
                    LEFT JOIN dim_store s ON n.store_id = s.store_id
                    WHERE (n.user_id IS NULL OR n.user_id = %s)
                    AND (n.store_id IS NULL OR n.store_id = %s)
                    ORDER BY n.created_at DESC
                    LIMIT 50
                """
                cursor.execute(query, (user_id, user_store_id))
            
            notifications = cursor.fetchall()
            
            # Convert datetime to string
            for notif in notifications:
                if notif['created_at']:
                    notif['created_at'] = notif['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Count unread
            unread_count = sum(1 for n in notifications if not n['is_read'])
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'notifications': notifications,
            
                'unread_count': unread_count
            })
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה בטעינת התראות'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE notifications SET is_read = TRUE WHERE notification_id = %s",
                (notification_id,)
            )
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({'success': True})
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה בעדכון התראה'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/notifications/read-all', methods=['PUT'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    user_id = session.get('user_id')
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE notifications SET is_read = TRUE WHERE user_id = %s OR user_id IS NULL",
                (user_id,)
            )
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({'success': True})
        except Error as e:
            print(f"Database error: {e}")
            connection.close()
            return jsonify({'error': 'שגיאה בעדכון התראות'}), 500
    return jsonify({'error': 'שגיאה בהתחברות'}), 500

@app.route('/api/anomaly-detection', methods=['GET'])
@login_required
def detect_anomalies():
    """Detect anomalies in sales data"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    
    where_clause = build_where_clause(date_start, date_end, '', '', '', restrict_to_store=True)
    
    # Get daily sales data
    query = f"""
    SELECT 
        d.date,
        SUM(f.revenue) AS daily_revenue,
        SUM(f.quantity) AS daily_quantity,
        COUNT(DISTINCT f.sale_id) AS daily_transactions
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_store s ON f.store_id = s.store_id
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE 1=1 {where_clause}
    GROUP BY d.date
    ORDER BY d.date
    """
    
    df = execute_query(query)
    
    if df.empty or len(df) < 7:
        return jsonify({'anomalies': [], 'message': 'לא מספיק נתונים לזיהוי אנומליות'})
    
    anomalies = []
    
    # Calculate statistics
    mean_revenue = df['daily_revenue'].mean()
    std_revenue = df['daily_revenue'].std()
    
    # Detect outliers (beyond 2 standard deviations)
    threshold = 2 * std_revenue
    
    for _, row in df.iterrows():
        if abs(row['daily_revenue'] - mean_revenue) > threshold:
            anomalies.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'revenue': float(row['daily_revenue']),
                'expected_revenue': float(mean_revenue),
                'deviation': float((row['daily_revenue'] - mean_revenue) / mean_revenue * 100),
                'type': 'high' if row['daily_revenue'] > mean_revenue else 'low'
            })
    
    return jsonify({
        'anomalies': anomalies,
        'statistics': {
            'mean_revenue': float(mean_revenue),
            'std_revenue': float(std_revenue),
            'total_days': len(df)
        }
    })

@app.route('/api/customer-segments', methods=['GET'])
@login_required
def get_customer_segments():
    """Segment customers using KMeans clustering"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    n_clusters = int(request.args.get('clusters', 4))

    where_clause = build_where_clause(date_start, date_end, '', '', '', restrict_to_store=True)

    query = f"""
    SELECT 
        c.customer_id,
        c.age_group,
        c.gender,
        COUNT(DISTINCT f.sale_id) AS transactions,
        SUM(f.revenue) AS total_revenue,
        AVG(f.revenue) AS avg_order_value,
        SUM(f.quantity) AS total_quantity
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_store s ON f.store_id = s.store_id
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE 1=1 {where_clause}
    GROUP BY c.customer_id, c.age_group, c.gender
    """

    df = execute_query(query)

    if df.empty or len(df) < n_clusters:
        return jsonify({
            'segments': [],
            'message': 'לא מספיק נתונים לחלוקה לקבוצות'
        })

    features = df[['transactions', 'total_revenue', 'avg_order_value', 'total_quantity']].fillna(0)
    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['segment'] = kmeans.fit_predict(X)

    # Build summary per segment
    segment_summary = df.groupby('segment').agg({
        'customer_id': 'count',
        'transactions': 'mean',
        'total_revenue': 'mean',
        'avg_order_value': 'mean',
        'total_quantity': 'mean'
    }).reset_index()

    segment_summary.rename(columns={
        'customer_id': 'customers_count',
        'transactions': 'avg_transactions',
        'total_revenue': 'avg_revenue',
        'avg_order_value': 'avg_order_value',
        'total_quantity': 'avg_quantity'
    }, inplace=True)

    return jsonify({
        'segments': segment_summary.to_dict(orient='records'),
        'customers': df[['customer_id', 'age_group', 'gender', 'segment']].to_dict(orient='records')
    })

@app.route('/api/filters', methods=['GET'])
@login_required
def get_filters():
    """Get filter options"""
    user_role = get_current_user_role()
    user_store_id = get_current_user_store_id()

    if user_role != 'admin' and user_store_id:
        stores_query = f"""
        SELECT DISTINCT store_id, store_name, city
        FROM dim_store
        WHERE store_id = {user_store_id}
        ORDER BY store_name
        """
        categories_query = f"""
        SELECT DISTINCT p.category
        FROM fact_sales f
        JOIN dim_product p ON f.product_id = p.product_id
        JOIN dim_store s ON f.store_id = s.store_id
        WHERE s.store_id = {user_store_id}
        ORDER BY p.category
        """
        regions_query = f"""
        SELECT DISTINCT region
        FROM dim_store
        WHERE store_id = {user_store_id}
        ORDER BY region
        """
    else:
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

@app.route('/api/inventory-optimization', methods=['GET'])
@login_required
def inventory_optimization():
    """Calculate optimal inventory levels (EOQ + Reorder Point)."""
    days_back = int(request.args.get('days', 60))
    lead_time_days = int(request.args.get('lead_time_days', 7))
    holding_cost_rate = float(request.args.get('holding_cost_rate', 0.2))  # % of unit cost per year
    ordering_cost = float(request.args.get('ordering_cost', 50))  # fixed cost per order
    update_levels = request.args.get('update', 'false').lower() == 'true'

    user_role = get_current_user_role()
    user_store_id = get_current_user_store_id()

    store_filter = ""
    if user_role != 'admin' and user_store_id:
        store_filter = f"AND s.store_id = {user_store_id}"

    inventory_table_ready = table_exists('inventory_levels') and column_exists('inventory_levels', 'current_quantity')

    if inventory_table_ready:
        query = f"""
        SELECT 
            s.store_id,
            s.store_name,
            p.product_id,
            p.product_name,
            p.cost AS unit_cost,
            SUM(f.quantity) AS total_qty,
            COUNT(DISTINCT d.date) AS sales_days,
            COALESCE(i.current_quantity, 0) AS current_stock
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_id = p.product_id
        JOIN dim_date d ON f.date_id = d.date_id
        LEFT JOIN inventory_levels i 
            ON i.store_id = s.store_id AND i.product_id = p.product_id
        WHERE d.date >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
        {store_filter}
        GROUP BY s.store_id, s.store_name, p.product_id, p.product_name, p.cost, i.current_quantity
        """
    else:
        query = f"""
        SELECT 
            s.store_id,
            s.store_name,
            p.product_id,
            p.product_name,
            p.cost AS unit_cost,
            SUM(f.quantity) AS total_qty,
            COUNT(DISTINCT d.date) AS sales_days,
            0 AS current_stock
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_id = p.product_id
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE d.date >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
        {store_filter}
        GROUP BY s.store_id, s.store_name, p.product_id, p.product_name, p.cost
        """

    df = execute_query(query)

    if df.empty:
        return jsonify({'items': [], 'message': 'אין נתונים לחישוב מלאי'}), 200

    results = []
    if update_levels and not inventory_table_ready:
        update_levels = False

    connection = get_db_connection() if update_levels else None
    cursor = connection.cursor() if connection else None

    for _, row in df.iterrows():
        if row['sales_days'] == 0:
            continue

        daily_demand = row['total_qty'] / max(row['sales_days'], 1)
        annual_demand = daily_demand * 365
        holding_cost = max(row['unit_cost'], 1) * holding_cost_rate

        # EOQ formula
        eoq = int(max(1, (2 * annual_demand * ordering_cost / max(holding_cost, 1)) ** 0.5))

        # Reorder point (basic): demand during lead time + safety stock (10% buffer)
        reorder_point = int(daily_demand * lead_time_days * 1.1)

        # Suggested min/max levels
        min_level = max(1, int(reorder_point * 0.8))
        max_level = int(reorder_point + eoq)

        results.append({
            'store_id': int(row['store_id']),
            'store_name': row['store_name'],
            'product_id': int(row['product_id']),
            'product_name': row['product_name'],
            'current_stock': int(row['current_stock']),
            'daily_demand': round(daily_demand, 2),
            'eoq': eoq,
            'reorder_point': reorder_point,
            'min_level': min_level,
            'max_level': max_level
        })

        if update_levels and cursor:
            cursor.execute("""
                INSERT INTO inventory_levels (store_id, product_id, current_quantity, min_quantity, max_quantity, reorder_point)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    min_quantity = VALUES(min_quantity),
                    max_quantity = VALUES(max_quantity),
                    reorder_point = VALUES(reorder_point)
            """, (
                int(row['store_id']),
                int(row['product_id']),
                int(row['current_stock']),
                min_level,
                max_level,
                reorder_point
            ))

    if update_levels and connection:
        connection.commit()
        cursor.close()
        connection.close()

    response = {'items': results, 'parameters': {
        'days_back': days_back,
        'lead_time_days': lead_time_days,
        'holding_cost_rate': holding_cost_rate,
        'ordering_cost': ordering_cost,
        'updated': update_levels
    }}

    if not inventory_table_ready:
        response['note'] = 'טבלת inventory_levels לא קיימת או חסרה עמודה. החישוב בוצע ללא מלאי נוכחי.'

    return jsonify(response)

@app.route('/api/inventory-reorder-suggestions', methods=['GET'])
@login_required
def inventory_reorder_suggestions():
    """Suggest reorders based on current stock vs reorder point."""
    user_role = get_current_user_role()
    user_store_id = get_current_user_store_id()
    auto_order = request.args.get('auto_order', 'false').lower() == 'true'

    if not table_exists('inventory_levels') or not column_exists('inventory_levels', 'current_quantity'):
        return jsonify({'suggestions': [], 'note': 'טבלת inventory_levels לא קיימת או חסרה עמודה.'})

    store_filter = ""
    if user_role != 'admin' and user_store_id:
        store_filter = f"WHERE i.store_id = {user_store_id}"

    query = f"""
    SELECT 
        i.store_id,
        s.store_name,
        i.product_id,
        p.product_name,
        i.current_quantity,
        i.reorder_point,
        i.max_quantity
    FROM inventory_levels i
    JOIN dim_store s ON i.store_id = s.store_id
    JOIN dim_product p ON i.product_id = p.product_id
    {store_filter}
    """

    df = execute_query(query)
    if df.empty:
        return jsonify({'suggestions': []})

    suggestions = []
    connection = get_db_connection() if auto_order else None
    cursor = connection.cursor() if connection else None

    for _, row in df.iterrows():
        if row['current_quantity'] <= row['reorder_point']:
            reorder_qty = max(0, int(row['max_quantity']) - int(row['current_quantity']))
            suggestions.append({
                'store_id': int(row['store_id']),
                'store_name': row['store_name'],
                'product_id': int(row['product_id']),
                'product_name': row['product_name'],
                'current_stock': int(row['current_quantity']),
                'reorder_point': int(row['reorder_point']),
                'suggested_order_qty': reorder_qty
            })

            if auto_order and cursor:
                cursor.execute("""
                    INSERT INTO notifications (type, title, message, severity, store_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    'low_stock',
                    f'הזמנה אוטומטית - {row["product_name"]}',
                    f'נוצרה הצעת הזמנה אוטומטית של {reorder_qty} יחידות עבור {row["product_name"]} בסניף {row["store_name"]}.',
                    'warning',
                    int(row['store_id'])
                ))

    if auto_order and connection:
        connection.commit()
        cursor.close()
        connection.close()

    return jsonify({'suggestions': suggestions, 'auto_order': auto_order})

@app.route('/api/inventory-auto-orders', methods=['GET'])
@login_required
def inventory_auto_orders():
    """Auto order suggestions using EOQ and reorder point."""
    days_back = int(request.args.get('days', 60))
    lead_time_days = int(request.args.get('lead_time_days', 7))
    holding_cost_rate = float(request.args.get('holding_cost_rate', 0.2))
    ordering_cost = float(request.args.get('ordering_cost', 50))
    auto_order = request.args.get('auto_order', 'false').lower() == 'true'

    if not table_exists('inventory_levels') or not column_exists('inventory_levels', 'current_quantity'):
        return jsonify({'suggestions': [], 'note': 'טבלת inventory_levels לא קיימת או חסרה עמודה.'})

    user_role = get_current_user_role()
    user_store_id = get_current_user_store_id()
    store_filter = ""
    if user_role != 'admin' and user_store_id:
        store_filter = f"AND s.store_id = {user_store_id}"

    query = f"""
    SELECT 
        s.store_id,
        s.store_name,
        p.product_id,
        p.product_name,
        p.cost AS unit_cost,
        COALESCE(i.current_quantity, 0) AS current_quantity,
        COALESCE(i.reorder_point, 0) AS reorder_point,
        COALESCE(i.max_quantity, 0) AS max_quantity,
        SUM(f.quantity) AS total_qty,
        COUNT(DISTINCT d.date) AS sales_days
    FROM fact_sales f
    JOIN dim_store s ON f.store_id = s.store_id
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_date d ON f.date_id = d.date_id
    LEFT JOIN inventory_levels i
        ON i.store_id = s.store_id AND i.product_id = p.product_id
    WHERE d.date >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
    {store_filter}
    GROUP BY s.store_id, s.store_name, p.product_id, p.product_name, p.cost, i.current_quantity, i.reorder_point, i.max_quantity
    """

    df = execute_query(query)
    if df.empty:
        return jsonify({'suggestions': []})

    suggestions = []
    connection = get_db_connection() if auto_order else None
    cursor = connection.cursor() if connection else None

    for _, row in df.iterrows():
        if row['sales_days'] == 0:
            continue

        daily_demand = row['total_qty'] / max(row['sales_days'], 1)
        annual_demand = daily_demand * 365
        holding_cost = max(row['unit_cost'], 1) * holding_cost_rate
        eoq = int(max(1, (2 * annual_demand * ordering_cost / max(holding_cost, 1)) ** 0.5))

        reorder_point = int(row['reorder_point']) if int(row['reorder_point']) > 0 else int(daily_demand * lead_time_days * 1.1)
        max_level = int(row['max_quantity']) if int(row['max_quantity']) > 0 else int(reorder_point + eoq)

        if int(row['current_quantity']) <= reorder_point:
            suggested_qty = max(eoq, max_level - int(row['current_quantity']))
            suggestions.append({
                'store_id': int(row['store_id']),
                'store_name': row['store_name'],
                'product_id': int(row['product_id']),
                'product_name': row['product_name'],
                'current_stock': int(row['current_quantity']),
                'reorder_point': reorder_point,
                'eoq': eoq,
                'suggested_order_qty': int(suggested_qty)
            })

            if auto_order and cursor:
                cursor.execute("""
                    INSERT INTO notifications (type, title, message, severity, store_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    'auto_order',
                    f'הזמנה אוטומטית - {row["product_name"]}',
                    f'הומלצה הזמנה אוטומטית של {int(suggested_qty)} יחידות עבור {row["product_name"]} בסניף {row["store_name"]}.',
                    'warning',
                    int(row['store_id'])
                ))

    if auto_order and connection:
        connection.commit()
        cursor.close()
        connection.close()

    return jsonify({
        'suggestions': suggestions,
        'parameters': {
            'days_back': days_back,
            'lead_time_days': lead_time_days,
            'holding_cost_rate': holding_cost_rate,
            'ordering_cost': ordering_cost,
            'auto_order': auto_order
        }
    })

@app.route('/api/inventory-availability', methods=['GET'])
@login_required
def inventory_availability():
    """Show store and central warehouse availability."""
    user_role = get_current_user_role()
    user_store_id = get_current_user_store_id()

    if not table_exists('inventory_levels') or not column_exists('inventory_levels', 'current_quantity'):
        return jsonify({'availability': [], 'note': 'טבלת inventory_levels לא קיימת או חסרה עמודה.'})

    store_filter = ""
    if user_role != 'admin' and user_store_id:
        store_filter = f"WHERE i.store_id = {user_store_id}"

    central_ready = table_exists('central_inventory') and column_exists('central_inventory', 'current_stock')

    if central_ready:
        query = f"""
        SELECT 
            i.store_id,
            s.store_name,
            i.product_id,
            p.product_name,
            i.current_quantity AS store_stock,
            COALESCE(c.current_stock, 0) AS central_stock
        FROM inventory_levels i
        JOIN dim_store s ON i.store_id = s.store_id
        JOIN dim_product p ON i.product_id = p.product_id
        LEFT JOIN central_inventory c ON c.product_id = i.product_id
        {store_filter}
        """
    else:
        query = f"""
        SELECT 
            i.store_id,
            s.store_name,
            i.product_id,
            p.product_name,
            i.current_quantity AS store_stock,
            0 AS central_stock
        FROM inventory_levels i
        JOIN dim_store s ON i.store_id = s.store_id
        JOIN dim_product p ON i.product_id = p.product_id
        {store_filter}
        """

    df = execute_query(query)
    response = {'availability': df.to_dict(orient='records')}
    if not central_ready:
        response['note'] = 'טבלת central_inventory לא קיימת. מוצג מלאי סניפים בלבד.'
    return jsonify(response)

@app.route('/api/inventory-levels', methods=['GET'])
@login_required
def get_inventory_levels():
    """Return inventory details with quantities and thresholds."""
    user_role = get_current_user_role()
    user_store_id = get_current_user_store_id()

    if not table_exists('inventory_levels') or not column_exists('inventory_levels', 'current_quantity'):
        return jsonify({'inventory': [], 'note': 'טבלת inventory_levels לא קיימת או חסרה עמודה.'})

    store_filter = ""
    if user_role != 'admin' and user_store_id:
        store_filter = f"WHERE i.store_id = {user_store_id}"

    query = f"""
    SELECT 
        i.store_id,
        s.store_name,
        i.product_id,
        p.product_name,
        i.current_quantity,
        i.min_quantity,
        i.max_quantity,
        i.reorder_point,
        i.last_updated
    FROM inventory_levels i
    JOIN dim_store s ON i.store_id = s.store_id
    JOIN dim_product p ON i.product_id = p.product_id
    {store_filter}
    ORDER BY i.last_updated DESC
    LIMIT 500
    """

    df = execute_query(query)
    return jsonify({'inventory': df.to_dict(orient='records')})

@app.route('/api/seasonal-analysis', methods=['GET'])
@login_required
def get_seasonal_analysis():
    """Get seasonal analysis - quarterly and monthly patterns"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    
    # Quarterly analysis
    quarterly_query = f"""
    SELECT 
        d.year,
        d.quarter,
        d.quarter_name,
        SUM(f.revenue) AS revenue,
        SUM(f.profit) AS profit,
        COUNT(DISTINCT f.sale_id) AS transactions,
        AVG(f.revenue) AS avg_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_store s ON f.store_id = s.store_id
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE 1=1 {where_clause}
    GROUP BY d.year, d.quarter, d.quarter_name
    ORDER BY d.year, d.quarter
    """
    
    # Monthly comparison (average by month across years)
    monthly_query = f"""
    SELECT 
        monthly_data.month,
        monthly_data.month_name,
        AVG(monthly_data.monthly_revenue) AS avg_revenue,
        AVG(monthly_data.monthly_profit) AS avg_profit,
        COUNT(*) AS year_count
    FROM (
        SELECT 
            d.year,
            d.month,
            d.month_name,
            SUM(f.revenue) AS monthly_revenue,
            SUM(f.profit) AS monthly_profit
        FROM fact_sales f
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_id = p.product_id
        WHERE 1=1 {where_clause}
        GROUP BY d.year, d.month, d.month_name
    ) AS monthly_data
    GROUP BY monthly_data.month, monthly_data.month_name
    ORDER BY monthly_data.month
    """
    
    df_quarterly = execute_query(quarterly_query)
    df_monthly = execute_query(monthly_query)
    
    # Calculate seasonal insights
    insights = []
    if not df_monthly.empty:
        max_month = df_monthly.loc[df_monthly['avg_revenue'].idxmax()]
        min_month = df_monthly.loc[df_monthly['avg_revenue'].idxmin()]
        avg_revenue = df_monthly['avg_revenue'].mean()
        
        insights.append({
            'type': 'peak_month',
            'month': max_month['month_name'],
            'revenue': float(max_month['avg_revenue']),
            'percentage_above_avg': float((max_month['avg_revenue'] / avg_revenue - 1) * 100)
        })
        
        insights.append({
            'type': 'low_month',
            'month': min_month['month_name'],
            'revenue': float(min_month['avg_revenue']),
            'percentage_below_avg': float((1 - min_month['avg_revenue'] / avg_revenue) * 100)
        })
    
    return jsonify({
        'quarterly': df_quarterly.to_dict(orient='records'),
        'monthly': df_monthly.to_dict(orient='records'),
        'insights': insights
    })

@app.route('/api/sales-forecast', methods=['GET'])
@login_required
def get_sales_forecast():
    """Predict future sales using simple linear regression"""
    date_start = request.args.get('date_start', '2023-01-01')
    date_end = request.args.get('date_end', datetime.now().strftime('%Y-%m-%d'))
    forecast_months = int(request.args.get('months', 6))  # Default 6 months ahead
    model_type = request.args.get('model', 'linear').lower()
    arima_order = request.args.get('arima_order', '1,1,1')
    stores = request.args.get('stores', '')
    categories = request.args.get('categories', '')
    regions = request.args.get('regions', '')
    
    where_clause = build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=True)
    
    # Get historical monthly data
    query = f"""
    SELECT 
        d.year,
        d.month,
        d.month_name,
        SUM(f.revenue) AS revenue,
        SUM(f.profit) AS profit
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN dim_store s ON f.store_id = s.store_id
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE 1=1 {where_clause}
    GROUP BY d.year, d.month, d.month_name
    ORDER BY d.year, d.month
    """
    
    df = execute_query(query)
    
    if df.empty or len(df) < 3:
        # Try to get all available data if the date range has no data
        # But still restrict to user's store if not admin
        user_role = get_current_user_role()
        user_store_id = get_current_user_store_id()
        store_restriction = ""
        if user_role != 'admin' and user_store_id:
            store_restriction = f"AND s.store_id = {user_store_id}"
        
        fallback_query = f"""
        SELECT 
            d.year,
            d.month,
            d.month_name,
            SUM(f.revenue) AS revenue,
            SUM(f.profit) AS profit
        FROM fact_sales f
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_store s ON f.store_id = s.store_id
        JOIN dim_product p ON f.product_id = p.product_id
        WHERE 1=1 {store_restriction}
        GROUP BY d.year, d.month, d.month_name
        ORDER BY d.year, d.month
        """
        df = execute_query(fallback_query)
        
        if df.empty or len(df) < 3:
            return jsonify({'error': 'Not enough data for forecasting. Need at least 3 months of data.'}), 400

    # Prepare data for forecasting
    df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
    df = df.sort_values('date')
    df['period'] = range(len(df))
    X = df[['period']].values
    y_revenue = df['revenue'].values
    y_profit = df['profit'].values

    # Generate future dates based on last available data
    last_date = df['date'].max()
    forecast_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=forecast_months, freq='MS')

    forecast_revenue = None
    forecast_profit = None
    model_accuracy = {'revenue_r2': None, 'profit_r2': None}

    if model_type == 'prophet':
        if Prophet is None:
            return jsonify({'error': 'Prophet is not installed. Install prophet to use this model.'}), 400
        if len(df) < 3:
            return jsonify({'error': 'Not enough data for Prophet. Need at least 3 months of data.'}), 400

        prophet_df = df[['date', 'revenue']].rename(columns={'date': 'ds', 'revenue': 'y'})
        prophet_profit_df = df[['date', 'profit']].rename(columns={'date': 'ds', 'profit': 'y'})

        model_revenue = Prophet()
        model_revenue.fit(prophet_df)
        model_profit = Prophet()
        model_profit.fit(prophet_profit_df)

        future = model_revenue.make_future_dataframe(periods=forecast_months, freq='MS')
        revenue_forecast = model_revenue.predict(future).tail(forecast_months)
        profit_forecast = model_profit.predict(future).tail(forecast_months)

        forecast_revenue = revenue_forecast['yhat'].values
        forecast_profit = profit_forecast['yhat'].values
    elif model_type == 'arima':
        if ARIMA is None:
            return jsonify({'error': 'statsmodels is not installed. Install statsmodels to use ARIMA.'}), 400
        try:
            order = tuple(int(x.strip()) for x in arima_order.split(','))
            if len(order) != 3:
                raise ValueError("Invalid ARIMA order")
        except Exception:
            return jsonify({'error': 'Invalid ARIMA order. Use format p,d,q (e.g., 1,1,1).'}), 400

        model_revenue = ARIMA(y_revenue, order=order).fit()
        model_profit = ARIMA(y_profit, order=order).fit()
        forecast_revenue = model_revenue.forecast(steps=forecast_months)
        forecast_profit = model_profit.forecast(steps=forecast_months)
    else:
        # Simple linear regression for revenue
        model_revenue = LinearRegression()
        model_revenue.fit(X, y_revenue)

        # Forecast future periods
        last_period = len(df) - 1
        future_periods = range(last_period + 1, last_period + 1 + forecast_months)
        future_X = np.array([[p] for p in future_periods])

        # Predict revenue
        forecast_revenue = model_revenue.predict(future_X)

        # Predict profit (using same trend as revenue)
        model_profit = LinearRegression()
        model_profit.fit(X, y_profit)
        forecast_profit = model_profit.predict(future_X)

        model_accuracy = {
            'revenue_r2': float(model_revenue.score(X, y_revenue)),
            'profit_r2': float(model_profit.score(X, y_profit))
        }

    # Combine historical and forecast
    historical = df[['year', 'month', 'month_name', 'revenue', 'profit']].to_dict(orient='records')
    
    forecast = []
    for i, date_val in enumerate(forecast_dates):
        year = date_val.year
        month = date_val.month
        month_names = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
                      'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר']
        forecast.append({
            'year': int(year),
            'month': int(month),
            'month_name': month_names[int(month) - 1],
            'revenue': float(forecast_revenue[i]),
            'profit': float(forecast_profit[i]),
            'is_forecast': True
        })
    
    return jsonify({
        'historical': historical,
        'forecast': forecast,
        'model_accuracy': model_accuracy,
        'model_type': model_type
    })

def build_where_clause(date_start, date_end, stores, categories, regions, restrict_to_store=False):
    """Build WHERE clause from filter parameters"""
    where_conditions = [f"d.date BETWEEN '{date_start}' AND '{date_end}'"]
    
    # Restrict to user's store if not admin
    user_role = get_current_user_role()
    user_store_id = get_current_user_store_id()
    
    if restrict_to_store and user_role != 'admin' and user_store_id:
        where_conditions.append(f"s.store_id = {user_store_id}")
    elif stores:
        # If user is not admin, only allow their store
        if user_role != 'admin' and user_store_id:
            if str(user_store_id) not in stores.split(','):
                where_conditions.append(f"s.store_id = {user_store_id}")
            else:
                store_list = stores.split(',')
                where_conditions.append(f"s.store_id IN ({','.join(store_list)})")
        else:
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

