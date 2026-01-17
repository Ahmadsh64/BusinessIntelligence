-- =====================================================
-- Retail BI Data Warehouse - Star Schema
-- =====================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;

-- =====================================================
-- DIMENSION TABLES
-- =====================================================

-- Date Dimension
CREATE TABLE dim_date (
    date_id INT PRIMARY KEY,
    date DATE NOT NULL,
    day INT NOT NULL,
    month INT NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL,
    month_name VARCHAR(20),
    quarter_name VARCHAR(10),
    day_of_week VARCHAR(10),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE
);

-- Store Dimension
CREATE TABLE dim_store (
    store_id INT PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    store_type VARCHAR(50) NOT NULL,
    opening_date DATE
);

-- Product Dimension
CREATE TABLE dim_product (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    brand VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL
);

-- Customer Dimension
CREATE TABLE dim_customer (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    age INT,
    age_group VARCHAR(10) NOT NULL,
    city VARCHAR(50)
);

-- =====================================================
-- FACT TABLE
-- =====================================================

-- Sales Fact Table
CREATE TABLE fact_sales (
    sale_id INT PRIMARY KEY,
    date_id INT NOT NULL,
    store_id INT NOT NULL,
    product_id INT NOT NULL,
    customer_id INT NOT NULL,
    quantity INT NOT NULL,
    revenue DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    profit DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
    FOREIGN KEY (store_id) REFERENCES dim_store(store_id),
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
    FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    INDEX idx_date (date_id),
    INDEX idx_store (store_id),
    INDEX idx_product (product_id),
    INDEX idx_customer (customer_id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX idx_fact_sales_date ON fact_sales(date_id);
CREATE INDEX idx_fact_sales_store ON fact_sales(store_id);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_id);

-- =====================================================
-- USERS TABLE FOR AUTHENTICATION
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'store_manager',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (store_id) REFERENCES dim_store(store_id) ON DELETE SET NULL,
    INDEX idx_username (username),
    INDEX idx_store_id (store_id)
);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Monthly Sales Summary View
CREATE OR REPLACE VIEW v_monthly_sales AS
SELECT 
    d.year,
    d.quarter,
    d.month,
    d.month_name,
    COUNT(f.sale_id) AS total_transactions,
    SUM(f.quantity) AS total_quantity,
    SUM(f.revenue) AS total_revenue,
    SUM(f.cost) AS total_cost,
    SUM(f.profit) AS total_profit,
    AVG(f.revenue) AS avg_revenue_per_transaction,
    SUM(f.profit) / SUM(f.revenue) * 100 AS profit_margin_pct
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.quarter, d.month, d.month_name
ORDER BY d.year, d.month;

-- Store Performance View
CREATE OR REPLACE VIEW v_store_performance AS
SELECT 
    s.store_id,
    s.store_name,
    s.city,
    s.region,
    s.store_type,
    COUNT(f.sale_id) AS total_transactions,
    SUM(f.revenue) AS total_revenue,
    SUM(f.profit) AS total_profit,
    SUM(f.profit) / SUM(f.revenue) * 100 AS profit_margin_pct,
    AVG(f.revenue) AS avg_order_value
FROM fact_sales f
JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.store_id, s.store_name, s.city, s.region, s.store_type
ORDER BY total_revenue DESC;

-- Product Performance View
CREATE OR REPLACE VIEW v_product_performance AS
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.brand,
    COUNT(f.sale_id) AS total_sales,
    SUM(f.quantity) AS total_quantity_sold,
    SUM(f.revenue) AS total_revenue,
    SUM(f.profit) AS total_profit,
    AVG(f.revenue) AS avg_revenue_per_sale
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.brand
ORDER BY total_revenue DESC;

