"""Call MCP server tool directly via stdio."""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_list_tables():
    """Call the list_tables tool on the MCP server."""
    server_params = StdioServerParameters(
        command="/Users/chongcheekeong/code/MCP/mssqlclient-mcp-server/python-mcp-server/.venv/bin/python",
        args=["-m", "mssqlclient_mcp.server"],
        env={
            "MSSQL_CONNECTIONSTRING": "DRIVER={ODBC Driver 17 for SQL Server};Server=localhost,1433;Database=master;UID=sa;PWD=YourStrongPassword123\\!;TrustServerCertificate=yes;",
            "ENABLE_EXECUTE_QUERY": "true",
            "ENABLE_EXECUTE_STORED_PROCEDURE": "true",
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # Call list_tables
            print("Calling MCP server tool: list_tables")
            print("=" * 60)
            
            result = await session.call_tool("list_tables", arguments={})
            
            # Print result
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)

asyncio.run(call_list_tables())
