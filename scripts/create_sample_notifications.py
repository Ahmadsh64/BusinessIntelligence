"""
Script to create sample notifications for testing
Run this script to create sample notifications
"""

import mysql.connector
from datetime import datetime, timedelta
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

def create_notifications_table():
    """Create notifications table if it doesn't exist"""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                store_id INT,
                type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                severity VARCHAR(20) DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (store_id) REFERENCES dim_store(store_id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_store_id (store_id),
                INDEX idx_is_read (is_read),
                INDEX idx_created_at (created_at)
            )
        """)
        connection.commit()
        print("✓ Notifications table created/verified")
    except Exception as e:
        print(f"✗ Error creating notifications table: {e}")
    finally:
        cursor.close()
        connection.close()

def create_sample_notifications():
    """Create sample notifications"""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    try:
        # Get stores
        cursor.execute("SELECT store_id FROM dim_store LIMIT 5")
        stores = cursor.fetchall()
        
        notifications = [
            {
                'type': 'low_stock',
                'title': 'מלאי נמוך - מוצר #123',
                'message': 'המוצר "מוצר A" הגיע לרמת מלאי נמוכה (5 יחידות). מומלץ להזמין מלאי נוסף.',
                'severity': 'warning',
                'store_id': stores[0][0] if stores else None
            },
            {
                'type': 'high_sales',
                'title': 'מכירות גבוהות - סניף תל אביב',
                'message': 'הסניף בתל אביב מדווח על מכירות גבוהות מהצפוי היום. ברכות!',
                'severity': 'info',
                'store_id': stores[0][0] if stores else None
            },
            {
                'type': 'forecast',
                'title': 'תחזית מכירות - חודש הבא',
                'message': 'לפי המודל, צפוי גידול של 15% במכירות בחודש הבא.',
                'severity': 'info',
                'store_id': None
            },
            {
                'type': 'anomaly',
                'title': 'זוהתה אנומליה במכירות',
                'message': 'זוהתה מכירה חריגה ב-20/01/2024. מומלץ לבדוק.',
                'severity': 'warning',
                'store_id': stores[1][0] if len(stores) > 1 else None
            },
            {
                'type': 'system',
                'title': 'עדכון מערכת',
                'message': 'המערכת עודכנה בהצלחה. תכונות חדשות זמינות כעת.',
                'severity': 'info',
                'store_id': None
            }
        ]
        
        for notif in notifications:
            cursor.execute("""
                INSERT INTO notifications (type, title, message, severity, store_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                notif['type'],
                notif['title'],
                notif['message'],
                notif['severity'],
                notif['store_id'],
                datetime.now() - timedelta(hours=len(notifications) - notifications.index(notif))
            ))
            print(f"  ✓ Created notification: {notif['title']}")
        
        connection.commit()
        print(f"\n✓ Created {len(notifications)} sample notifications")
    except Exception as e:
        print(f"✗ Error creating notifications: {e}")
    finally:
        cursor.close()
        connection.close()

def main():
    """Main function"""
    print("="*50)
    print("CREATING SAMPLE NOTIFICATIONS")
    print("="*50)
    
    create_notifications_table()
    create_sample_notifications()
    
    print("\n" + "="*50)
    print("NOTIFICATIONS CREATION COMPLETED!")
    print("="*50)

if __name__ == '__main__':
    main()

