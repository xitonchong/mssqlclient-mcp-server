"""Formatters for converting database results to readable formats."""

from typing import List, Dict, Any
from .models import TableInfo, TableSchemaInfo, DatabaseInfo, StoredProcedureInfo


def format_table_list(tables: List[TableInfo]) -> str:
    """Format table list as markdown table."""
    if not tables:
        return "No tables found."

    output = "Available Tables:\n\n"
    output += "Schema | Table Name | Row Count\n"
    output += "------ | ---------- | ---------\n"

    for table in tables:
        row_count = str(table.row_count) if table.row_count is not None else "N/A"
        output += f"{table.schema} | {table.name} | {row_count}\n"

    return output


def format_table_schema(schema: TableSchemaInfo) -> str:
    """Format table schema as markdown table."""
    output = f"Schema for table: {schema.table_name}\n"
    if schema.description:
        output += f"\nDescription: {schema.description}\n"

    output += "\nColumn Name | Data Type | Max Length | Is Nullable\n"
    output += "----------- | --------- | ---------- | -----------\n"

    for column in schema.columns:
        output += f"{column.name} | {column.data_type} | {column.max_length} | {column.is_nullable}\n"

    return output


def format_database_list(databases: List[DatabaseInfo]) -> str:
    """Format database list as markdown table."""
    if not databases:
        return "No databases found."

    output = "Available Databases:\n\n"
    output += "Name | State | Size (MB)\n"
    output += "---- | ----- | ---------\n"

    for db in databases:
        size = f"{db.size_mb:.2f}" if db.size_mb is not None else "N/A"
        output += f"{db.name} | {db.state} | {size}\n"

    return output


def format_stored_procedure_list(procedures: List[StoredProcedureInfo]) -> str:
    """Format stored procedure list as markdown table."""
    if not procedures:
        return "No stored procedures found."

    output = "Available Stored Procedures:\n\n"
    output += "Schema | Procedure Name | Parameters | Created\n"
    output += "------ | -------------- | ---------- | -------\n"

    for proc in procedures:
        param_count = len(proc.parameters)
        created = proc.create_date.strftime("%Y-%m-%d")
        output += f"{proc.schema_name} | {proc.name} | {param_count} | {created}\n"

    return output


def format_query_results(results: List[Dict[str, Any]], max_rows: int = 100) -> str:
    """Format query results as markdown table."""
    if not results:
        return "Query returned no results."

    # Limit results
    limited_results = results[:max_rows]
    total_rows = len(results)

    # Get column names from first row
    columns = list(limited_results[0].keys())

    # Build table
    output = "| " + " | ".join(columns) + " |\n"
    output += "| " + " | ".join(["---" for _ in columns]) + " |\n"

    for row in limited_results:
        values = [str(row.get(col, "")) for col in columns]
        # Truncate long values
        values = [v[:50] + "..." if len(v) > 50 else v for v in values]
        output += "| " + " | ".join(values) + " |\n"

    if total_rows > max_rows:
        output += f"\n(Showing first {max_rows} of {total_rows} rows)"
    else:
        output += f"\nTotal rows: {total_rows}"

    return output
