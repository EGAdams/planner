import mysql.connector
import sys

try:
    print("Attempting to connect to MySQL...")
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='',
        connection_timeout=5
    )
    print("Successfully connected to MySQL!")
    
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    databases = [db[0] for db in cursor.fetchall()]
    print(f"Databases found: {databases}")
    
    if 'nonprofit_finance' in databases:
        print("SUCCESS: 'nonprofit_finance' database exists.")
    else:
        print("FAILURE: 'nonprofit_finance' database NOT found.")
        
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
