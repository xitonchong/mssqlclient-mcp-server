"""MCP Server implementation for Microsoft SQL Server."""

import asyncio
import sys
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import DatabaseConfiguration
from .database_service import DatabaseService, SessionManager, CapabilityDetector
from .formatters import (
    format_table_list,
    format_table_schema,
    format_database_list,
    format_stored_procedure_list,
    format_query_results,
)
from .models import EnhancedJSONEncoder
import json


def create_server(config: DatabaseConfiguration) -> Server:
    """Create and configure the MCP server."""
    server = Server("mssqlclient-mcp-server")
    db_service = DatabaseService(config)
    session_manager = SessionManager(
        database_service=db_service,
        max_workers=config.max_concurrent_sessions
    )
    capability_detector = CapabilityDetector(database_service=db_service)
    is_server_mode = DatabaseConfiguration.is_server_mode(config.connection_string)

    # Common tools available in both modes
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools based on configuration."""
        tools = []

        # Always available
        tools.append(
            Tool(
                name="server_capabilities",
                description="Get SQL Server capabilities and features",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            )
        )

        # Session management tools (available in both modes when enabled)
        if config.enable_start_query:
            tools.append(
                Tool(
                    name="start_query",
                    description="Start a SQL query in the background without blocking",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query to execute",
                            },
                            "databaseName": {
                                "type": "string",
                                "description": "Optional database name (server mode only)",
                            },
                            "timeoutSeconds": {
                                "type": "integer",
                                "description": "Query timeout in seconds (default 30)",
                                "default": 30,
                            },
                        },
                        "required": ["query"],
                    },
                )
            )

            tools.append(
                Tool(
                    name="get_session_status",
                    description="Get the status of a background query session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "The session ID returned from start_query",
                            },
                        },
                        "required": ["sessionId"],
                    },
                )
            )

            tools.append(
                Tool(
                    name="get_session_result",
                    description="Get the result of a completed background query session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "The session ID returned from start_query",
                            },
                        },
                        "required": ["sessionId"],
                    },
                )
            )

            tools.append(
                Tool(
                    name="cancel_session",
                    description="Cancel a running background query session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sessionId": {
                                "type": "string",
                                "description": "The session ID to cancel",
                            },
                        },
                        "required": ["sessionId"],
                    },
                )
            )

        # Stored procedure tools (available in both modes when enabled)
        tools.append(
            Tool(
                name="get_stored_procedure_parameters",
                description="Get parameter information for a stored procedure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "procedureName": {
                            "type": "string",
                            "description": "Name of the stored procedure (with optional schema)",
                        },
                        "databaseName": {
                            "type": "string",
                            "description": "Optional database name (server mode only)",
                        },
                    },
                    "required": ["procedureName"],
                },
            )
        )

        if config.enable_execute_stored_procedure:
            tools.append(
                Tool(
                    name="execute_stored_procedure",
                    description="Execute a stored procedure with typed parameters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedureName": {
                                "type": "string",
                                "description": "Name of the stored procedure",
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Dictionary of parameter names to values",
                            },
                            "databaseName": {
                                "type": "string",
                                "description": "Optional database name (server mode only)",
                            },
                            "timeoutSeconds": {
                                "type": "integer",
                                "description": "Optional timeout in seconds",
                            },
                        },
                        "required": ["procedureName"],
                    },
                )
            )

        if config.enable_start_stored_procedure:
            tools.append(
                Tool(
                    name="start_stored_procedure",
                    description="Start a stored procedure execution in the background",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedureName": {
                                "type": "string",
                                "description": "Name of the stored procedure",
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Dictionary of parameter names to values",
                            },
                            "databaseName": {
                                "type": "string",
                                "description": "Optional database name (server mode only)",
                            },
                            "timeoutSeconds": {
                                "type": "integer",
                                "description": "Optional timeout in seconds (default 30)",
                                "default": 30,
                            },
                        },
                        "required": ["procedureName"],
                    },
                )
            )

        # Server capability detection (always available)
        tools.append(
            Tool(
                name="get_server_capabilities",
                description="Detect SQL Server version, edition, and supported features",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "databaseName": {
                            "type": "string",
                            "description": "Optional database name (server mode only)",
                        },
                    },
                },
            )
        )

        # Advanced table metadata tools (available in both modes)
        tools.append(
            Tool(
                name="get_table_indexes",
                description="Get index information for a table including primary keys and constraints",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tableName": {
                            "type": "string",
                            "description": "Name of the table (with optional schema)",
                        },
                        "databaseName": {
                            "type": "string",
                            "description": "Optional database name (server mode only)",
                        },
                    },
                    "required": ["tableName"],
                },
            )
        )

        tools.append(
            Tool(
                name="get_table_foreign_keys",
                description="Get foreign key relationships for a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tableName": {
                            "type": "string",
                            "description": "Name of the table (with optional schema)",
                        },
                        "databaseName": {
                            "type": "string",
                            "description": "Optional database name (server mode only)",
                        },
                    },
                    "required": ["tableName"],
                },
            )
        )

        tools.append(
            Tool(
                name="get_table_statistics",
                description="Get table size and row count statistics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tableName": {
                            "type": "string",
                            "description": "Name of the table (with optional schema)",
                        },
                        "databaseName": {
                            "type": "string",
                            "description": "Optional database name (server mode only)",
                        },
                    },
                    "required": ["tableName"],
                },
            )
        )

        if is_server_mode:
            # Server mode tools
            tools.append(
                Tool(
                    name="list_databases",
                    description="List all databases on the SQL Server instance",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                )
            )

            tools.append(
                Tool(
                    name="list_tables_in_database",
                    description="List all tables in a specific database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "databaseName": {
                                "type": "string",
                                "description": "The name of the database",
                            }
                        },
                        "required": ["databaseName"],
                    },
                )
            )

            tools.append(
                Tool(
                    name="get_table_schema_in_database",
                    description="Get schema for a table in a specific database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "databaseName": {
                                "type": "string",
                                "description": "The name of the database",
                            },
                            "tableName": {
                                "type": "string",
                                "description": "The name of the table",
                            },
                        },
                        "required": ["databaseName", "tableName"],
                    },
                )
            )

            if config.enable_execute_query:
                tools.append(
                    Tool(
                        name="execute_query_in_database",
                        description="Execute a SQL query in a specific database",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "databaseName": {
                                    "type": "string",
                                    "description": "The name of the database",
                                },
                                "query": {
                                    "type": "string",
                                    "description": "The SQL query to execute",
                                },
                                "timeoutSeconds": {
                                    "type": "integer",
                                    "description": "Optional timeout in seconds",
                                },
                            },
                            "required": ["databaseName", "query"],
                        },
                    )
                )

            tools.append(
                Tool(
                    name="list_stored_procedures_in_database",
                    description="List all stored procedures in a specific database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "databaseName": {
                                "type": "string",
                                "description": "The name of the database",
                            }
                        },
                        "required": ["databaseName"],
                    },
                )
            )

            tools.append(
                Tool(
                    name="get_stored_procedure_definition_in_database",
                    description="Get stored procedure definition from a specific database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "databaseName": {
                                "type": "string",
                                "description": "The name of the database",
                            },
                            "procedureName": {
                                "type": "string",
                                "description": "The name of the stored procedure",
                            },
                        },
                        "required": ["databaseName", "procedureName"],
                    },
                )
            )

        else:
            # Database mode tools
            tools.append(
                Tool(
                    name="list_tables",
                    description="List all tables in the connected database",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                )
            )

            tools.append(
                Tool(
                    name="get_table_schema",
                    description="Get schema for a table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tableName": {
                                "type": "string",
                                "description": "The name of the table",
                            }
                        },
                        "required": ["tableName"],
                    },
                )
            )

            if config.enable_execute_query:
                tools.append(
                    Tool(
                        name="execute_query",
                        description="Execute a SQL query",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The SQL query to execute",
                                },
                                "timeoutSeconds": {
                                    "type": "integer",
                                    "description": "Optional timeout in seconds",
                                },
                            },
                            "required": ["query"],
                        },
                    )
                )

            tools.append(
                Tool(
                    name="list_stored_procedures",
                    description="List all stored procedures in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                )
            )

            tools.append(
                Tool(
                    name="get_stored_procedure_definition",
                    description="Get stored procedure definition",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedureName": {
                                "type": "string",
                                "description": "The name of the stored procedure",
                            }
                        },
                        "required": ["procedureName"],
                    },
                )
            )

        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "server_capabilities":
                capabilities = {
                    "toolMode": "server" if is_server_mode else "database",
                    "version": "Python 0.1.0",
                    "enableExecuteQuery": config.enable_execute_query,
                    "enableExecuteStoredProcedure": config.enable_execute_stored_procedure,
                    "enableStartQuery": config.enable_start_query,
                    "enableStartStoredProcedure": config.enable_start_stored_procedure,
                }
                return [TextContent(type="text", text=str(capabilities))]

            # Session management tools
            elif name == "start_query" and config.enable_start_query:
                session_id = session_manager.start_query(
                    query=arguments["query"],
                    database_name=arguments.get("databaseName") if is_server_mode else None,
                    timeout_seconds=arguments.get("timeoutSeconds", 30),
                )
                result = {"sessionId": session_id, "status": "started"}
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            elif name == "get_session_status" and config.enable_start_query:
                session = session_manager.get_session(arguments["sessionId"])
                if not session:
                    return [TextContent(type="text", text=json.dumps({"error": "Session not found"}))]

                result = {
                    "sessionId": session.session_id,
                    "status": session.status.value,
                    "startTime": session.start_time.isoformat(),
                    "endTime": session.end_time.isoformat() if session.end_time else None,
                    "rowCount": session.row_count,
                    "durationSeconds": session.duration_seconds(),
                    "error": session.error,
                }
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            elif name == "get_session_result" and config.enable_start_query:
                session = session_manager.get_session(arguments["sessionId"])
                if not session:
                    return [TextContent(type="text", text=json.dumps({"error": "Session not found"}))]

                if session.is_running():
                    result = {
                        "sessionId": session.session_id,
                        "status": "running",
                        "message": "Session is still running. Check status first.",
                    }
                elif session.status.value == "failed":
                    result = {
                        "sessionId": session.session_id,
                        "status": "failed",
                        "error": session.error,
                    }
                else:
                    result = {
                        "sessionId": session.session_id,
                        "status": session.status.value,
                        "rowCount": session.row_count,
                        "results": session.results or "",
                        "durationSeconds": session.duration_seconds(),
                    }
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            elif name == "cancel_session" and config.enable_start_query:
                cancelled = session_manager.cancel_session(arguments["sessionId"])
                result = {
                    "sessionId": arguments["sessionId"],
                    "cancelled": cancelled,
                    "message": "Session cancelled" if cancelled else "Session not found or already completed",
                }
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            # Stored procedure tools
            elif name == "get_stored_procedure_parameters":
                parameters = await db_service.get_sp_parameters(
                    procedure_name=arguments["procedureName"],
                    database_name=arguments.get("databaseName") if is_server_mode else None,
                )
                # Convert to JSON-serializable format
                params_list = [
                    {
                        "parameterName": p.parameter_name,
                        "parameterId": p.parameter_id,
                        "dataType": p.data_type,
                        "maxLength": p.max_length,
                        "precision": p.precision,
                        "scale": p.scale,
                        "isOutput": p.is_output,
                        "hasDefaultValue": p.has_default_value,
                        "defaultValue": p.default_value,
                        "isNullable": p.is_nullable,
                        "isRequired": p.is_required(),
                    }
                    for p in parameters
                ]
                return [TextContent(type="text", text=json.dumps({"parameters": params_list}, cls=EnhancedJSONEncoder))]

            elif name == "execute_stored_procedure" and config.enable_execute_stored_procedure:
                results = await db_service.execute_stored_procedure(
                    procedure_name=arguments["procedureName"],
                    parameters=arguments.get("parameters", {}),
                    database_name=arguments.get("databaseName") if is_server_mode else None,
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                result = {
                    "rowCount": len(results),
                    "results": results,
                }
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            elif name == "start_stored_procedure" and config.enable_start_stored_procedure:
                session_id = session_manager.start_stored_procedure(
                    procedure_name=arguments["procedureName"],
                    parameters=arguments.get("parameters", {}),
                    database_name=arguments.get("databaseName") if is_server_mode else None,
                    timeout_seconds=arguments.get("timeoutSeconds", 30),
                )
                result = {"sessionId": session_id, "status": "started"}
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            # Server capability detection
            elif name == "get_server_capabilities":
                capability = await capability_detector.get_capabilities(
                    database_name=arguments.get("databaseName") if is_server_mode else None
                )
                result = {
                    "version": capability.version,
                    "majorVersion": capability.major_version,
                    "edition": capability.edition,
                    "deploymentType": capability.get_deployment_type(),
                    "isAzureSqlDb": capability.is_azure_sql_db,
                    "isAzureVm": capability.is_azure_vm,
                    "isOnPremises": capability.is_on_premises,
                    "features": {
                        "json": capability.supports_json,
                        "columnstore": capability.supports_columnstore,
                        "temporalTables": capability.supports_temporal_tables,
                        "rowLevelSecurity": capability.supports_row_level_security,
                        "inMemoryOltp": capability.supports_in_memory_oltp,
                        "graphDatabase": capability.supports_graph_database,
                        "alwaysEncrypted": capability.supports_always_encrypted,
                        "queryStore": capability.supports_query_store,
                        "resumableIndexOps": capability.supports_resumable_index_ops,
                        "dataCompression": capability.supports_data_compression,
                    },
                }
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            # Advanced table metadata tools
            elif name == "get_table_indexes":
                indexes = await db_service.get_table_indexes(
                    table_name=arguments["tableName"],
                    database_name=arguments.get("databaseName") if is_server_mode else None,
                )
                indexes_list = [
                    {
                        "indexName": idx.index_name,
                        "indexType": idx.index_type,
                        "isPrimaryKey": idx.is_primary_key,
                        "isUnique": idx.is_unique,
                        "isUniqueConstraint": idx.is_unique_constraint,
                        "columns": idx.columns,
                        "includedColumns": idx.included_columns,
                    }
                    for idx in indexes
                ]
                result = {
                    "tableName": arguments["tableName"],
                    "indexCount": len(indexes),
                    "indexes": indexes_list,
                }
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            elif name == "get_table_foreign_keys":
                foreign_keys = await db_service.get_table_foreign_keys(
                    table_name=arguments["tableName"],
                    database_name=arguments.get("databaseName") if is_server_mode else None,
                )
                fks_list = [
                    {
                        "constraintName": fk.constraint_name,
                        "tableName": fk.table_name,
                        "columnName": fk.column_name,
                        "referencedTable": fk.referenced_table,
                        "referencedColumn": fk.referenced_column,
                        "deleteAction": fk.delete_action,
                        "updateAction": fk.update_action,
                    }
                    for fk in foreign_keys
                ]
                result = {
                    "tableName": arguments["tableName"],
                    "foreignKeyCount": len(foreign_keys),
                    "foreignKeys": fks_list,
                }
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            elif name == "get_table_statistics":
                stats = await db_service.get_table_statistics(
                    table_name=arguments["tableName"],
                    database_name=arguments.get("databaseName") if is_server_mode else None,
                )
                result = {
                    "tableName": stats.table_name,
                    "rowCount": stats.row_count,
                    "totalSpaceKB": stats.total_space_kb,
                    "usedSpaceKB": stats.used_space_kb,
                    "unusedSpaceKB": stats.unused_space_kb,
                    "totalSpaceMB": stats.total_space_mb,
                    "usedSpaceMB": stats.used_space_mb,
                }
                return [TextContent(type="text", text=json.dumps(result, cls=EnhancedJSONEncoder))]

            elif name == "list_databases" and is_server_mode:
                databases = await db_service.list_databases(
                    timeout_seconds=arguments.get("timeoutSeconds")
                )
                return [TextContent(type="text", text=format_database_list(databases))]

            elif name == "list_tables_in_database" and is_server_mode:
                tables = await db_service.list_tables(
                    database_name=arguments["databaseName"],
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                return [TextContent(type="text", text=format_table_list(tables))]

            elif name == "list_tables" and not is_server_mode:
                tables = await db_service.list_tables(
                    timeout_seconds=arguments.get("timeoutSeconds")
                )
                return [TextContent(type="text", text=format_table_list(tables))]

            elif name == "get_table_schema_in_database" and is_server_mode:
                schema = await db_service.get_table_schema(
                    table_name=arguments["tableName"],
                    database_name=arguments["databaseName"],
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                return [TextContent(type="text", text=format_table_schema(schema))]

            elif name == "get_table_schema" and not is_server_mode:
                schema = await db_service.get_table_schema(
                    table_name=arguments["tableName"],
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                return [TextContent(type="text", text=format_table_schema(schema))]

            elif name == "execute_query_in_database" and is_server_mode and config.enable_execute_query:
                results = await db_service.execute_query(
                    query=arguments["query"],
                    database_name=arguments["databaseName"],
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                return [TextContent(type="text", text=format_query_results(results))]

            elif name == "execute_query" and not is_server_mode and config.enable_execute_query:
                results = await db_service.execute_query(
                    query=arguments["query"],
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                return [TextContent(type="text", text=format_query_results(results))]

            elif name == "list_stored_procedures_in_database" and is_server_mode:
                procedures = await db_service.list_stored_procedures(
                    database_name=arguments["databaseName"],
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                return [
                    TextContent(
                        type="text", text=format_stored_procedure_list(procedures)
                    )
                ]

            elif name == "list_stored_procedures" and not is_server_mode:
                procedures = await db_service.list_stored_procedures(
                    timeout_seconds=arguments.get("timeoutSeconds")
                )
                return [
                    TextContent(
                        type="text", text=format_stored_procedure_list(procedures)
                    )
                ]

            elif name == "get_stored_procedure_definition_in_database" and is_server_mode:
                definition = await db_service.get_stored_procedure_definition(
                    procedure_name=arguments["procedureName"],
                    database_name=arguments["databaseName"],
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                return [TextContent(type="text", text=definition)]

            elif name == "get_stored_procedure_definition" and not is_server_mode:
                definition = await db_service.get_stored_procedure_definition(
                    procedure_name=arguments["procedureName"],
                    timeout_seconds=arguments.get("timeoutSeconds"),
                )
                return [TextContent(type="text", text=definition)]

            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Tool '{name}' not available or not enabled",
                    )
                ]

        except Exception as e:
            error_msg = f"Error executing {name}: {str(e)}"
            print(error_msg, file=sys.stderr)
            return [TextContent(type="text", text=error_msg)]

    return server


async def main():
    """Main entry point for the MCP server."""
    try:
        # Load configuration
        config = DatabaseConfiguration.from_env()

        print(
            f"Starting MCP MSSQLClient Server (Python)...", file=sys.stderr
        )
        print(
            f"Server mode: {DatabaseConfiguration.is_server_mode(config.connection_string)}",
            file=sys.stderr,
        )
        print(
            f"EnableExecuteQuery: {config.enable_execute_query}", file=sys.stderr
        )
        print(
            f"EnableExecuteStoredProcedure: {config.enable_execute_stored_procedure}",
            file=sys.stderr,
        )

        # Create and run server
        server = create_server(config)

        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
