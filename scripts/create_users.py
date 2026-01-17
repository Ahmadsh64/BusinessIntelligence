"""
Script to create initial users for the Retail BI system
Run this script to create users for each store
"""

import mysql.connector
from werkzeug.security import generate_password_hash
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'BusinessIntelligence',
    'user': 'root',
    'password': '12345',  # Change this to your MySQL password
    'charset': 'utf8mb4'
}

def create_users_table():
    """Create users table if it doesn't exist"""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
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
            )
        """)
        connection.commit()
        print("✓ Users table created/verified")
    except Exception as e:
        print(f"✗ Error creating users table: {e}")
    finally:
        cursor.close()
        connection.close()

def get_stores():
    """Get all stores from database"""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT store_id, store_name, city FROM dim_store ORDER BY store_id")
        stores = cursor.fetchall()
        return stores
    except Exception as e:
        print(f"✗ Error fetching stores: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def create_user(username, password, store_id, role='store_manager'):
    """Create a new user"""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    try:
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, store_id, role)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            password_hash = VALUES(password_hash),
            store_id = VALUES(store_id),
            role = VALUES(role),
            is_active = TRUE
        """, (username, password_hash, store_id, role))
        connection.commit()
        print(f"  ✓ Created/Updated user: {username} (Store ID: {store_id}, Role: {role})")
        return True
    except Exception as e:
        print(f"  ✗ Error creating user {username}: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def main():
    """Main function to create users"""
    print("="*50)
    print("CREATING USERS FOR RETAIL BI SYSTEM")
    print("="*50)
    
    # Create users table
    create_users_table()
    
    # Get all stores
    stores = get_stores()
    
    if not stores:
        print("\n✗ No stores found. Please run ETL pipeline first.")
        return
    
    print(f"\nFound {len(stores)} stores")
    print("\nCreating users...")
    
    # Create admin user
    create_user('admin', 'admin123', None, 'admin')
    
    # Create users for each store
    for store in stores:
        store_id = store['store_id']
        store_name = store['store_name'].replace(' ', '_').lower()
        username = f"store_{store_id}"
        password = f"store{store_id}123"  # Default password
        
        create_user(username, password, store_id, 'store_manager')
    
    print("\n" + "="*50)
    print("USER CREATION COMPLETED!")
    print("="*50)
    print("\nDefault credentials:")
    print("  Admin: username='admin', password='admin123'")
    print("  Store Managers: username='store_X', password='storeX123' (where X is store_id)")
    print("\n⚠️  IMPORTANT: Change passwords after first login!")
    print("="*50)

if __name__ == '__main__':
    main()

