"""List all tables in the SQL Server database."""
import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};Server=localhost,1433;Database=master;UID=sa;PWD=YourStrongPassword123\\!;TrustServerCertificate=yes;"

try:
    conn = pyodbc.connect(conn_str, timeout=5)
    cursor = conn.cursor()
    
    # Query to list all user tables
    query = """
    SELECT 
        s.name AS SchemaName,
        t.name AS TableName,
        t.type_desc AS TableType
    FROM sys.tables t
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    ORDER BY s.name, t.name
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if rows:
        print(f"Found {len(rows)} table(s) in the 'master' database:\n")
        print(f"{'Schema':<20} {'Table Name':<40} {'Type':<20}")
        print("-" * 80)
        for row in rows:
            print(f"{row.SchemaName:<20} {row.TableName:<40} {row.TableType:<20}")
    else:
        print("No user tables found in the 'master' database.")
        print("\nNote: The 'master' database typically doesn't contain user tables.")
        print("Try checking other databases instead.")
        
        # List all databases
        cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb') ORDER BY name")
        user_dbs = cursor.fetchall()
        
        if user_dbs:
            print(f"\nFound {len(user_dbs)} user database(s):")
            for db in user_dbs:
                print(f"  - {db.name}")
        else:
            print("\nNo user databases found.")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
