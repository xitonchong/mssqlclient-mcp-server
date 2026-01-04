import os
import pyodbc

# Set connection string with DRIVER specified
conn_str = "DRIVER={ODBC Driver 17 for SQL Server};Server=localhost,1433;Database=master;UID=sa;PWD=YourStrongPassword123!;TrustServerCertificate=yes;"

try:
    # Try to connect
    print("Testing connection to SQL Server...")
    print(f"Connection string: {conn_str.replace('PWD=YourStrongPassword123!', 'PWD=***')}")
    
    conn = pyodbc.connect(conn_str, timeout=5)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    
    print("\n✓ Connection successful!")
    print(f"SQL Server version:\n{row[0]}")
    
    # Test a simple query
    cursor.execute("SELECT DB_NAME() as CurrentDatabase")
    row = cursor.fetchone()
    print(f"\nCurrent database: {row[0]}")
    
    cursor.close()
    conn.close()
    
except pyodbc.Error as e:
    print(f"\n✗ Connection failed!")
    print(f"Error: {e}")
    print("\nCommon issues:")
    print("1. SQL Server is not running")
    print("2. Wrong credentials (username/password)")
    print("3. SQL Server not configured to accept TCP/IP connections")
    print("4. Firewall blocking port 1433")
    print("5. SQL Server authentication mode not set to 'SQL Server and Windows Authentication'")
    
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
