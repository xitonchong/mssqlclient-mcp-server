"""
Example usage of the MSSQL MCP Server components.

This script demonstrates how to use the database service directly,
without going through the MCP protocol layer.
"""

import asyncio
import os
from dotenv import load_dotenv
from mssqlclient_mcp.config import DatabaseConfiguration
from mssqlclient_mcp.database_service import DatabaseService
from mssqlclient_mcp.formatters import (
    format_table_list,
    format_database_list,
    format_table_schema,
    format_query_results,
)


async def main():
    """Example usage of database service."""
    # Load environment variables
    load_dotenv()

    # Create configuration
    try:
        config = DatabaseConfiguration.from_env()
        print(f"✓ Configuration loaded")
        print(f"  Server mode: {DatabaseConfiguration.is_server_mode(config.connection_string)}")
        print(f"  Query execution enabled: {config.enable_execute_query}")
        print()
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("  Please set MSSQL_CONNECTIONSTRING in .env file")
        return

    # Create database service
    db_service = DatabaseService(config)

    # Example 1: List databases (Server mode only)
    is_server_mode = DatabaseConfiguration.is_server_mode(config.connection_string)
    if is_server_mode:
        print("Example 1: Listing databases...")
        try:
            databases = await db_service.list_databases()
            print(format_database_list(databases))
            print()
        except Exception as e:
            print(f"✗ Error listing databases: {e}\n")

    # Example 2: List tables
    print("Example 2: Listing tables...")
    try:
        tables = await db_service.list_tables()
        print(format_table_list(tables))
        print()
    except Exception as e:
        print(f"✗ Error listing tables: {e}\n")

    # Example 3: Get table schema
    print("Example 3: Getting table schema...")
    try:
        tables = await db_service.list_tables()
        if tables:
            first_table = tables[0]
            table_name = f"{first_table.schema}.{first_table.name}"
            schema = await db_service.get_table_schema(table_name)
            print(format_table_schema(schema))
            print()
        else:
            print("No tables found to demonstrate schema retrieval\n")
    except Exception as e:
        print(f"✗ Error getting table schema: {e}\n")

    # Example 4: Execute query (if enabled)
    if config.enable_execute_query:
        print("Example 4: Executing query...")
        try:
            # Simple query that works on most SQL Servers
            query = "SELECT @@VERSION AS Version, DB_NAME() AS DatabaseName, GETDATE() AS CurrentTime"
            results = await db_service.execute_query(query)
            print(format_query_results(results))
            print()
        except Exception as e:
            print(f"✗ Error executing query: {e}\n")
    else:
        print("Example 4: Skipped (query execution not enabled)")
        print("  Set ENABLE_EXECUTE_QUERY=true in .env to enable\n")

    # Example 5: List stored procedures
    print("Example 5: Listing stored procedures...")
    try:
        procedures = await db_service.list_stored_procedures()
        if procedures:
            print(f"Found {len(procedures)} stored procedures:")
            for proc in procedures[:5]:  # Show first 5
                print(f"  - {proc.schema_name}.{proc.name}")
            if len(procedures) > 5:
                print(f"  ... and {len(procedures) - 5} more")
        else:
            print("No stored procedures found")
        print()
    except Exception as e:
        print(f"✗ Error listing stored procedures: {e}\n")

    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
