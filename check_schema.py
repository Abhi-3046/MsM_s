import mysql.connector
import os

db_config = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv('DB_PASSWORD', 'A@ihb064'),
    "database": "mobile_shop"
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DESCRIBE users")
    for row in cursor.fetchall():
        print(row)
    conn.close()
except Exception as e:
    print(e)
