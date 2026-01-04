# Quick Start: Python MCP Server Advanced Features

**Feature**: 001-python-mcp-server
**Date**: 2026-01-03
**Phase**: 1 - Design

## Overview

This guide provides a quick start for using the advanced features of the Python MCP Server once implemented. It covers session management, stored procedure execution, capability detection, and advanced metadata queries.

## Prerequisites

- Python MCP Server installed and configured
- SQL Server 2016 or higher
- Valid SQL Server connection configured in `.env`
- ODBC Driver for SQL Server installed

## Feature Enablement

Add these environment variables to enable advanced execution features:

```bash
# Enable background query sessions
ENABLE_START_QUERY=true

# Enable background stored procedure sessions
ENABLE_START_STORED_PROCEDURE=true

# Enable synchronous stored procedure execution
ENABLE_EXECUTE_STORED_PROCEDURE=true

# Optional: Configure session limits
MAX_CONCURRENT_SESSIONS=10
SESSION_CLEANUP_INTERVAL_MINUTES=15
```

## 1. Background Query Execution

Start a long-running query without blocking:

```python
# Start a query in the background
result = await mcp_client.call_tool("start_query", {
    "query": "SELECT * FROM LargeTable WHERE Year = 2024",
    "timeout_seconds": 120
})
session_id = result["session_id"]
print(f"Started session: {session_id}")

# Check status
status = await mcp_client.call_tool("get_session_status", {
    "session_id": session_id
})
print(f"Status: {status['status']}, Rows: {status['row_count']}")

# Get results when completed
if status["status"] == "completed":
    result = await mcp_client.call_tool("get_session_result", {
        "session_id": session_id
    })
    print(result["results"])
```

**Use Cases**:
- Running reports that take > 30 seconds
- Executing data migrations
- Complex analytical queries
- Background data exports

## 2. Stored Procedure Execution

### Discover Parameters

Before executing a stored procedure, discover its parameters:

```python
# Get parameter information
params_info = await mcp_client.call_tool("get_stored_procedure_parameters", {
    "procedure_name": "dbo.GetCustomerOrders",
    "database_name": "Northwind"  # Optional in database mode
})

for param in params_info["parameters"]:
    print(f"{param['parameter_name']}: {param['data_type']}")
    if param["is_required"]:
        print("  (Required)")
    if param["has_default_value"]:
        print(f"  Default: {param['default_value']}")
```

### Execute with Parameters

```python
# Execute stored procedure with type-safe parameters
result = await mcp_client.call_tool("execute_stored_procedure", {
    "procedure_name": "dbo.GetCustomerOrders",
    "parameters": {
        "@CustomerId": "ALFKI",
        "@StartDate": "2024-01-01",
        "@EndDate": "2024-12-31"
    },
    "database_name": "Northwind"
})

print(f"Rows returned: {result['row_count']}")
print(result["results"])
```

**Supported Parameter Types**:
- `int`, `bigint`, `smallint`, `tinyint`
- `decimal`, `numeric`, `money`
- `varchar`, `nvarchar`, `char`, `nchar`
- `datetime`, `datetime2`, `date`, `time`
- `bit` (boolean)
- `uniqueidentifier` (UUID)
- `binary`, `varbinary`

**Note**: OUTPUT parameters not yet supported in MVP. Use procedures that return result sets.

## 3. Server Capability Detection

Check what features your SQL Server supports:

```python
# Get server capabilities
capabilities = await mcp_client.call_tool("get_server_capabilities", {})

print(f"Version: {capabilities['version']}")
print(f"Edition: {capabilities['edition']}")
print(f"Deployment: {capabilities['deployment_type']}")

print("\nSupported Features:")
for feature, supported in capabilities["features"].items():
    status = "✓" if supported else "✗"
    print(f"  {status} {feature}")
```

**Example Output**:
```
Version: SQL Server 15.0.2000.5 (Enterprise Edition)
Edition: Enterprise Edition
Deployment: On-Premises

Supported Features:
  ✓ json
  ✓ columnstore
  ✓ temporal_tables
  ✓ row_level_security
  ✓ in_memory_oltp
  ✓ graph_database
  ✓ always_encrypted
  ✓ query_store
```

**Use Cases**:
- Conditional feature usage
- Compatibility checking before deployment
- Generating capability reports
- Recommending SQL Server upgrades

## 4. Advanced Table Metadata

### Get Index Information

```python
# Get all indexes for a table
indexes = await mcp_client.call_tool("get_table_indexes", {
    "table_name": "dbo.Customers",
    "database_name": "Northwind"
})

print(f"Table: {indexes['table_name']}")
print(f"Total Indexes: {indexes['index_count']}\n")

for idx in indexes["indexes"]:
    pk_marker = " (PK)" if idx["is_primary_key"] else ""
    unique_marker = " (Unique)" if idx["is_unique"] else ""
    print(f"{idx['index_name']}: {idx['index_type']}{pk_marker}{unique_marker}")
    print(f"  Columns: {', '.join(idx['columns'])}")
    if idx["included_columns"]:
        print(f"  Included: {', '.join(idx['included_columns'])}")
```

### Get Foreign Key Relationships

```python
# Get foreign keys
fks = await mcp_client.call_tool("get_table_foreign_keys", {
    "table_name": "dbo.Orders"
})

print(f"Foreign Keys for {fks['table_name']}:\n")
for fk in fks["foreign_keys"]:
    print(f"{fk['constraint_name']}:")
    print(f"  {fk['column_name']} -> {fk['referenced_table']}.{fk['referenced_column']}")
    print(f"  ON DELETE {fk['delete_action']}")
```

### Get Table Statistics

```python
# Get table size and row count
stats = await mcp_client.call_tool("get_table_statistics", {
    "table_name": "dbo.OrderDetails"
})

print(f"Table: {stats['table_name']}")
print(f"Rows: {stats['row_count']:,}")
print(f"Total Space: {stats['total_space_mb']:.2f} MB")
print(f"Used Space: {stats['used_space_mb']:.2f} MB")
print(f"Unused Space: {stats['unused_space_kb']:,} KB")
```

## 5. Complete Example: Data Analysis Workflow

```python
async def analyze_database():
    # 1. Check server capabilities
    caps = await mcp_client.call_tool("get_server_capabilities", {})
    print(f"Analyzing {caps['edition']} database\n")

    # 2. Start a background analytical query
    session = await mcp_client.call_tool("start_query", {
        "query": """
            SELECT
                Year(OrderDate) AS Year,
                COUNT(*) AS OrderCount,
                SUM(TotalAmount) AS Revenue
            FROM Orders
            GROUP BY Year(OrderDate)
            ORDER BY Year
        """,
        "timeout_seconds": 60
    })
    session_id = session["session_id"]

    # 3. While query runs, examine table metadata
    indexes = await mcp_client.call_tool("get_table_indexes", {
        "table_name": "Orders"
    })
    print(f"Orders table has {indexes['index_count']} indexes")

    stats = await mcp_client.call_tool("get_table_statistics", {
        "table_name": "Orders"
    })
    print(f"Orders table: {stats['row_count']:,} rows, {stats['total_space_mb']:.2f} MB\n")

    # 4. Check if query is done
    status = await mcp_client.call_tool("get_session_status", {
        "session_id": session_id
    })

    # 5. Get results
    if status["status"] == "completed":
        result = await mcp_client.call_tool("get_session_result", {
            "session_id": session_id
        })
        print("Annual Revenue Report:")
        print(result["results"])
    else:
        print(f"Query still running... ({status['duration_seconds']:.1f}s)")

# Run the analysis
asyncio.run(analyze_database())
```

## Error Handling

### Session Errors

```python
try:
    result = await mcp_client.call_tool("start_query", {
        "query": "SELECT * FROM NonExistentTable"
    })
    session_id = result["session_id"]

    # Poll for completion
    while True:
        status = await mcp_client.call_tool("get_session_status", {
            "session_id": session_id
        })
        if status["status"] != "running":
            break
        await asyncio.sleep(1)

    if status["status"] == "failed":
        print(f"Query failed: {status['error']}")
except Exception as e:
    print(f"Error: {e}")
```

### Parameter Type Errors

```python
try:
    result = await mcp_client.call_tool("execute_stored_procedure", {
        "procedure_name": "dbo.UpdateCustomer",
        "parameters": {
            "@CustomerId": "ALFKI",
            "@CreditLimit": "not a number"  # Type error!
        }
    })
except ValueError as e:
    print(f"Parameter type error: {e}")
```

## Performance Tips

1. **Session Management**:
   - Limit concurrent sessions to 10 or fewer
   - Always retrieve results to free memory
   - Cancel sessions that are no longer needed

2. **Capability Caching**:
   - Capabilities are cached for 1 hour
   - No need to repeatedly call `get_server_capabilities`

3. **Stored Procedures**:
   - Discover parameters once, cache the result
   - Use procedures for complex operations (faster than queries)

4. **Metadata Queries**:
   - Metadata queries are fast (<1s typically)
   - Safe to call repeatedly for up-to-date information

## Troubleshooting

### "Maximum concurrent sessions reached"

**Solution**: Wait for sessions to complete or increase `MAX_CONCURRENT_SESSIONS`.

```python
# Cancel old sessions
await mcp_client.call_tool("cancel_session", {"session_id": old_session_id})
```

### "Tool not enabled"

**Solution**: Enable the tool in your `.env` file:

```bash
ENABLE_START_QUERY=true
```

### "Cannot convert type"

**Solution**: Ensure parameter types match SQL Server expectations:

```python
# ✗ Wrong
"@Age": "25"  # String instead of int

# ✓ Correct
"@Age": 25  # Integer
```

## Next Steps

- See [data-model.md](./data-model.md) for detailed entity definitions
- See [contracts/](./contracts/) for complete MCP tool specifications
- See [plan.md](./plan.md) for implementation details

## Support

For issues or questions:
- Check implementation status in [plan.md](./plan.md)
- Review error messages in session status
- Consult SQL Server logs for database-side errors
