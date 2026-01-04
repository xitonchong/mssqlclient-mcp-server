"""Test the MCP server configuration by importing and testing the database connection."""
import sys
import os

# Set environment variables
os.environ["MSSQL_CONNECTIONSTRING"] = "DRIVER={ODBC Driver 17 for SQL Server};Server=localhost,1433;Database=master;UID=sa;PWD=YourStrongPassword123\\!;TrustServerCertificate=yes;"
os.environ["ENABLE_EXECUTE_QUERY"] = "true"

# Import the config module
from mssqlclient_mcp.config import DatabaseConfiguration
from mssqlclient_mcp.database_service import DatabaseService

try:
    print("Loading configuration...")
    config = DatabaseConfiguration.from_env()
    print(f"✓ Configuration loaded")
    print(f"  - Server mode: {DatabaseConfiguration.is_server_mode(config.connection_string)}")
    print(f"  - Execute query enabled: {config.enable_execute_query}")
    
    print("\nTesting database connection...")
    db_service = DatabaseService(config)
    
    # This will test the connection
    import asyncio
    async def test_connection():
        databases = await db_service.list_databases()
        return databases
    
    databases = asyncio.run(test_connection())
    print(f"✓ Connection successful!")
    print(f"  - Found {len(databases)} databases")
    print(f"  - Databases: {', '.join([db.name for db in databases[:5]])}{'...' if len(databases) > 5 else ''}")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed! Your MCP server configuration is correct.")
