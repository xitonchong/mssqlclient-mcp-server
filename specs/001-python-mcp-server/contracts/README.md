# MCP Tool Contracts

This directory contains the contracts (interface definitions) for all new MCP tools added by the Python MCP Server Advanced Features.

## Tool Categories

### Session Management Tools
- `start_query.json` - Start a query in background session
- `get_session_status.json` - Get status of a running session
- `get_session_result.json` - Retrieve results from completed session
- `cancel_session.json` - Cancel a running session

### Stored Procedure Tools
- `get_stored_procedure_parameters.json` - Discover SP parameters
- `execute_stored_procedure.json` - Execute SP with parameters (enhanced)

### Capability Tools
- `get_server_capabilities.json` - Get SQL Server capabilities and features

### Metadata Tools
- `get_table_indexes.json` - Get index information for a table
- `get_table_foreign_keys.json` - Get foreign key relationships
- `get_table_statistics.json` - Get table size and row count

## Contract Format

Each contract file follows the MCP Tool schema:

```json
{
  "name": "tool_name",
  "description": "What the tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param_name": {
        "type": "string",
        "description": "Parameter description"
      }
    },
    "required": ["param_name"]
  }
}
```

## Security Flags

Tools that modify data require explicit enablement via environment variables:

- `start_query` requires `ENABLE_START_QUERY=true`
- `start_stored_procedure` requires `ENABLE_START_STORED_PROCEDURE=true`
- `execute_stored_procedure` requires `ENABLE_EXECUTE_STORED_PROCEDURE=true`

Read-only tools are always enabled.
