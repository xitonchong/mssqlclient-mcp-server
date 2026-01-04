"""List tables in TestDB using MCP server."""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def list_tables_testdb():
    """List tables in TestDB database."""
    # Connect to TestDB instead of master
    server_params = StdioServerParameters(
        command="/Users/chongcheekeong/code/MCP/mssqlclient-mcp-server/python-mcp-server/.venv/bin/python",
        args=["-m", "mssqlclient_mcp.server"],
        env={
            "MSSQL_CONNECTIONSTRING": "DRIVER={ODBC Driver 17 for SQL Server};Server=localhost,1433;Database=TestDB;UID=sa;PWD=YourStrongPassword123\\!;TrustServerCertificate=yes;",
            "ENABLE_EXECUTE_QUERY": "true",
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("=" * 70)
            print("LISTING TABLES IN TESTDB DATABASE (via MCP Server)")
            print("=" * 70 + "\n")
            
            # Method 1: Using list_tables tool
            print("Method 1: Using list_tables MCP tool")
            print("-" * 70)
            result = await session.call_tool("list_tables", arguments={})
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            # print("\n" + "-" * 70)
            # print("\nMethod 2: Using execute_query to get table schema")
            # print("-" * 70)
            
            # Method 2: Query for detailed table info
            # query = """
            # SELECT 
            #     t.name AS TableName,
            #     s.name AS SchemaName,
            #     p.rows AS RowCount
            # FROM sys.tables t
            # INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            # INNER JOIN sys.partitions p ON t.object_id = p.object_id
            # WHERE p.index_id IN (0,1)
            # ORDER BY t.name;
            # """
            
            # result = await session.call_tool("execute_query", arguments={"query": query})
            # for content in result.content:
            #     if hasattr(content, 'text'):
            #         print(content.text)

asyncio.run(list_tables_testdb())
