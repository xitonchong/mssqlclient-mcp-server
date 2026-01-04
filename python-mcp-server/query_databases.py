"""Query databases using MCP server."""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def query_databases():
    """Use execute_query to list databases."""
    server_params = StdioServerParameters(
        command="/Users/chongcheekeong/code/MCP/mssqlclient-mcp-server/python-mcp-server/.venv/bin/python",
        args=["-m", "mssqlclient_mcp.server"],
        env={
            "MSSQL_CONNECTIONSTRING": "DRIVER={ODBC Driver 17 for SQL Server};Server=localhost,1433;Database=master;UID=sa;PWD=YourStrongPassword123\\!;TrustServerCertificate=yes;",
            "ENABLE_EXECUTE_QUERY": "true",
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # Query to list all databases
            query = """
            SELECT 
                name AS DatabaseName,
                database_id AS ID,
                create_date AS Created
            FROM sys.databases 
            ORDER BY name
            """
            
            print("Calling MCP server tool: execute_query")
            print("Query: List all databases")
            print("=" * 60)
            
            result = await session.call_tool("execute_query", arguments={"query": query})
            
            # Print result
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)

asyncio.run(query_databases())
