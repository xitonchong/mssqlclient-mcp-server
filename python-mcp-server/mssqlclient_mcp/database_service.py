"""Database service for SQL Server operations."""

import pyodbc
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import uuid
import threading
from .models import (
    TableInfo,
    TableColumnInfo,
    TableSchemaInfo,
    DatabaseInfo,
    StoredProcedureInfo,
    StoredProcedureParameterInfo,
    QuerySession,
    SessionStatus,
    SessionType,
    StoredProcedureParameter,
    ServerCapability,
    TableIndex,
    ForeignKey,
    TableStatistics,
)
from .config import DatabaseConfiguration
from .type_mapper import convert_parameters_for_execution


class DatabaseService:
    """Core database service for SQL Server operations."""

    def __init__(self, config: DatabaseConfiguration):
        """Initialize the database service."""
        self.connection_string = config.connection_string
        self.config = config

    def _get_connection(self, database_name: Optional[str] = None) -> pyodbc.Connection:
        """Get a database connection."""
        connection_string = self.connection_string

        # If a specific database is requested, modify the connection string
        if database_name:
            # Parse and replace database name in connection string
            parts = connection_string.split(";")
            new_parts = []
            database_set = False

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                if part.lower().startswith("database=") or part.lower().startswith("initial catalog="):
                    new_parts.append(f"Database={database_name}")
                    database_set = True
                else:
                    new_parts.append(part)

            if not database_set:
                new_parts.append(f"Database={database_name}")

            connection_string = ";".join(new_parts)

        return pyodbc.connect(
            connection_string,
            timeout=self.config.connection_timeout_seconds
        )

    async def list_tables(
        self,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> List[TableInfo]:
        """List all tables in the database."""
        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout
            # Connection timeout is already set when creating the connection

            # Query to get table information
            query = """
                SELECT
                    s.name AS SchemaName,
                    t.name AS TableName,
                    t.create_date AS CreateDate,
                    t.modify_date AS ModifyDate,
                    'Normal' AS TableType
                FROM
                    sys.tables t
                JOIN
                    sys.schemas s ON t.schema_id = s.schema_id
                WHERE
                    t.is_ms_shipped = 0
                ORDER BY
                    s.name, t.name
            """

            cursor.execute(query)
            tables = []

            for row in cursor.fetchall():
                table = TableInfo(
                    schema=row.SchemaName,
                    name=row.TableName,
                    create_date=row.CreateDate,
                    modify_date=row.ModifyDate,
                    table_type=row.TableType,
                )
                tables.append(table)

            # Enhance with row counts
            for table in tables:
                try:
                    count_query = f"SELECT COUNT(*) FROM [{table.schema}].[{table.name}]"
                    cursor.execute(count_query)
                    count = cursor.fetchone()[0]
                    table.row_count = count
                except Exception as e:
                    # If counting fails, just skip
                    pass

            return tables
        finally:
            conn.close()

    async def get_table_schema(
        self,
        table_name: str,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> TableSchemaInfo:
        """Get schema information for a specific table."""
        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            # Parse schema and table name
            schema_name = "dbo"
            table_name_only = table_name

            if "." in table_name:
                parts = table_name.split(".", 1)
                schema_name = parts[0].strip("[]")
                table_name_only = parts[1].strip("[]")

            # Get current database name
            cursor.execute("SELECT DB_NAME()")
            current_db = cursor.fetchone()[0]

            # Query to get column information
            query = """
                SELECT
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    CAST(ISNULL(c.CHARACTER_MAXIMUM_LENGTH, -1) AS VARCHAR(20)) AS MAX_LENGTH,
                    c.IS_NULLABLE
                FROM
                    INFORMATION_SCHEMA.COLUMNS c
                WHERE
                    c.TABLE_SCHEMA = ? AND c.TABLE_NAME = ?
                ORDER BY
                    c.ORDINAL_POSITION
            """

            cursor.execute(query, schema_name, table_name_only)
            columns = []

            for row in cursor.fetchall():
                column = TableColumnInfo(
                    name=row.COLUMN_NAME,
                    data_type=row.DATA_TYPE,
                    max_length=row.MAX_LENGTH,
                    is_nullable=row.IS_NULLABLE,
                )
                columns.append(column)

            if not columns:
                raise ValueError(
                    f"Table '{table_name}' does not exist in database '{current_db}' "
                    "or you don't have permission to access it"
                )

            return TableSchemaInfo(
                table_name=table_name,
                database_name=current_db,
                description="",
                columns=columns,
            )
        finally:
            conn.close()

    async def execute_query(
        self,
        query: str,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead
            cursor.execute(query)

            # Get column names
            columns = [column[0] for column in cursor.description] if cursor.description else []

            # Fetch results
            rows = cursor.fetchall()
            results = []

            for row in rows:
                result = {}
                for i, value in enumerate(row):
                    # Convert datetime objects to strings for JSON serialization
                    if isinstance(value, datetime):
                        result[columns[i]] = value.isoformat()
                    else:
                        result[columns[i]] = value
                results.append(result)

            return results
        finally:
            conn.close()

    async def list_databases(
        self, timeout_seconds: Optional[int] = None
    ) -> List[DatabaseInfo]:
        """List all databases on the server."""
        conn = self._get_connection()
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            query = """
                SELECT
                    name AS Name,
                    state_desc AS State,
                    create_date AS CreateDate
                FROM
                    sys.databases
                ORDER BY
                    name
            """

            cursor.execute(query)
            databases = []

            for row in cursor.fetchall():
                db = DatabaseInfo(
                    name=row.Name,
                    state=row.State,
                    create_date=row.CreateDate,
                )
                databases.append(db)

            return databases
        finally:
            conn.close()

    async def list_stored_procedures(
        self,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> List[StoredProcedureInfo]:
        """List all stored procedures in the database."""
        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            query = """
                SELECT
                    s.name AS SchemaName,
                    p.name AS ProcedureName,
                    p.create_date AS CreateDate,
                    p.modify_date AS ModifyDate,
                    ISNULL(USER_NAME(p.principal_id), '') AS Owner,
                    CAST(CASE WHEN p.type = 'P' THEN 0 ELSE 1 END AS BIT) AS IsFunction
                FROM
                    sys.procedures p
                JOIN
                    sys.schemas s ON p.schema_id = s.schema_id
                WHERE
                    p.is_ms_shipped = 0
                ORDER BY
                    s.name, p.name
            """

            cursor.execute(query)
            procedures = []

            for row in cursor.fetchall():
                proc = StoredProcedureInfo(
                    schema_name=row.SchemaName,
                    name=row.ProcedureName,
                    create_date=row.CreateDate,
                    modify_date=row.ModifyDate,
                    owner=row.Owner,
                    is_function=bool(row.IsFunction),
                    parameters=[],
                )
                procedures.append(proc)

            return procedures
        finally:
            conn.close()

    async def get_stored_procedure_definition(
        self,
        procedure_name: str,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """Get the definition of a stored procedure."""
        if not procedure_name or not procedure_name.strip():
            raise ValueError("Procedure name cannot be empty")

        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            # Parse schema and procedure name
            schema_name = "dbo"
            proc_name_only = procedure_name

            if "." in procedure_name:
                parts = procedure_name.split(".", 1)
                schema_name = parts[0].strip("[]")
                proc_name_only = parts[1].strip("[]")

            query = """
                SELECT ISNULL(m.definition, '') AS Definition
                FROM sys.procedures p
                JOIN sys.schemas s ON p.schema_id = s.schema_id
                LEFT JOIN sys.sql_modules m ON p.object_id = m.object_id
                WHERE s.name = ? AND p.name = ?
            """

            cursor.execute(query, schema_name, proc_name_only)
            row = cursor.fetchone()

            if not row:
                raise ValueError(
                    f"Stored procedure '{schema_name}.{proc_name_only}' does not exist "
                    "or you don't have permission to access it"
                )

            definition = row.Definition or ""

            if not definition.strip():
                definition = "-- Unable to retrieve stored procedure definition. It may be encrypted."

            return definition
        finally:
            conn.close()

    async def execute_stored_procedure(
        self,
        procedure_name: str,
        parameters: Dict[str, Any],
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a stored procedure with type-safe parameters.

        Args:
            procedure_name: Name of stored procedure (with optional schema)
            parameters: Dictionary of parameter names -> values
            database_name: Optional database name
            timeout_seconds: Optional timeout in seconds

        Returns:
            List of result rows as dictionaries

        Raises:
            ValueError: If required parameters missing or type conversion fails
        """
        if not procedure_name or not procedure_name.strip():
            raise ValueError("Procedure name cannot be empty")

        # Get parameter metadata first
        param_metadata = await self.get_sp_parameters(procedure_name, database_name, timeout_seconds)

        # Convert and validate parameters
        param_values = convert_parameters_for_execution(parameters, param_metadata)

        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            # Parse schema and procedure name
            schema_name = "dbo"
            proc_name_only = procedure_name

            if "." in procedure_name:
                parts = procedure_name.split(".", 1)
                schema_name = parts[0].strip("[]")
                proc_name_only = parts[1].strip("[]")

            # Build parameter placeholders (skip parameter_id=0 which is return value)
            input_params = [p for p in param_metadata if p.parameter_id > 0 and not p.is_output]
            param_placeholders = ", ".join(["?" for _ in input_params])

            # Execute stored procedure
            if param_placeholders:
                query = f"EXEC [{schema_name}].[{proc_name_only}] {param_placeholders}"
                cursor.execute(query, *param_values)
            else:
                query = f"EXEC [{schema_name}].[{proc_name_only}]"
                cursor.execute(query)

            # Collect all result sets
            all_results = []
            while True:
                # Get column names
                columns = [column[0] for column in cursor.description] if cursor.description else []

                # Fetch results from this result set
                if columns:
                    rows = cursor.fetchall()
                    for row in rows:
                        result = {}
                        for i, value in enumerate(row):
                            if isinstance(value, datetime):
                                result[columns[i]] = value.isoformat()
                            else:
                                result[columns[i]] = value
                        all_results.append(result)

                # Try to move to next result set
                if not cursor.nextset():
                    break

            return all_results
        finally:
            conn.close()

    async def get_sp_parameters(
        self,
        procedure_name: str,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> List[StoredProcedureParameter]:
        """
        Get parameter metadata for a stored procedure.

        Args:
            procedure_name: Name of the stored procedure (with optional schema)
            database_name: Optional database name
            timeout_seconds: Optional timeout in seconds

        Returns:
            List of StoredProcedureParameter objects
        """
        if not procedure_name or not procedure_name.strip():
            raise ValueError("Procedure name cannot be empty")

        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            # Parse schema and procedure name
            schema_name = "dbo"
            proc_name_only = procedure_name

            if "." in procedure_name:
                parts = procedure_name.split(".", 1)
                schema_name = parts[0].strip("[]")
                proc_name_only = parts[1].strip("[]")

            # Query to get parameter information from sys.parameters
            query = """
                SELECT
                    p.name AS ParameterName,
                    p.parameter_id AS ParameterId,
                    t.name AS DataType,
                    p.max_length AS MaxLength,
                    p.precision AS Precision,
                    p.scale AS Scale,
                    p.is_output AS IsOutput,
                    p.has_default_value AS HasDefaultValue,
                    CAST(p.default_value AS NVARCHAR(MAX)) AS DefaultValue,
                    p.is_nullable AS IsNullable
                FROM sys.parameters p
                JOIN sys.types t ON p.user_type_id = t.user_type_id
                JOIN sys.procedures sp ON p.object_id = sp.object_id
                JOIN sys.schemas s ON sp.schema_id = s.schema_id
                WHERE s.name = ? AND sp.name = ?
                ORDER BY p.parameter_id
            """

            cursor.execute(query, schema_name, proc_name_only)
            parameters = []

            for row in cursor.fetchall():
                param = StoredProcedureParameter(
                    parameter_name=row.ParameterName,
                    parameter_id=row.ParameterId,
                    data_type=row.DataType,
                    max_length=row.MaxLength,
                    precision=row.Precision,
                    scale=row.Scale,
                    is_output=bool(row.IsOutput),
                    has_default_value=bool(row.HasDefaultValue),
                    default_value=row.DefaultValue,
                    is_nullable=bool(row.IsNullable),
                )
                parameters.append(param)

            return parameters
        finally:
            conn.close()

    async def get_table_indexes(
        self,
        table_name: str,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> List[TableIndex]:
        """
        Get index information for a table.

        Args:
            table_name: Name of the table (with optional schema)
            database_name: Optional database name
            timeout_seconds: Optional timeout in seconds

        Returns:
            List of TableIndex objects
        """
        if not table_name or not table_name.strip():
            raise ValueError("Table name cannot be empty")

        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            # Parse schema and table name
            schema_name = "dbo"
            table_name_only = table_name

            if "." in table_name:
                parts = table_name.split(".", 1)
                schema_name = parts[0].strip("[]")
                table_name_only = parts[1].strip("[]")

            # Query to get index information
            query = """
                SELECT
                    i.name AS IndexName,
                    i.type_desc AS IndexType,
                    i.is_primary_key AS IsPrimaryKey,
                    i.is_unique AS IsUnique,
                    i.is_unique_constraint AS IsUniqueConstraint,
                    STRING_AGG(
                        CASE WHEN ic.is_included_column = 0 THEN c.name ELSE NULL END,
                        ', '
                    ) WITHIN GROUP (ORDER BY ic.key_ordinal) AS KeyColumns,
                    STRING_AGG(
                        CASE WHEN ic.is_included_column = 1 THEN c.name ELSE NULL END,
                        ', '
                    ) AS IncludedColumns
                FROM sys.indexes i
                INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
                INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                INNER JOIN sys.tables t ON i.object_id = t.object_id
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = ? AND t.name = ?
                GROUP BY i.index_id, i.name, i.type_desc, i.is_primary_key, i.is_unique, i.is_unique_constraint
                ORDER BY i.index_id
            """

            cursor.execute(query, schema_name, table_name_only)
            indexes = []

            for row in cursor.fetchall():
                # Parse columns
                key_columns = row.KeyColumns.split(", ") if row.KeyColumns else []
                included_columns = row.IncludedColumns.split(", ") if row.IncludedColumns else []

                index = TableIndex(
                    index_name=row.IndexName,
                    index_type=row.IndexType,
                    is_primary_key=bool(row.IsPrimaryKey),
                    is_unique=bool(row.IsUnique),
                    is_unique_constraint=bool(row.IsUniqueConstraint),
                    columns=key_columns,
                    included_columns=included_columns,
                )
                indexes.append(index)

            return indexes
        finally:
            conn.close()

    async def get_table_foreign_keys(
        self,
        table_name: str,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> List[ForeignKey]:
        """
        Get foreign key relationships for a table.

        Args:
            table_name: Name of the table (with optional schema)
            database_name: Optional database name
            timeout_seconds: Optional timeout in seconds

        Returns:
            List of ForeignKey objects
        """
        if not table_name or not table_name.strip():
            raise ValueError("Table name cannot be empty")

        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            # Parse schema and table name
            schema_name = "dbo"
            table_name_only = table_name

            if "." in table_name:
                parts = table_name.split(".", 1)
                schema_name = parts[0].strip("[]")
                table_name_only = parts[1].strip("[]")

            # Query to get foreign key information
            query = """
                SELECT
                    fk.name AS ForeignKeyName,
                    OBJECT_SCHEMA_NAME(fk.parent_object_id) + '.' + OBJECT_NAME(fk.parent_object_id) AS TableName,
                    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS ColumnName,
                    OBJECT_SCHEMA_NAME(fk.referenced_object_id) + '.' + OBJECT_NAME(fk.referenced_object_id) AS ReferencedTable,
                    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS ReferencedColumn,
                    fk.delete_referential_action_desc AS DeleteAction,
                    fk.update_referential_action_desc AS UpdateAction
                FROM sys.foreign_keys fk
                INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = ? AND t.name = ?
                ORDER BY fk.name, fkc.constraint_column_id
            """

            cursor.execute(query, schema_name, table_name_only)
            foreign_keys = []

            for row in cursor.fetchall():
                fk = ForeignKey(
                    constraint_name=row.ForeignKeyName,
                    table_name=row.TableName,
                    column_name=row.ColumnName,
                    referenced_table=row.ReferencedTable,
                    referenced_column=row.ReferencedColumn,
                    delete_action=row.DeleteAction,
                    update_action=row.UpdateAction,
                )
                foreign_keys.append(fk)

            return foreign_keys
        finally:
            conn.close()

    async def get_table_statistics(
        self,
        table_name: str,
        database_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> TableStatistics:
        """
        Get size and row count statistics for a table.

        Args:
            table_name: Name of the table (with optional schema)
            database_name: Optional database name
            timeout_seconds: Optional timeout in seconds

        Returns:
            TableStatistics object
        """
        if not table_name or not table_name.strip():
            raise ValueError("Table name cannot be empty")

        conn = self._get_connection(database_name)
        timeout = timeout_seconds or self.config.default_command_timeout_seconds

        try:
            cursor = conn.cursor()
            # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

            # Parse schema and table name
            schema_name = "dbo"
            table_name_only = table_name

            if "." in table_name:
                parts = table_name.split(".", 1)
                schema_name = parts[0].strip("[]")
                table_name_only = parts[1].strip("[]")

            # Query to get table statistics
            query = """
                SELECT
                    t.name AS TableName,
                    SUM(p.rows) AS RowCount,
                    SUM(a.total_pages) * 8 AS TotalSpaceKB,
                    SUM(a.used_pages) * 8 AS UsedSpaceKB,
                    (SUM(a.total_pages) - SUM(a.used_pages)) * 8 AS UnusedSpaceKB
                FROM sys.tables t
                INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                INNER JOIN sys.indexes i ON t.object_id = i.object_id
                INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE s.name = ? AND t.name = ?
                AND i.index_id <= 1  -- heap or clustered index only
                GROUP BY t.name
            """

            cursor.execute(query, schema_name, table_name_only)
            row = cursor.fetchone()

            if not row:
                raise ValueError(
                    f"Table '{schema_name}.{table_name_only}' does not exist "
                    "or you don't have permission to access it"
                )

            stats = TableStatistics(
                table_name=f"{schema_name}.{row.TableName}",
                row_count=row.RowCount or 0,
                total_space_kb=row.TotalSpaceKB or 0,
                used_space_kb=row.UsedSpaceKB or 0,
                unused_space_kb=row.UnusedSpaceKB or 0,
            )

            return stats
        finally:
            conn.close()


class SessionManager:
    """Manages background query and stored procedure execution sessions."""

    def __init__(self, database_service: DatabaseService, max_workers: int = 10):
        """
        Initialize the session manager.

        Args:
            database_service: The database service to use for queries
            max_workers: Maximum number of concurrent background sessions
        """
        self.database_service = database_service
        self._sessions: Dict[str, QuerySession] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._max_sessions = max_workers
        self._cleanup_interval_minutes = 15

    def start_query(
        self,
        query: str,
        database_name: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> str:
        """
        Start a query in the background.

        Args:
            query: SQL query to execute
            database_name: Optional database name
            timeout_seconds: Query timeout in seconds

        Returns:
            session_id: Unique session identifier

        Raises:
            RuntimeError: If maximum concurrent sessions reached
        """
        with self._lock:
            # Check concurrent session limit
            active_sessions = sum(
                1 for s in self._sessions.values() if s.is_running()
            )
            if active_sessions >= self._max_sessions:
                raise RuntimeError(
                    f"Maximum concurrent sessions ({self._max_sessions}) reached"
                )

            # Create new session
            session_id = str(uuid.uuid4())
            session = QuerySession(
                session_id=session_id,
                query=query,
                session_type=SessionType.QUERY,
                status=SessionStatus.RUNNING,
                start_time=datetime.utcnow(),
                database_name=database_name,
                timeout_seconds=timeout_seconds,
            )
            self._sessions[session_id] = session

        # Launch background execution
        self._executor.submit(self._execute_query_in_background, session)

        return session_id

    def _execute_query_in_background(self, session: QuerySession) -> None:
        """
        Execute a query in the background thread pool.

        Args:
            session: The query session to execute
        """
        try:
            # Get connection for this thread
            conn = self.database_service._get_connection(session.database_name)

            try:
                cursor = conn.cursor()
                # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead
                cursor.execute(session.query)

                # Get column names
                columns = (
                    [column[0] for column in cursor.description]
                    if cursor.description
                    else []
                )

                # Fetch results
                rows = cursor.fetchall()
                session.row_count = len(rows)

                # Format results as tab-delimited string
                result_lines = []
                if columns:
                    result_lines.append("\t".join(columns))

                for row in rows:
                    row_data = []
                    for value in row:
                        if value is None:
                            row_data.append("NULL")
                        elif isinstance(value, datetime):
                            row_data.append(value.isoformat())
                        else:
                            row_data.append(str(value))
                    result_lines.append("\t".join(row_data))

                session.results = "\n".join(result_lines)
                session.status = SessionStatus.COMPLETED

            finally:
                conn.close()

        except Exception as e:
            session.status = SessionStatus.FAILED
            session.error = str(e)
        finally:
            session.end_time = datetime.utcnow()

    def get_session(self, session_id: str) -> Optional[QuerySession]:
        """
        Get a session by ID.

        Args:
            session_id: The session identifier

        Returns:
            QuerySession if found, None otherwise
        """
        with self._lock:
            return self._sessions.get(session_id)

    def list_sessions(self) -> List[QuerySession]:
        """
        Get all sessions.

        Returns:
            List of all query sessions
        """
        with self._lock:
            return list(self._sessions.values())

    def cancel_session(self, session_id: str) -> bool:
        """
        Cancel a running session.

        Args:
            session_id: The session identifier

        Returns:
            True if session was cancelled, False if not found or already completed

        Note:
            Due to pyodbc limitations, cancellation closes the connection but
            the query may still complete on the server side.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session or not session.is_running():
                return False

            session.status = SessionStatus.CANCELLED
            session.end_time = datetime.utcnow()
            session.error = "Cancelled by user"

        return True

    def cleanup_completed_sessions(self) -> int:
        """
        Remove completed sessions older than the cleanup interval.

        Returns:
            Number of sessions removed
        """
        cutoff_time = datetime.utcnow() - timedelta(
            minutes=self._cleanup_interval_minutes
        )

        with self._lock:
            sessions_to_remove = [
                session_id
                for session_id, session in self._sessions.items()
                if session.end_time
                and session.end_time < cutoff_time
                and not session.is_running()
            ]

            for session_id in sessions_to_remove:
                del self._sessions[session_id]

            return len(sessions_to_remove)

    def start_stored_procedure(
        self,
        procedure_name: str,
        parameters: Dict[str, Any],
        database_name: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> str:
        """
        Start a stored procedure execution in the background.

        Args:
            procedure_name: Name of stored procedure (with optional schema)
            parameters: Dictionary of parameter names -> values
            database_name: Optional database name
            timeout_seconds: Execution timeout in seconds

        Returns:
            session_id: Unique session identifier

        Raises:
            RuntimeError: If maximum concurrent sessions reached
        """
        with self._lock:
            # Check concurrent session limit
            active_sessions = sum(
                1 for s in self._sessions.values() if s.is_running()
            )
            if active_sessions >= self._max_sessions:
                raise RuntimeError(
                    f"Maximum concurrent sessions ({self._max_sessions}) reached"
                )

            # Create new session
            session_id = str(uuid.uuid4())
            session = QuerySession(
                session_id=session_id,
                query=procedure_name,  # Store procedure name in query field
                session_type=SessionType.STORED_PROCEDURE,
                status=SessionStatus.RUNNING,
                start_time=datetime.utcnow(),
                database_name=database_name,
                parameters=parameters,  # Store parameters
                timeout_seconds=timeout_seconds,
            )
            self._sessions[session_id] = session

        # Launch background execution
        self._executor.submit(self._execute_sp_in_background, session)

        return session_id

    def _execute_sp_in_background(self, session: QuerySession) -> None:
        """
        Execute a stored procedure in the background thread pool.

        Args:
            session: The session with stored procedure info
        """
        import asyncio

        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Get parameter metadata
                param_metadata_future = self.database_service.get_sp_parameters(
                    session.query,  # procedure_name stored in query field
                    session.database_name,
                    session.timeout_seconds
                )
                param_metadata = loop.run_until_complete(param_metadata_future)

                # Convert and validate parameters
                param_values = convert_parameters_for_execution(
                    session.parameters or {},
                    param_metadata
                )

                # Get connection for this thread
                conn = self.database_service._get_connection(session.database_name)

                try:
                    cursor = conn.cursor()
                    # Note: pyodbc doesn't support cursor.timeout - using connection timeout instead

                    # Parse schema and procedure name
                    schema_name = "dbo"
                    proc_name_only = session.query

                    if "." in session.query:
                        parts = session.query.split(".", 1)
                        schema_name = parts[0].strip("[]")
                        proc_name_only = parts[1].strip("[]")

                    # Build parameter placeholders (skip parameter_id=0 and OUTPUT params)
                    input_params = [p for p in param_metadata if p.parameter_id > 0 and not p.is_output]
                    param_placeholders = ", ".join(["?" for _ in input_params])

                    # Execute stored procedure
                    if param_placeholders:
                        query = f"EXEC [{schema_name}].[{proc_name_only}] {param_placeholders}"
                        cursor.execute(query, *param_values)
                    else:
                        query = f"EXEC [{schema_name}].[{proc_name_only}]"
                        cursor.execute(query)

                    # Collect all result sets
                    result_lines = []
                    total_rows = 0

                    while True:
                        # Get column names
                        columns = (
                            [column[0] for column in cursor.description]
                            if cursor.description
                            else []
                        )

                        # Fetch results from this result set
                        if columns:
                            # Add header for this result set
                            if result_lines:
                                result_lines.append("")  # Separator between result sets
                            result_lines.append("\t".join(columns))

                            rows = cursor.fetchall()
                            for row in rows:
                                row_data = []
                                for value in row:
                                    if value is None:
                                        row_data.append("NULL")
                                    elif isinstance(value, datetime):
                                        row_data.append(value.isoformat())
                                    else:
                                        row_data.append(str(value))
                                result_lines.append("\t".join(row_data))
                                total_rows += 1

                        # Try to move to next result set
                        if not cursor.nextset():
                            break

                    session.row_count = total_rows
                    session.results = "\n".join(result_lines)
                    session.status = SessionStatus.COMPLETED

                finally:
                    conn.close()

            finally:
                loop.close()

        except Exception as e:
            session.status = SessionStatus.FAILED
            session.error = str(e)
        finally:
            session.end_time = datetime.utcnow()


class CapabilityDetector:
    """Detects SQL Server capabilities and features with caching."""

    # Cache TTL in minutes
    CACHE_TTL_MINUTES = 60

    def __init__(self, database_service: DatabaseService):
        """
        Initialize the capability detector.

        Args:
            database_service: The database service to use for queries
        """
        self.database_service = database_service
        # Cache: {connection_string: (ServerCapability, timestamp)}
        self._cache: Dict[str, Tuple[ServerCapability, datetime]] = {}
        self._lock = threading.Lock()

    async def get_capabilities(
        self,
        database_name: Optional[str] = None,
    ) -> ServerCapability:
        """
        Get server capabilities with caching.

        Args:
            database_name: Optional database name

        Returns:
            ServerCapability object with version and feature information
        """
        # Use connection string as cache key
        cache_key = self.database_service.connection_string
        if database_name:
            cache_key += f"|{database_name}"

        # Check cache
        with self._lock:
            if cache_key in self._cache:
                capability, timestamp = self._cache[cache_key]
                age_minutes = (datetime.utcnow() - timestamp).total_seconds() / 60
                if age_minutes < self.CACHE_TTL_MINUTES:
                    return capability

        # Detect capabilities
        capability = await self._detect_capabilities(database_name)

        # Update cache
        with self._lock:
            self._cache[cache_key] = (capability, datetime.utcnow())

        return capability

    async def _detect_capabilities(
        self, database_name: Optional[str] = None
    ) -> ServerCapability:
        """
        Detect server capabilities by querying SQL Server.

        Args:
            database_name: Optional database name

        Returns:
            ServerCapability object
        """
        conn = self.database_service._get_connection(database_name)

        try:
            cursor = conn.cursor()

            # Query version and edition information
            query = """
                SELECT
                    @@VERSION AS ServerVersion,
                    CAST(SERVERPROPERTY('ProductVersion') AS NVARCHAR(128)) AS ProductVersion,
                    CAST(SERVERPROPERTY('Edition') AS NVARCHAR(128)) AS Edition,
                    CAST(SERVERPROPERTY('EngineEdition') AS INT) AS EngineEdition,
                    CAST(SERVERPROPERTY('ProductMajorVersion') AS INT) AS MajorVersion
            """

            cursor.execute(query)
            row = cursor.fetchone()

            server_version = row.ServerVersion
            product_version = row.ProductVersion
            edition = row.Edition
            engine_edition = row.EngineEdition
            major_version = row.MajorVersion if row.MajorVersion else self._parse_major_version(product_version)

            # Detect deployment type
            is_azure_sql_db = (engine_edition == 5)
            is_azure_vm = self._detect_azure_vm(server_version)
            is_on_premises = not is_azure_sql_db and not is_azure_vm

            # Determine feature support based on version
            features = self._determine_feature_support(major_version, is_azure_sql_db)

            return ServerCapability(
                version=server_version,
                major_version=major_version,
                minor_version=0,  # Not critical for feature detection
                build_number=0,   # Not critical for feature detection
                edition=edition,
                is_azure_sql_db=is_azure_sql_db,
                is_azure_vm=is_azure_vm,
                is_on_premises=is_on_premises,
                **features
            )

        finally:
            conn.close()

    def _parse_major_version(self, product_version: str) -> int:
        """
        Parse major version from product version string.

        Args:
            product_version: Version string like "15.0.2000.5"

        Returns:
            Major version number
        """
        try:
            parts = product_version.split(".")
            return int(parts[0])
        except:
            return 0

    def _detect_azure_vm(self, server_version: str) -> bool:
        """
        Detect if running on Azure VM.

        Args:
            server_version: Server version string

        Returns:
            True if Azure VM, False otherwise
        """
        # Azure VM detection is heuristic-based
        # Typically contains "Azure" but not in a way that indicates SQL DB
        server_version_lower = server_version.lower()
        return "azure" in server_version_lower and "sql database" not in server_version_lower

    def _determine_feature_support(
        self, major_version: int, is_azure_sql_db: bool
    ) -> Dict[str, bool]:
        """
        Determine feature support based on version.

        Args:
            major_version: SQL Server major version number
            is_azure_sql_db: Whether this is Azure SQL Database

        Returns:
            Dictionary of feature flags
        """
        # Version mapping:
        # SQL Server 2012: 11
        # SQL Server 2014: 12
        # SQL Server 2016: 13
        # SQL Server 2017: 14
        # SQL Server 2019: 15
        # SQL Server 2022: 16

        features = {
            # SQL Server 2012+ (v11+)
            "supports_columnstore": major_version >= 11,

            # SQL Server 2014+ (v12+)
            "supports_in_memory_oltp": major_version >= 12,

            # SQL Server 2016+ (v13+)
            "supports_json": major_version >= 13,
            "supports_temporal_tables": major_version >= 13,
            "supports_row_level_security": major_version >= 13,
            "supports_always_encrypted": major_version >= 13,
            "supports_query_store": major_version >= 13,

            # SQL Server 2017+ (v14+)
            "supports_graph_database": major_version >= 14,

            # SQL Server 2019+ (v15+)
            "supports_resumable_index_ops": major_version >= 15,

            # Available in most versions
            "supports_data_compression": major_version >= 10,
        }

        # Azure SQL Database has all modern features
        if is_azure_sql_db:
            for key in features:
                features[key] = True

        return features
