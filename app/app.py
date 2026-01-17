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
from datetime import datetime, timedelta
import json
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'  # Change this in production!
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'  # Change this in production!

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
    
    df = execute_query(query)
    
    if df.empty:
        return jsonify({'error': 'No data to export'}), 400
    
    # Create CSV
    from io import StringIO
    output = StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=retail_bi_export_{datetime.now().strftime("%Y%m%d")}.csv'}
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

@app.route('/api/filters', methods=['GET'])
@login_required
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
        d.month,
        d.month_name,
        AVG(monthly_revenue) AS avg_revenue,
        AVG(monthly_profit) AS avg_profit,
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
    GROUP BY d.month, d.month_name
    ORDER BY d.month
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
    df['period'] = range(len(df))
    X = df[['period']].values
    y_revenue = df['revenue'].values
    y_profit = df['profit'].values
    
    # Simple linear regression for revenue
    model_revenue = LinearRegression()
    model_revenue.fit(X, y_revenue)
    
    # Polynomial regression for better fit (if enough data)
    if len(df) >= 6:
        poly_features = PolynomialFeatures(degree=2)
        X_poly = poly_features.fit_transform(X)
        model_revenue_poly = LinearRegression()
        model_revenue_poly.fit(X_poly, y_revenue)
    
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
    
    # Generate future dates
    last_date = datetime.strptime(date_end, '%Y-%m-%d')
    forecast_dates = []
    current_date = last_date
    
    for i in range(forecast_months):
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1, day=1)
        forecast_dates.append(current_date.strftime('%Y-%m'))
    
    # Combine historical and forecast
    historical = df[['year', 'month', 'month_name', 'revenue', 'profit']].to_dict(orient='records')
    
    forecast = []
    for i, date_str in enumerate(forecast_dates):
        year, month = date_str.split('-')
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
        'model_accuracy': {
            'revenue_r2': float(model_revenue.score(X, y_revenue)),
            'profit_r2': float(model_profit.score(X, y_profit))
        }
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

