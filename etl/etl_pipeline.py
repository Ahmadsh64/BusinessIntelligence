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
    """Validate and clean data"""
    print("\n" + "="*50)
    print("VALIDATING AND CLEANING DATA")
    print("="*50)
    
    # Check for missing values
    print("\nChecking for missing values...")
    for name, df in [('Stores', df_stores), ('Products', df_products), 
                     ('Customers', df_customers), ('Sales', df_sales)]:
        missing = df.isnull().sum()
        if missing.any():
            print(f"  {name} - Missing values found:")
            print(f"    {missing[missing > 0]}")
        else:
            print(f"  ✓ {name} - No missing values")
    
    # Clean sales data
    print("\nCleaning sales data...")
    # Remove rows with negative values
    initial_count = len(df_sales)
    df_sales = df_sales[df_sales['revenue'] > 0]
    df_sales = df_sales[df_sales['quantity'] > 0]
    removed = initial_count - len(df_sales)
    if removed > 0:
        print(f"  Removed {removed} invalid sales records")
    
    # Ensure date is datetime
    df_sales['sale_date'] = pd.to_datetime(df_sales['sale_date'])
    
    print("✓ Data validation completed")
    return df_stores, df_products, df_customers, df_sales

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

