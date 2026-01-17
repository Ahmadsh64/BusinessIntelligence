"""
Data Generation Script for Retail BI Project
Creates synthetic retail data using Faker library
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Initialize Faker
fake = Faker('he_IL')  # Hebrew locale
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# Create output directory
output_dir = 'data/raw_excel'
os.makedirs(output_dir, exist_ok=True)

# ==================== STORES DATA ====================
print("Generating stores data...")
cities = ['תל אביב', 'ירושלים', 'חיפה', 'באר שבע', 'אשדוד', 'נתניה', 'רמת גן', 'חולון']
regions = ['מרכז', 'צפון', 'דרום', 'ירושלים']
store_types = ['סניף', 'מרכז קניות', 'אונליין']

stores_data = []
for i in range(1, 21):  # 20 stores
    stores_data.append({
        'store_id': i,
        'store_name': f'סניף {fake.company()}',
        'city': random.choice(cities),
        'region': random.choice(regions),
        'store_type': random.choice(store_types),
        'opening_date': fake.date_between(start_date='-5y', end_date='-1y')
    })

df_stores = pd.DataFrame(stores_data)
df_stores.to_excel(f'{output_dir}/stores.xlsx', index=False)
print(f"✓ Created stores.xlsx with {len(df_stores)} stores")

# ==================== PRODUCTS DATA ====================
print("Generating products data...")
categories = ['אלקטרוניקה', 'ביגוד', 'מזון', 'ספרים', 'צעצועים', 'בית וגן', 'ספורט', 'יופי']
brands = {
    'אלקטרוניקה': ['סמסונג', 'אפל', 'סוני', 'LG'],
    'ביגוד': ['נייקי', 'אדידס', 'זארה', 'H&M'],
    'מזון': ['תנובה', 'שטראוס', 'אוסם', 'אסם'],
    'ספרים': ['ידיעות ספרים', 'כתר', 'מטר', 'עם עובד'],
    'צעצועים': ['לגו', 'ברבי', 'פישר פרייס', 'האסברו'],
    'בית וגן': ['איקאה', 'Home Center', 'רמי לוי', 'ויליאמס'],
    'ספורט': ['נייקי', 'אדידס', 'פומה', 'ריבוק'],
    'יופי': ['לוריאל', 'אוליאה', 'ריבון', 'MAC']
}

products_data = []
for i in range(1, 201):  # 200 products
    category = random.choice(categories)
    brand = random.choice(brands[category])
    
    # Price based on category
    price_ranges = {
        'אלקטרוניקה': (200, 5000),
        'ביגוד': (50, 500),
        'מזון': (10, 150),
        'ספרים': (30, 200),
        'צעצועים': (50, 800),
        'בית וגן': (100, 2000),
        'ספורט': (100, 1500),
        'יופי': (30, 400)
    }
    
    min_price, max_price = price_ranges[category]
    price = round(random.uniform(min_price, max_price), 2)
    cost = round(price * random.uniform(0.4, 0.7), 2)  # Cost is 40-70% of price
    
    products_data.append({
        'product_id': i,
        'product_name': f'{brand} {fake.word()}',
        'category': category,
        'brand': brand,
        'price': price,
        'cost': cost
    })

df_products = pd.DataFrame(products_data)
df_products.to_excel(f'{output_dir}/products.xlsx', index=False)
print(f"✓ Created products.xlsx with {len(df_products)} products")

# ==================== CUSTOMERS DATA ====================
print("Generating customers data...")
customers_data = []
genders = ['זכר', 'נקבה']
age_groups = ['18-25', '26-35', '36-45', '46-55', '56+']

for i in range(1, 1001):  # 1000 customers
    gender = random.choice(genders)
    age = random.randint(18, 75)
    
    # Determine age group
    if age <= 25:
        age_group = '18-25'
    elif age <= 35:
        age_group = '26-35'
    elif age <= 45:
        age_group = '36-45'
    elif age <= 55:
        age_group = '46-55'
    else:
        age_group = '56+'
    
    customers_data.append({
        'customer_id': i,
        'customer_name': fake.name(),
        'gender': gender,
        'age': age,
        'age_group': age_group,
        'email': fake.email(),
        'city': random.choice(cities)
    })

df_customers = pd.DataFrame(customers_data)
df_customers.to_excel(f'{output_dir}/customers.xlsx', index=False)
print(f"✓ Created customers.xlsx with {len(df_customers)} customers")

# ==================== SALES DATA ====================
print("Generating sales data...")
start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)

sales_data = []
sale_id = 1

# Generate sales for 2 years
current_date = start_date
while current_date <= end_date:
    # More sales on weekends and certain months (seasonality)
    day_of_week = current_date.weekday()
    month = current_date.month
    
    # Base number of sales per day
    if day_of_week >= 5:  # Weekend
        num_sales = random.randint(80, 150)
    else:
        num_sales = random.randint(50, 100)
    
    # Seasonal adjustment (Q4 has more sales)
    if month in [10, 11, 12]:
        num_sales = int(num_sales * 1.3)
    
    for _ in range(num_sales):
        store_id = random.randint(1, 20)
        product_id = random.randint(1, 200)
        customer_id = random.randint(1, 1000)
        
        # Get product price
        product = df_products[df_products['product_id'] == product_id].iloc[0]
        price = product['price']
        cost = product['cost']
        
        # Quantity (1-5 items)
        quantity = random.randint(1, 5)
        
        revenue = round(price * quantity, 2)
        total_cost = round(cost * quantity, 2)
        profit = round(revenue - total_cost, 2)
        
        # Add some randomness to sale time during the day
        sale_time = current_date + timedelta(
            hours=random.randint(8, 20),
            minutes=random.randint(0, 59)
        )
        
        sales_data.append({
            'sale_id': sale_id,
            'sale_date': sale_time,
            'store_id': store_id,
            'product_id': product_id,
            'customer_id': customer_id,
            'quantity': quantity,
            'revenue': revenue,
            'cost': total_cost,
            'profit': profit
        })
        
        sale_id += 1
    
    current_date += timedelta(days=1)
    
    # Progress indicator
    if sale_id % 10000 == 0:
        print(f"  Generated {sale_id} sales...")

df_sales = pd.DataFrame(sales_data)
df_sales.to_excel(f'{output_dir}/sales_raw.xlsx', index=False)
print(f"✓ Created sales_raw.xlsx with {len(df_sales)} sales transactions")

print("\n" + "="*50)
print("Data generation completed successfully!")
print(f"All files saved to: {output_dir}/")
print("="*50)

