import mysql.connector
import os

db_config = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv('DB_PASSWORD', 'A@ihb064'),
    "database": "mobile_shop"
}

try:
    print("Connecting to database...")
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    print("Altering users table to increase password column length...")
    cursor.execute("ALTER TABLE users MODIFY password VARCHAR(255)")
    conn.commit()
    print("Successfully altered password column to VARCHAR(255).")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
