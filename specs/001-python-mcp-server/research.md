# Research: Python MCP Server Advanced Features

**Feature**: 001-python-mcp-server
**Date**: 2026-01-03
**Research Phase**: Phase 0

## Overview

This document consolidates research findings for implementing advanced features in the Python MCP Server. Research was conducted by examining the existing .NET implementation and Python best practices for async operations, SQL Server interaction, and type conversion.

## 1. Session Management (Background Query Execution)

### Decision: Use asyncio with run_in_executor for Thread-Based Execution

**Rationale**:
- pyodbc is **not thread-safe** and does not support native async
- asyncio's `run_in_executor()` allows running blocking pyodbc calls in a thread pool without blocking the event loop
- This matches the .NET implementation's `Task.Run()` pattern

**Python Implementation Pattern**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid

class SessionStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class QuerySession:
    session_id: str
    query: str
    database_name: str | None
    status: SessionStatus
    start_time: datetime
    end_time: datetime | None = None
    row_count: int = 0
    results: str | None = None
    error: str | None = None

class SessionManager:
    def __init__(self, max_workers=10):
        self._sessions: dict[str, QuerySession] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._loop = asyncio.get_event_loop()

    async def start_query(self, query: str, database_name: str | None = None):
        session_id = str(uuid.uuid4())
        session = QuerySession(
            session_id=session_id,
            query=query,
            database_name=database_name,
            status=SessionStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        self._sessions[session_id] = session

        # Execute in thread pool to avoid blocking
        self._loop.run_in_executor(
            self._executor,
            self._execute_query,
            session
        )

        return session_id

    def _execute_query(self, session: QuerySession):
        # This runs in a separate thread
        try:
            # pyodbc operations here
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute(session.query)
            # Process results...
            session.status = SessionStatus.COMPLETED
        except Exception as e:
            session.status = SessionStatus.FAILED
            session.error = str(e)
        finally:
            session.end_time = datetime.utcnow()
```

**Key Features**:
- **Session Storage**: Dictionary keyed by UUID session IDs
- **Cleanup**: Background task to remove completed sessions after timeout (e.g., 15 minutes)
- **Concurrency Limit**: Configurable max concurrent sessions (default: 10)
- **Cancellation**: Not directly supported by pyodbc; would need to track and close connections

**Alternatives Considered**:
- `asyncpg` or `aioodbc` for native async - **Rejected**: Limited SQL Server support
- Thread per query - **Rejected**: Poor resource utilization, ThreadPoolExecutor is more efficient
- Process pool - **Rejected**: Overhead too high for typical MCP usage

## 2. Stored Procedure Execution with Parameters

### Decision: Use sys.parameters for Metadata Discovery + Manual Type Conversion

**Rationale**:
- SQL Server stores complete parameter metadata in `sys.parameters`
- .NET implementation uses this approach successfully
- pyodbc supports parameter binding with proper type conversion

**Parameter Discovery SQL**:
```sql
SELECT
    p.name AS ParameterName,
    p.parameter_id AS ParameterId,
    t.name AS DataType,
    p.max_length AS MaxLength,
    p.precision AS Precision,
    p.scale AS Scale,
    p.is_output AS IsOutput,
    p.has_default_value AS HasDefaultValue,
    p.default_value AS DefaultValue,
    p.is_nullable AS IsNullable
FROM sys.parameters p
JOIN sys.types t ON p.user_type_id = t.user_type_id
JOIN sys.procedures sp ON p.object_id = sp.object_id
JOIN sys.schemas s ON sp.schema_id = s.schema_id
WHERE s.name = ? AND sp.name = ?
ORDER BY p.parameter_id
```

**Execution Pattern**:
```python
def execute_stored_procedure(proc_name: str, params: dict):
    # 1. Discover parameters
    param_metadata = get_stored_procedure_parameters(proc_name)

    # 2. Build parameter list with types
    sql_params = []
    for meta in param_metadata:
        if meta.parameter_name in params:
            value = params[meta.parameter_name]
            # Convert Python type to SQL type
            sql_param = convert_parameter(value, meta)
            sql_params.append(sql_param)

    # 3. Execute
    cursor.execute(f"EXEC {proc_name} {placeholders}", sql_params)
```

**OUTPUT Parameter Handling**:
- pyodbc does not support OUTPUT parameters directly
- Workaround: Use `SELECT @output_param AS output_param` after execution
- Or: Redesign to use RETURN values or result sets

**Multiple Result Sets**:
```python
cursor.execute("EXEC multi_result_sp")
results = []
while True:
    results.append(cursor.fetchall())
    if not cursor.nextset():
        break
```

**Alternatives Considered**:
- SQLAlchemy for SP execution - **Rejected**: Adds heavy dependency
- Raw parameter passing without metadata - **Rejected**: Type safety issues
- Only support INPUT parameters - **Selected as MVP**: OUTPUT params as future enhancement

## 3. SQL Server Capability Detection

### Decision: Query SERVERPROPERTY and @@VERSION, Cache Per Connection

**Rationale**:
- .NET implementation proves this approach works reliably
- Capability queries are fast (<50ms typically)
- Caching prevents repeated queries

**Detection Queries** (from .NET implementation):
```sql
-- Version and Edition
SELECT
    @@VERSION AS ServerVersion,
    SERVERPROPERTY('ProductVersion') AS ProductVersion,
    SERVERPROPERTY('Edition') AS Edition,
    SERVERPROPERTY('EngineEdition') AS EngineEdition

-- Azure Detection
SELECT CASE
    WHEN SERVERPROPERTY('EngineEdition') = 5 THEN 1
    ELSE 0
END AS IsAzureSqlDb
```

**Feature Detection Logic** (version-based):
```python
@dataclass
class ServerCapability:
    version: str
    major_version: int
    edition: str
    is_azure_sql_db: bool
    is_azure_vm: bool
    is_on_premises: bool

    # Features (based on major version)
    supports_json: bool  # SQL 2016+ (v13+)
    supports_columnstore: bool  # SQL 2012+ (v11+)
    supports_temporal_tables: bool  # SQL 2016+ (v13+)
    supports_row_level_security: bool  # SQL 2016+ (v13+)
    supports_in_memory_oltp: bool  # SQL 2014+ (v12+)
    supports_graph_database: bool  # SQL 2017+ (v14+)
    supports_always_encrypted: bool  # SQL 2016+ (v13+)
    supports_query_store: bool  # SQL 2016+ (v13+)

def detect_capabilities(connection_string: str) -> ServerCapability:
    # Parse version: "15.0.2000.5" -> major=15
    major_version = parse_major_version(product_version)

    return ServerCapability(
        version=server_version,
        major_version=major_version,
        edition=edition,
        is_azure_sql_db=(engine_edition == 5),
        supports_json=(major_version >= 13),
        supports_columnstore=(major_version >= 11),
        # ...
    )
```

**Caching Strategy**:
```python
_capability_cache: dict[str, tuple[ServerCapability, datetime]] = {}
CACHE_TTL_MINUTES = 60

def get_capabilities(connection_string: str) -> ServerCapability:
    cache_key = connection_string
    if cache_key in _capability_cache:
        cap, timestamp = _capability_cache[cache_key]
        if (datetime.utcnow() - timestamp).total_seconds() < CACHE_TTL_MINUTES * 60:
            return cap

    # Detect and cache
    cap = detect_capabilities(connection_string)
    _capability_cache[cache_key] = (cap, datetime.utcnow())
    return cap
```

**Alternatives Considered**:
- Query system views for each feature - **Rejected**: Too slow, brittle
- No caching - **Rejected**: Wasteful repeated queries
- Global cache vs per-connection - **Selected per-connection**: Different servers may be used

## 4. Python-to-SQL Type Conversion

### Decision: Explicit Type Mapping Table with Validation

**Rationale**:
- pyodbc does some automatic conversion but not always correctly
- Explicit mapping ensures correctness and provides better error messages
- .NET implementation uses similar approach via SqlTypeMapper

**Type Mapping Table**:

| Python Type | SQL Server Types | Notes |
|-------------|------------------|-------|
| `int` | `int`, `bigint`, `smallint`, `tinyint` | Range validation |
| `float` | `float`, `real` | Precision loss warning |
| `Decimal` | `decimal`, `numeric`, `money` | Use for precision |
| `str` | `varchar`, `nvarchar`, `char`, `nchar`, `text` | Length validation |
| `bool` | `bit` | Convert to 0/1 |
| `datetime` | `datetime`, `datetime2`, `smalldatetime`, `date` | Timezone handling |
| `bytes` | `binary`, `varbinary`, `image` | Direct mapping |
| `None` | Any (if nullable) | Maps to NULL |
| `uuid.UUID` | `uniqueidentifier` | String representation |

**Conversion Function**:
```python
from decimal import Decimal
from datetime import datetime
import uuid

def convert_python_to_sql(value: any, sql_type: str, max_length: int = -1) -> any:
    if value is None:
        return None

    # String types
    if sql_type in ('varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext'):
        s = str(value)
        if max_length > 0 and len(s) > max_length:
            raise ValueError(f"String length {len(s)} exceeds max {max_length}")
        return s

    # Integer types
    elif sql_type in ('int', 'bigint', 'smallint', 'tinyint'):
        if not isinstance(value, int):
            try:
                return int(value)
            except:
                raise TypeError(f"Cannot convert {type(value)} to int")
        return value

    # Decimal types
    elif sql_type in ('decimal', 'numeric', 'money', 'smallmoney'):
        if isinstance(value, (int, float, str)):
            return Decimal(str(value))
        elif isinstance(value, Decimal):
            return value
        raise TypeError(f"Cannot convert {type(value)} to Decimal")

    # Datetime types
    elif sql_type in ('datetime', 'datetime2', 'smalldatetime', 'date', 'time'):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        elif isinstance(value, datetime):
            return value
        raise TypeError(f"Cannot convert {type(value)} to datetime")

    # Boolean/bit
    elif sql_type == 'bit':
        return 1 if value else 0

    # UUID/uniqueidentifier
    elif sql_type == 'uniqueidentifier':
        if isinstance(value, str):
            return str(uuid.UUID(value))  # Validate UUID format
        elif isinstance(value, uuid.UUID):
            return str(value)
        raise TypeError(f"Cannot convert {type(value)} to uniqueidentifier")

    # Binary types
    elif sql_type in ('binary', 'varbinary', 'image'):
        if isinstance(value, bytes):
            return value
        elif isinstance(value, str):
            return bytes(value, 'utf-8')
        raise TypeError(f"Cannot convert {type(value)} to bytes")

    # Default: pass through
    return value
```

**Validation Strategy**:
1. Check nullability before conversion
2. Validate length constraints for strings
3. Validate range for numeric types
4. Provide clear error messages with parameter name and expected type

**Alternatives Considered**:
- Rely on pyodbc automatic conversion - **Rejected**: Inconsistent behavior
- Use JSON for all parameters - **Rejected**: Loss of type safety
- No validation - **Rejected**: Poor error messages

## 5. Advanced Table Metadata

### Decision: Query SQL Server System Views Directly

**Rationale**:
- .NET implementation demonstrates effective SQL queries for metadata
- System views provide complete information
- Can be formatted as markdown tables for MCP responses

**Index Metadata Query**:
```sql
SELECT
    i.name AS IndexName,
    i.type_desc AS IndexType,
    i.is_primary_key AS IsPrimaryKey,
    i.is_unique AS IsUnique,
    i.is_unique_constraint AS IsUniqueConstraint,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS Columns
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID(@table_name)
GROUP BY i.name, i.type_desc, i.is_primary_key, i.is_unique, i.is_unique_constraint
ORDER BY i.index_id
```

**Foreign Key Query**:
```sql
SELECT
    fk.name AS ForeignKeyName,
    OBJECT_NAME(fk.parent_object_id) AS TableName,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS ColumnName,
    OBJECT_NAME(fk.referenced_object_id) AS ReferencedTable,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS ReferencedColumn,
    fk.delete_referential_action_desc AS DeleteAction,
    fk.update_referential_action_desc AS UpdateAction
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE fk.parent_object_id = OBJECT_ID(@table_name)
ORDER BY fk.name, fkc.constraint_column_id
```

**Table Size Query**:
```sql
SELECT
    SUM(p.rows) AS RowCount,
    SUM(a.total_pages) * 8 AS TotalSpaceKB,
    SUM(a.used_pages) * 8 AS UsedSpaceKB,
    (SUM(a.total_pages) - SUM(a.used_pages)) * 8 AS UnusedSpaceKB
FROM sys.tables t
INNER JOIN sys.indexes i ON t.object_id = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE t.object_id = OBJECT_ID(@table_name)
AND i.index_id <= 1  -- heap or clustered index only
GROUP BY t.name
```

**Computed Columns Query**:
```sql
SELECT
    c.name AS ColumnName,
    c.definition AS Formula,
    c.is_persisted AS IsPersisted
FROM sys.computed_columns c
WHERE c.object_id = OBJECT_ID(@table_name)
ORDER BY c.column_id
```

**Implementation**:
```python
def get_table_indexes(table_name: str, database_name: str | None = None):
    query = """..."""  # Index query above
    cursor.execute(query, table_name)
    return format_as_markdown_table(cursor.fetchall())
```

**Alternatives Considered**:
- INFORMATION_SCHEMA views - **Rejected**: Less complete than sys views
- Third-party libraries - **Rejected**: Adds dependencies
- sp_helpindex, sp_helpconstraint - **Rejected**: Inconsistent output format

## Summary of Technical Decisions

| Area | Decision | Key Reason |
|------|----------|-----------|
| **Session Management** | asyncio + ThreadPoolExecutor | pyodbc not async-native |
| **SP Parameters** | sys.parameters metadata | Complete type information |
| **OUTPUT Params** | Defer to future (MVP: INPUT only) | pyodbc limitations |
| **Capabilities** | Version-based + caching | Fast, reliable, proven |
| **Type Conversion** | Explicit mapping table | Type safety + validation |
| **Metadata** | sys.* system views | Complete, efficient |

## Risk Mitigation

1. **pyodbc Thread Safety**: Use connection per thread, never share connections
2. **Session Memory**: Implement aggressive cleanup (15-minute TTL)
3. **Type Conversion Errors**: Validate before execution, clear error messages
4. **Long-Running Queries**: Enforce timeout limits, provide cancellation (close connection)
5. **Capability Cache Staleness**: 1-hour TTL balances freshness vs performance

## Implementation Priorities

**Phase 1 (MVP)**:
1. Session management with basic cleanup
2. Stored procedure execution (INPUT parameters only)
3. Server capability detection with caching
4. Basic metadata (indexes, foreign keys)

**Phase 2 (Enhanced)**:
5. OUTPUT parameter support (using workarounds)
6. Advanced metadata (sizes, computed columns)
7. Enhanced error handling and logging
8. Comprehensive test coverage

## References

- `.NET Implementation`: `/Users/chongcheekeong/code/MCP/mssqlclient-mcp-server/dotnet-mcp-server/`
- `QuerySessionManager.cs`: Session management pattern
- `SqlServerCapabilityDetector.cs`: Capability detection approach
- `SqlTypeMapper.cs`: Type conversion logic
- `sys.parameters`: https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-parameters-transact-sql
- `pyodbc documentation`: https://github.com/mkleehammer/pyodbc/wiki
