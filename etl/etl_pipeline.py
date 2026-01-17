"""
ETL Pipeline for Retail BI Project
Extracts data from Excel, transforms it, and loads into Data Warehouse
"""

import pandas as pd
import numpy as np
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import os
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# Configuration
EXCEL_DIR = 'data/raw_excel'
DB_CONFIG = {
    'host': 'localhost',
    'database': 'BusinessIntelligence',
    'user': 'root',
    'password': '12345',  # Change this to your MySQL password
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def create_database_connection():
    """Create connection to MySQL database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✓ Connected to MySQL database")
            return connection
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        print("\nNote: Make sure MySQL is running and database 'retail_bi' exists")
        return None

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Connect without specifying database
        config_temp = DB_CONFIG.copy()
        config_temp.pop('database', None)
        connection = mysql.connector.connect(**config_temp)
        cursor = connection.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ Database '{DB_CONFIG['database']}' ready")
        
        cursor.close()
        connection.close()
    except Error as e:
        print(f"✗ Error creating database: {e}")

def load_sql_schema(connection):
    """Load SQL schema from file"""
    try:
        with open('warehouse/star_schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Split by semicolon and execute each statement
        cursor = connection.cursor()
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except Error as e:
                    # Ignore errors for DROP TABLE IF EXISTS if tables don't exist
                    if 'DROP TABLE' not in statement.upper():
                        print(f"Warning: {e}")
        
        connection.commit()
        cursor.close()
        print("✓ Database schema loaded successfully")
    except Exception as e:
        print(f"✗ Error loading schema: {e}")

def extract_excel_data():
    """Extract data from Excel files"""
    print("\n" + "="*50)
    print("EXTRACTING DATA FROM EXCEL FILES")
    print("="*50)
    
    try:
        # Load all Excel files
        df_stores = pd.read_excel(f'{EXCEL_DIR}/stores.xlsx')
        df_products = pd.read_excel(f'{EXCEL_DIR}/products.xlsx')
        df_customers = pd.read_excel(f'{EXCEL_DIR}/customers.xlsx')
        df_sales = pd.read_excel(f'{EXCEL_DIR}/sales_raw.xlsx')
        
        print(f"✓ Loaded stores: {len(df_stores)} rows")
        print(f"✓ Loaded products: {len(df_products)} rows")
        print(f"✓ Loaded customers: {len(df_customers)} rows")
        print(f"✓ Loaded sales: {len(df_sales)} rows")
        
        return df_stores, df_products, df_customers, df_sales
    except Exception as e:
        print(f"✗ Error loading Excel files: {e}")
        return None, None, None, None

def validate_data(df_stores, df_products, df_customers, df_sales):
    """Validate and clean data with comprehensive data quality checks"""
    print("\n" + "="*50)
    print("VALIDATING AND CLEANING DATA")
    print("="*50)
    
    quality_report = {
        'missing_values': {},
        'duplicates': {},
        'outliers': {},
        'data_types': {},
        'business_rules': {}
    }
    
    # Check for missing values
    print("\n[1/5] Checking for missing values...")
    for name, df in [('Stores', df_stores), ('Products', df_products), 
                     ('Customers', df_customers), ('Sales', df_sales)]:
        missing = df.isnull().sum()
        if missing.any():
            print(f"  ⚠ {name} - Missing values found:")
            for col, count in missing[missing > 0].items():
                print(f"    - {col}: {count} ({count/len(df)*100:.1f}%)")
            quality_report['missing_values'][name] = missing[missing > 0].to_dict()
        else:
            print(f"  ✓ {name} - No missing values")
            quality_report['missing_values'][name] = {}
    
    # Check for duplicates
    print("\n[2/5] Checking for duplicates...")
    for name, df, key_col in [('Stores', df_stores, 'store_id'),
                              ('Products', df_products, 'product_id'),
                              ('Customers', df_customers, 'customer_id'),
                              ('Sales', df_sales, 'sale_id')]:
        duplicates = df.duplicated(subset=[key_col]).sum()
        if duplicates > 0:
            print(f"  ⚠ {name} - Found {duplicates} duplicate {key_col}s")
            quality_report['duplicates'][name] = duplicates
            # Remove duplicates, keep first
            df = df.drop_duplicates(subset=[key_col], keep='first')
            if name == 'Stores':
                df_stores = df
            elif name == 'Products':
                df_products = df
            elif name == 'Customers':
                df_customers = df
            else:
                df_sales = df
        else:
            print(f"  ✓ {name} - No duplicates")
            quality_report['duplicates'][name] = 0
    
    # Check for outliers (using IQR method)
    print("\n[3/5] Checking for outliers...")
    if 'revenue' in df_sales.columns:
        Q1 = df_sales['revenue'].quantile(0.25)
        Q3 = df_sales['revenue'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df_sales[(df_sales['revenue'] < lower_bound) | 
                            (df_sales['revenue'] > upper_bound)]
        outlier_count = len(outliers)
        
        if outlier_count > 0:
            print(f"  ⚠ Sales - Found {outlier_count} revenue outliers ({outlier_count/len(df_sales)*100:.1f}%)")
            print(f"    Range: {lower_bound:.2f} - {upper_bound:.2f}")
            quality_report['outliers']['Sales'] = {
                'count': outlier_count,
                'percentage': outlier_count/len(df_sales)*100
            }
        else:
            print(f"  ✓ Sales - No significant outliers")
            quality_report['outliers']['Sales'] = {'count': 0, 'percentage': 0}
    
    # Validate data types
    print("\n[4/5] Validating data types...")
    df_sales['sale_date'] = pd.to_datetime(df_sales['sale_date'], errors='coerce')
    invalid_dates = df_sales['sale_date'].isna().sum()
    if invalid_dates > 0:
        print(f"  ⚠ Sales - {invalid_dates} invalid dates found")
        df_sales = df_sales[df_sales['sale_date'].notna()]
    else:
        print(f"  ✓ Sales - All dates are valid")
    
    # Business rules validation
    print("\n[5/5] Validating business rules...")
    initial_count = len(df_sales)
    
    # Rule 1: Revenue must be positive
    df_sales = df_sales[df_sales['revenue'] > 0]
    removed_negative = initial_count - len(df_sales)
    
    # Rule 2: Quantity must be positive
    df_sales = df_sales[df_sales['quantity'] > 0]
    removed_zero_qty = initial_count - (removed_negative + len(df_sales))
    
    # Rule 3: Profit should be <= Revenue (cost can't be negative)
    df_sales = df_sales[df_sales['profit'] <= df_sales['revenue']]
    removed_invalid_profit = initial_count - (removed_negative + removed_zero_qty + len(df_sales))
    
    # Rule 4: Check referential integrity (will be done later in transform)
    
    total_removed = removed_negative + removed_zero_qty + removed_invalid_profit
    if total_removed > 0:
        print(f"  ⚠ Removed {total_removed} records violating business rules:")
        if removed_negative > 0:
            print(f"    - {removed_negative} records with negative/zero revenue")
        if removed_zero_qty > 0:
            print(f"    - {removed_zero_qty} records with zero/negative quantity")
        if removed_invalid_profit > 0:
            print(f"    - {removed_invalid_profit} records with invalid profit")
        
        quality_report['business_rules'] = {
            'removed_negative_revenue': int(removed_negative),
            'removed_zero_quantity': int(removed_zero_qty),
            'removed_invalid_profit': int(removed_invalid_profit),
            'total_removed': int(total_removed)
        }
    else:
        print(f"  ✓ All records pass business rules")
        quality_report['business_rules'] = {'total_removed': 0}
    
    # Data quality summary
    print("\n" + "-"*50)
    print("DATA QUALITY SUMMARY")
    print("-"*50)
    print(f"Total records after cleaning: {len(df_sales):,}")
    print(f"Data quality score: {calculate_quality_score(quality_report):.1f}%")
    print("-"*50)
    
    print("\n✓ Data validation completed")
    return df_stores, df_products, df_customers, df_sales

def calculate_quality_score(quality_report):
    """Calculate overall data quality score (0-100)"""
    score = 100
    
    # Deduct points for missing values
    for table, missing in quality_report['missing_values'].items():
        if missing:
            score -= min(20, sum(missing.values()) * 0.1)
    
    # Deduct points for duplicates
    for table, dup_count in quality_report['duplicates'].items():
        if dup_count > 0:
            score -= min(15, dup_count * 0.1)
    
    # Deduct points for outliers (if excessive)
    if 'Sales' in quality_report['outliers']:
        outlier_pct = quality_report['outliers']['Sales'].get('percentage', 0)
        if outlier_pct > 5:  # More than 5% outliers
            score -= min(10, (outlier_pct - 5) * 0.5)
    
    # Deduct points for business rule violations
    total_removed = quality_report['business_rules'].get('total_removed', 0)
    if total_removed > 0:
        score -= min(15, total_removed * 0.01)
    
    return max(0, score)

def transform_data(df_stores, df_products, df_customers, df_sales):
    """Transform data for Data Warehouse"""
    print("\n" + "="*50)
    print("TRANSFORMING DATA")
    print("="*50)
    
    # ========== DIM_DATE ==========
    print("Creating date dimension...")
    df_sales['sale_date'] = pd.to_datetime(df_sales['sale_date'])
    unique_dates = df_sales['sale_date'].dt.date.unique()
    
    dim_date_data = []
    for i, date in enumerate(sorted(unique_dates), 1):
        date_obj = pd.to_datetime(date)
        dim_date_data.append({
            'date_id': i,
            'date': date,
            'day': date_obj.day,
            'month': date_obj.month,
            'quarter': date_obj.quarter,
            'year': date_obj.year,
            'month_name': date_obj.strftime('%B'),
            'quarter_name': f'Q{date_obj.quarter}',
            'day_of_week': date_obj.strftime('%A'),
            'is_weekend': date_obj.weekday() >= 5,
            'is_holiday': False
        })
    
    df_dim_date = pd.DataFrame(dim_date_data)
    print(f"  ✓ Created {len(df_dim_date)} date records")
    
    # Create date mapping
    date_mapping = {date: i+1 for i, date in enumerate(sorted(unique_dates))}
    df_sales['date_id'] = df_sales['sale_date'].dt.date.map(date_mapping)
    
    # ========== DIM_STORE ==========
    print("Creating store dimension...")
    df_dim_store = df_stores.copy()
    print(f"  ✓ Created {len(df_dim_store)} store records")
    
    # ========== DIM_PRODUCT ==========
    print("Creating product dimension...")
    df_dim_product = df_products.copy()
    print(f"  ✓ Created {len(df_dim_product)} product records")
    
    # ========== DIM_CUSTOMER ==========
    print("Creating customer dimension...")
    df_dim_customer = df_customers[['customer_id', 'customer_name', 'gender', 'age', 'age_group', 'city']].copy()
    print(f"  ✓ Created {len(df_dim_customer)} customer records")
    
    # ========== FACT_SALES ==========
    print("Creating sales fact table...")
    df_fact_sales = df_sales[[
        'sale_id', 'date_id', 'store_id', 'product_id', 
        'customer_id', 'quantity', 'revenue', 'cost', 'profit'
    ]].copy()
    
    # Ensure all foreign keys exist
    valid_stores = set(df_dim_store['store_id'])
    valid_products = set(df_dim_product['product_id'])
    valid_customers = set(df_dim_customer['customer_id'])
    valid_dates = set(df_dim_date['date_id'])
    
    initial_count = len(df_fact_sales)
    df_fact_sales = df_fact_sales[
        (df_fact_sales['store_id'].isin(valid_stores)) &
        (df_fact_sales['product_id'].isin(valid_products)) &
        (df_fact_sales['customer_id'].isin(valid_customers)) &
        (df_fact_sales['date_id'].isin(valid_dates))
    ]
    removed = initial_count - len(df_fact_sales)
    if removed > 0:
        print(f"  Removed {removed} sales with invalid foreign keys")
    
    print(f"  ✓ Created {len(df_fact_sales)} sales fact records")
    
    print("\n✓ Data transformation completed")
    return df_dim_date, df_dim_store, df_dim_product, df_dim_customer, df_fact_sales

def load_to_database(connection, df_dim_date, df_dim_store, df_dim_product, 
                     df_dim_customer, df_fact_sales):
    """Load transformed data into Data Warehouse"""
    print("\n" + "="*50)
    print("LOADING DATA TO DATA WAREHOUSE")
    print("="*50)
    
    try:
        # Create SQLAlchemy engine for faster bulk inserts
        connection_string = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
        )
        engine = create_engine(connection_string)
        
        # Clear existing data first (in correct order due to foreign keys)
        print("\nClearing existing data...")
        cursor = connection.cursor()
        
        # Disable foreign key checks temporarily
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Clear fact table first (has foreign keys)
        try:
            cursor.execute("TRUNCATE TABLE fact_sales")
            print("  ✓ Cleared fact_sales")
        except:
            pass
        
        # Clear dimension tables
        for table in ['dim_date', 'dim_store', 'dim_product', 'dim_customer']:
            try:
                cursor.execute(f"TRUNCATE TABLE {table}")
                print(f"  ✓ Cleared {table}")
            except:
                pass
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()
        cursor.close()
        
        # Load dimension tables
        print("\nLoading dimension tables...")
        df_dim_date.to_sql('dim_date', engine, if_exists='append', index=False)
        print(f"  ✓ Loaded dim_date: {len(df_dim_date)} rows")
        
        df_dim_store.to_sql('dim_store', engine, if_exists='append', index=False)
        print(f"  ✓ Loaded dim_store: {len(df_dim_store)} rows")
        
        df_dim_product.to_sql('dim_product', engine, if_exists='append', index=False)
        print(f"  ✓ Loaded dim_product: {len(df_dim_product)} rows")
        
        df_dim_customer.to_sql('dim_customer', engine, if_exists='append', index=False)
        print(f"  ✓ Loaded dim_customer: {len(df_dim_customer)} rows")
        
        # Load fact table in chunks for better performance
        print("\nLoading fact table...")
        chunk_size = 10000
        total_chunks = (len(df_fact_sales) // chunk_size) + 1
        
        for i in range(0, len(df_fact_sales), chunk_size):
            chunk = df_fact_sales.iloc[i:i+chunk_size]
            chunk.to_sql('fact_sales', engine, if_exists='append', index=False)
            print(f"  Loaded chunk {i//chunk_size + 1}/{total_chunks} ({len(chunk)} rows)")
        
        print(f"  ✓ Loaded fact_sales: {len(df_fact_sales)} rows")
        
        engine.dispose()
        print("\n✓ Data loading completed successfully!")
        
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        import traceback
        traceback.print_exc()

def run_etl():
    """Main ETL process"""
    print("="*50)
    print("RETAIL BI - ETL PIPELINE")
    print("="*50)
    
    # Create database if needed
    create_database_if_not_exists()
    
    # Connect to database
    connection = create_database_connection()
    if not connection:
        print("\n✗ Cannot proceed without database connection")
        return
    
    # Load schema
    load_sql_schema(connection)
    
    # Extract
    df_stores, df_products, df_customers, df_sales = extract_excel_data()
    if df_sales is None:
        connection.close()
        return
    
    # Validate
    df_stores, df_products, df_customers, df_sales = validate_data(
        df_stores, df_products, df_customers, df_sales
    )
    
    # Transform
    df_dim_date, df_dim_store, df_dim_product, df_dim_customer, df_fact_sales = transform_data(
        df_stores, df_products, df_customers, df_sales
    )
    
    # Load
    load_to_database(connection, df_dim_date, df_dim_store, df_dim_product, 
                    df_dim_customer, df_fact_sales)
    
    connection.close()
    print("\n" + "="*50)
    print("ETL PROCESS COMPLETED SUCCESSFULLY!")
    print("="*50)

if __name__ == '__main__':
    run_etl()

