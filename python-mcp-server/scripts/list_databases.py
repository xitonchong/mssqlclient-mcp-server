"""List all databases using MCP server."""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_list_databases():
    """Call the list_databases tool on the MCP server."""
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
            
            # Call list_databases
            print("Calling MCP server tool: list_databases")
            print("=" * 60)
            
            result = await session.call_tool("list_databases", arguments={})
            
            # Print result
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)

asyncio.run(call_list_databases())
