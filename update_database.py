"""
Database Update Script - Add contact_messages table
Run this script to add the contact_messages table to your existing database
"""
# -*- coding: utf-8 -*-
import mysql.connector
from mysql.connector import Error
import os
import sys

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def update_database():
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv('DB_PASSWORD', 'A@ihb064'),
            database="mobile_shop"
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("Connected to mobile_shop database")
            
            # Create contact_messages table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS contact_messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                subject VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                status ENUM('new', 'read', 'replied', 'archived') DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
            """
            
            cursor.execute(create_table_query)
            print("✓ contact_messages table created successfully!")
            
            # Show all tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("\nCurrent tables in mobile_shop database:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Show contact_messages table structure
            cursor.execute("DESCRIBE contact_messages")
            columns = cursor.fetchall()
            print("\ncontact_messages table structure:")
            for column in columns:
                print(f"  {column[0]}: {column[1]}")
            
            connection.commit()
            print("\n✓ Database update completed successfully!")
            
    except Error as e:
        print(f"✗ Error: {e}")
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    print("=" * 60)
    print("Mobile Shop Database Update - Adding contact_messages table")
    print("=" * 60)
    update_database()
