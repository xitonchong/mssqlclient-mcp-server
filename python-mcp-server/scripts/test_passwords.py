import pyodbc

passwords = [
    "YourStrongPassword123!",
    "YourStrongPassword123\\!",
    "YourStrongPassword123",
]

for pwd in passwords:
    try:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};Server=localhost,1433;Database=master;UID=sa;PWD={pwd};TrustServerCertificate=yes;"
        print(f"\nTrying password: {pwd.replace(pwd, '***' + pwd[-3:])}")
        
        conn = pyodbc.connect(conn_str, timeout=3)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        
        print(f"✓ SUCCESS! Password works: {pwd}")
        
        # Get version
        row = cursor.fetchone()
        print(f"\nSQL Server version:\n{row[0][:100]}...")
        
        cursor.close()
        conn.close()
        break
        
    except pyodbc.Error as e:
        if "Login failed" in str(e):
            print(f"✗ Login failed - wrong password")
        else:
            print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
