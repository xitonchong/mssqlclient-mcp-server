# Data Model: Python MCP Server Advanced Features

**Feature**: 001-python-mcp-server
**Date**: 2026-01-03
**Phase**: 1 - Design

## Overview

This document defines the data models and entities required for implementing advanced features in the Python MCP Server. All models use Python dataclasses with type hints for clarity and runtime type checking.

## Core Entities

### 1. QuerySession

Represents a background query or stored procedure execution session.

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

class SessionStatus(Enum):
    """Status of a query session"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SessionType(Enum):
    """Type of session"""
    QUERY = "query"
    STORED_PROCEDURE = "stored_procedure"

@dataclass
class QuerySession:
    """Represents a background query execution session"""
    session_id: str
    query: str
    session_type: SessionType
    status: SessionStatus
    start_time: datetime
    database_name: Optional[str] = None
    parameters: Optional[dict[str, any]] = None
    end_time: Optional[datetime] = None
    row_count: int = 0
    results: Optional[str] = None
    error: Optional[str] = None
    timeout_seconds: int = 30

    def is_running(self) -> bool:
        return self.status == SessionStatus.RUNNING

    def duration_seconds(self) -> float:
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()
```

**Attributes**:
- `session_id`: Unique identifier (UUID string)
- `query`: SQL query or stored procedure name
- `session_type`: QUERY or STORED_PROCEDURE
- `status`: Current session status
- `start_time`: When session started (UTC)
- `database_name`: Target database (None = default from connection string)
- `parameters`: SP parameters (None for queries)
- `end_time`: When session completed/failed (None if still running)
- `row_count`: Number of rows returned
- `results`: Query results as formatted string (tab-delimited)
- `error`: Error message if failed
- `timeout_seconds`: Query timeout

**State Transitions**:
```
RUNNING -> COMPLETED (successful execution)
RUNNING -> FAILED (error during execution)
RUNNING -> CANCELLED (user cancellation)
```

**Validation Rules**:
- `session_id` must be valid UUID
- `query` cannot be empty
- `timeout_seconds` must be > 0
- `status` must progress forward (no COMPLETED -> RUNNING)

### 2. StoredProcedureParameter

Metadata about a stored procedure parameter.

```python
@dataclass
class StoredProcedureParameter:
    """Metadata for a stored procedure parameter"""
    parameter_name: str
    parameter_id: int
    data_type: str
    max_length: int
    precision: int
    scale: int
    is_output: bool
    has_default_value: bool
    default_value: Optional[str]
    is_nullable: bool

    def is_required(self) -> bool:
        """Parameter is required if it has no default and is not output-only"""
        return not self.has_default_value and not self.is_output

    def format_signature(self) -> str:
        """Format parameter signature for display"""
        parts = [self.parameter_name, self.data_type]
        if self.max_length > 0 and self.data_type in ('varchar', 'nvarchar', 'char', 'nchar'):
            parts.append(f"({self.max_length})")
        elif self.data_type in ('decimal', 'numeric'):
            parts.append(f"({self.precision},{self.scale})")
        if self.is_output:
            parts.append("OUTPUT")
        if self.is_nullable:
            parts.append("NULL")
        return " ".join(parts)
```

**Attributes**:
- `parameter_name`: Name with @ prefix (e.g., "@CustomerId")
- `parameter_id`: Ordinal position (0 = return value)
- `data_type`: SQL type name (e.g., "int", "nvarchar")
- `max_length`: Maximum length for strings/binary
- `precision`: Precision for decimal/numeric
- `scale`: Scale for decimal/numeric
- `is_output`: True if OUTPUT or RETURN parameter
- `has_default_value`: True if parameter has default
- `default_value`: Default value as string (if any)
- `is_nullable`: True if NULL allowed

**Validation Rules**:
- `parameter_name` must start with "@"
- `parameter_id` >= 0
- `data_type` must be valid SQL Server type
- If `has_default_value`, can omit from execution

### 3. ServerCapability

Information about SQL Server capabilities and features.

```python
@dataclass
class ServerCapability:
    """SQL Server capability information"""
    version: str
    major_version: int
    minor_version: int
    build_number: int
    edition: str
    is_azure_sql_db: bool
    is_azure_vm: bool
    is_on_premises: bool

    # Feature flags (based on version)
    supports_json: bool
    supports_columnstore: bool
    supports_temporal_tables: bool
    supports_row_level_security: bool
    supports_in_memory_oltp: bool
    supports_graph_database: bool
    supports_always_encrypted: bool
    supports_query_store: bool
    supports_resumable_index_ops: bool
    supports_data_compression: bool

    def get_version_display(self) -> str:
        """Format version for display"""
        return f"SQL Server {self.major_version}.{self.minor_version}.{self.build_number} ({self.edition})"

    def get_deployment_type(self) -> str:
        """Get deployment type as string"""
        if self.is_azure_sql_db:
            return "Azure SQL Database"
        elif self.is_azure_vm:
            return "Azure Virtual Machine"
        else:
            return "On-Premises"
```

**Attributes**:
- `version`: Full version string from @@VERSION
- `major_version`: Major version number (e.g., 15 for SQL 2019)
- `minor_version`: Minor version number
- `build_number`: Build number
- `edition`: Edition string (e.g., "Enterprise Edition")
- `is_azure_sql_db`: True if Azure SQL Database (EngineEdition=5)
- `is_azure_vm`: True if SQL Server on Azure VM
- `is_on_premises`: True if on-premises installation
- `supports_*`: Boolean flags for feature support

**Version Mapping**:
- SQL Server 2016: major_version = 13
- SQL Server 2017: major_version = 14
- SQL Server 2019: major_version = 15
- SQL Server 2022: major_version = 16

### 4. TableIndex

Information about a table index.

```python
@dataclass
class TableIndex:
    """Metadata about a table index"""
    index_name: str
    index_type: str
    is_primary_key: bool
    is_unique: bool
    is_unique_constraint: bool
    columns: list[str]
    included_columns: list[str] = field(default_factory=list)

    def format_columns(self) -> str:
        """Format column list for display"""
        col_str = ", ".join(self.columns)
        if self.included_columns:
            col_str += f" INCLUDE ({', '.join(self.included_columns)})"
        return col_str
```

**Attributes**:
- `index_name`: Name of the index
- `index_type`: Type (CLUSTERED, NONCLUSTERED, HEAP, etc.)
- `is_primary_key`: True if this is the primary key
- `is_unique`: True if index enforces uniqueness
- `is_unique_constraint`: True if this is a unique constraint
- `columns`: List of indexed column names (in order)
- `included_columns`: List of included (non-key) columns

### 5. ForeignKey

Information about a foreign key relationship.

```python
@dataclass
class ForeignKey:
    """Metadata about a foreign key relationship"""
    constraint_name: str
    table_name: str
    column_name: str
    referenced_table: str
    referenced_column: str
    delete_action: str
    update_action: str

    def format_relationship(self) -> str:
        """Format relationship for display"""
        return f"{self.table_name}.{self.column_name} -> {self.referenced_table}.{self.referenced_column}"
```

**Attributes**:
- `constraint_name`: Name of FK constraint
- `table_name`: Source table
- `column_name`: Source column
- `referenced_table`: Target table
- `referenced_column`: Target column
- `delete_action`: ON DELETE action (CASCADE, NO_ACTION, etc.)
- `update_action`: ON UPDATE action

### 6. TableStatistics

Size and row count information for a table.

```python
@dataclass
class TableStatistics:
    """Table size and row count statistics"""
    table_name: str
    row_count: int
    total_space_kb: int
    used_space_kb: int
    unused_space_kb: int

    @property
    def total_space_mb(self) -> float:
        return self.total_space_kb / 1024.0

    @property
    def used_space_mb(self) -> float:
        return self.used_space_kb / 1024.0

    def format_size(self) -> str:
        """Format size for display"""
        if self.total_space_kb < 1024:
            return f"{self.total_space_kb} KB"
        elif self.total_space_kb < 1024 * 1024:
            return f"{self.total_space_mb:.2f} MB"
        else:
            return f"{self.total_space_mb / 1024:.2f} GB"
```

**Attributes**:
- `table_name`: Name of the table
- `row_count`: Number of rows
- `total_space_kb`: Total space allocated (KB)
- `used_space_kb`: Space actually used (KB)
- `unused_space_kb`: Allocated but unused space (KB)

## Supporting Types

### TypeMapping

Maps Python types to SQL Server types for parameter conversion.

```python
from decimal import Decimal
from datetime import datetime, date, time
import uuid

TypeMapping = {
    # Python Type -> SQL Server Types (list of compatible types)
    int: ['int', 'bigint', 'smallint', 'tinyint', 'bit'],
    float: ['float', 'real'],
    Decimal: ['decimal', 'numeric', 'money', 'smallmoney'],
    str: ['varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext'],
    bool: ['bit'],
    datetime: ['datetime', 'datetime2', 'smalldatetime'],
    date: ['date'],
    time: ['time'],
    bytes: ['binary', 'varbinary', 'image'],
    uuid.UUID: ['uniqueidentifier'],
    type(None): []  # NULL compatible with any nullable type
}
```

## Entity Relationships

```
QuerySession
  ├─ session_id (PK)
  ├─ query
  ├─ parameters -> dict[str, any]
  └─ results -> formatted string

StoredProcedureParameter
  ├─ parameter_name
  ├─ data_type
  └─ (discovered from sys.parameters)

ServerCapability
  ├─ version info
  └─ feature flags (derived from major_version)

Table Metadata:
  TableIndex
    └─ columns: list[str]
  ForeignKey
    └─ relationship: table.column -> referenced_table.referenced_column
  TableStatistics
    └─ size metrics
```

## Persistence

**In-Memory Storage** (No database persistence):
- `QuerySession`: Stored in dictionary `{session_id: QuerySession}`
- `ServerCapability`: Cached in dictionary `{connection_string: (capability, timestamp)}`
- `StoredProcedureParameter`: Queried on-demand, not persisted
- Table Metadata: Queried on-demand, not persisted

**Cleanup**:
- Sessions: Automatic cleanup after 15 minutes of completion
- Capabilities: Cache TTL of 60 minutes

## Validation and Constraints

### QuerySession Constraints
- Maximum 10 concurrent sessions (configurable)
- Timeout between 1-600 seconds
- Results limited to 10MB in memory

### StoredProcedureParameter Constraints
- Parameter name must match SQL Server naming rules
- Required parameters must be provided
- Type conversion must succeed before execution

### ServerCapability Constraints
- Must successfully parse major_version
- Feature flags must be consistent with version

## Data Flow

### Session Creation Flow
```
1. User calls start_query MCP tool
2. Create QuerySession with status=RUNNING
3. Generate unique session_id (UUID)
4. Store in session dictionary
5. Launch background thread for execution
6. Return session_id to user
```

### Session Execution Flow
```
1. Background thread executes query
2. Update row_count periodically
3. Collect results in memory
4. Set status=COMPLETED or FAILED
5. Set end_time
6. Session available for retrieval
```

### Capability Detection Flow
```
1. Check cache for connection string
2. If cached and fresh, return cached
3. Otherwise, query SQL Server
4. Parse version and detect features
5. Cache result with timestamp
6. Return capability object
```

## JSON Serialization

All dataclasses must be JSON-serializable for MCP responses:

```python
import json
from dataclasses import asdict
from datetime import datetime
from enum import Enum

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        return super().default(obj)

# Usage
json.dumps(query_session, cls=EnhancedJSONEncoder)
```

## Migration from Current Model

**Existing Models** (in `models.py`):
- `TableInfo`
- `ColumnInfo`
- `StoredProcedureInfo`
- `DatabaseInfo`

**New Models** (to add):
- `QuerySession`
- `StoredProcedureParameter`
- `ServerCapability`
- `TableIndex`
- `ForeignKey`
- `TableStatistics`

**No Breaking Changes**: All existing models remain unchanged. New models are additive.

## Summary

This data model provides:
- ✅ Complete session tracking for background execution
- ✅ Type-safe stored procedure parameter metadata
- ✅ Comprehensive server capability information
- ✅ Rich table metadata (indexes, foreign keys, statistics)
- ✅ JSON serialization for MCP responses
- ✅ No persistence (in-memory only)
- ✅ Backward compatible with existing models
