import mysql.connector
from mysql.connector import Error
import os

def create_database():
    """
    Connect to MySQL server and create the database and tables
    defined in Database/database.sql
    """
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": os.getenv('DB_PASSWORD', 'A@ihb064') # Default or from Env
    }

    try:
        # Connect to MySQL Server (without database specified provided initially)
        print("Connecting to MySQL...")
        try:
            conn = mysql.connector.connect(**db_config)
        except Error as e:
            if e.errno == 1045: # Access denied
                print("Access denied. Please enter MySQL root password:")
                db_config['password'] = input("Password: ")
                conn = mysql.connector.connect(**db_config)
            else:
                raise e

        if conn.is_connected():
            print("Connected to MySQL Server")
            cursor = conn.cursor()

            # Read SQL file
            sql_file_path = os.path.join("Database", "database.sql")
            print(f"Reading SQL file from: {sql_file_path}")
            
            with open(sql_file_path, 'r') as f:
                sql_script = f.read()

            # Execute SQL commands
            # Split by semicolon to execute commands one by one, 
            # but handling the case where triggers/procedures might use semicolons is harder.
            # simpler approach for basic schema:
            
            commands = sql_script.split(';')
            
            for command in commands:
                if command.strip():
                    try:
                        cursor.execute(command)
                        # print(f"Executed: {command[:50]}...")
                    except Error as err:
                        if err.errno == 1050: # Table already exists
                            print(f"Table already exists, skipping: {err.msg}")
                        elif err.errno == 1007: # DB already exists
                            print(f"Database already exists, skipping: {err.msg}")
                        else:
                            print(f"Error executing command: {err}")
                            
            print("Database initialization completed successfully!")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    create_database()
