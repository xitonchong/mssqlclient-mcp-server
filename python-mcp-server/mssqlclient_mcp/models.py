"""Data models for MSSQL MCP Server."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Any
from enum import Enum
import json


@dataclass
class TableInfo:
    """Information about a database table."""

    schema: str
    name: str
    create_date: datetime
    modify_date: datetime
    row_count: Optional[int] = None
    size_mb: Optional[float] = None
    index_count: Optional[int] = None
    foreign_key_count: Optional[int] = None
    table_type: str = "Normal"


@dataclass
class TableColumnInfo:
    """Information about a table column."""

    name: str
    data_type: str
    max_length: str
    is_nullable: str
    description: str = ""


@dataclass
class TableSchemaInfo:
    """Schema information for a table."""

    table_name: str
    database_name: str
    description: str
    columns: List[TableColumnInfo]


@dataclass
class DatabaseInfo:
    """Information about a database."""

    name: str
    state: str
    create_date: datetime
    size_mb: Optional[float] = None
    owner: str = ""
    compatibility_level: str = ""
    collation_name: str = ""
    recovery_model: str = ""
    is_read_only: bool = False


@dataclass
class StoredProcedureParameterInfo:
    """Information about a stored procedure parameter."""

    name: str
    data_type: str
    length: int
    precision: int
    scale: int
    is_output: bool
    is_nullable: bool
    default_value: Optional[str] = None


@dataclass
class StoredProcedureInfo:
    """Information about a stored procedure."""

    schema_name: str
    name: str
    create_date: datetime
    modify_date: datetime
    owner: str
    parameters: List[StoredProcedureParameterInfo]
    is_function: bool = False
    last_execution_time: Optional[datetime] = None
    execution_count: Optional[int] = None
    average_duration_ms: Optional[int] = None


# Enums for Session Management

class SessionStatus(Enum):
    """Status of a query session."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionType(Enum):
    """Type of session."""
    QUERY = "query"
    STORED_PROCEDURE = "stored_procedure"


@dataclass
class QuerySession:
    """Represents a background query execution session."""

    session_id: str
    query: str
    session_type: SessionType
    status: SessionStatus
    start_time: datetime
    database_name: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    end_time: Optional[datetime] = None
    row_count: int = 0
    results: Optional[str] = None
    error: Optional[str] = None
    timeout_seconds: int = 30

    def is_running(self) -> bool:
        """Check if session is still running."""
        return self.status == SessionStatus.RUNNING

    def duration_seconds(self) -> float:
        """Calculate session duration in seconds."""
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()


@dataclass
class StoredProcedureParameter:
    """Metadata for a stored procedure parameter."""

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
        """Parameter is required if it has no default and is not output-only."""
        return not self.has_default_value and not self.is_output

    def format_signature(self) -> str:
        """Format parameter signature for display."""
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


@dataclass
class ServerCapability:
    """SQL Server capability information."""

    version: str
    major_version: int
    minor_version: int
    build_number: int
    edition: str
    is_azure_sql_db: bool
    is_azure_vm: bool
    is_on_premises: bool
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
        """Format version for display."""
        return f"SQL Server {self.major_version}.{self.minor_version}.{self.build_number} ({self.edition})"

    def get_deployment_type(self) -> str:
        """Get deployment type as string."""
        if self.is_azure_sql_db:
            return "Azure SQL Database"
        elif self.is_azure_vm:
            return "Azure Virtual Machine"
        else:
            return "On-Premises"


@dataclass
class TableIndex:
    """Metadata about a table index."""

    index_name: str
    index_type: str
    is_primary_key: bool
    is_unique: bool
    is_unique_constraint: bool
    columns: List[str]
    included_columns: List[str] = field(default_factory=list)

    def format_columns(self) -> str:
        """Format column list for display."""
        col_str = ", ".join(self.columns)
        if self.included_columns:
            col_str += f" INCLUDE ({', '.join(self.included_columns)})"
        return col_str


@dataclass
class ForeignKey:
    """Metadata about a foreign key relationship."""

    constraint_name: str
    table_name: str
    column_name: str
    referenced_table: str
    referenced_column: str
    delete_action: str
    update_action: str

    def format_relationship(self) -> str:
        """Format relationship for display."""
        return f"{self.table_name}.{self.column_name} -> {self.referenced_table}.{self.referenced_column}"


@dataclass
class TableStatistics:
    """Table size and row count statistics."""

    table_name: str
    row_count: int
    total_space_kb: int
    used_space_kb: int
    unused_space_kb: int

    @property
    def total_space_mb(self) -> float:
        """Total space in megabytes."""
        return self.total_space_kb / 1024.0

    @property
    def used_space_mb(self) -> float:
        """Used space in megabytes."""
        return self.used_space_kb / 1024.0

    def format_size(self) -> str:
        """Format size for display."""
        if self.total_space_kb < 1024:
            return f"{self.total_space_kb} KB"
        elif self.total_space_kb < 1024 * 1024:
            return f"{self.total_space_mb:.2f} MB"
        else:
            return f"{self.total_space_mb / 1024:.2f} GB"


# JSON Encoder for MCP responses

class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime and Enum types."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        return super().default(obj)
