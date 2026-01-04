"""Type mapping utilities for converting Python types to SQL Server types."""

from decimal import Decimal
from datetime import datetime, date, time
from typing import Any, Optional
import uuid


# Type mapping: Python type -> Compatible SQL Server types
TYPE_MAPPING = {
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
    type(None): [],  # NULL compatible with any nullable type
}


def convert_python_to_sql(
    value: Any,
    sql_type: str,
    max_length: int = -1,
    precision: int = 0,
    scale: int = 0
) -> Any:
    """
    Convert a Python value to SQL Server compatible type.

    Args:
        value: The Python value to convert
        sql_type: Target SQL Server type name
        max_length: Maximum length for string/binary types
        precision: Precision for decimal/numeric types
        scale: Scale for decimal/numeric types

    Returns:
        Converted value suitable for SQL Server

    Raises:
        ValueError: If conversion fails or violates constraints
        TypeError: If type is incompatible
    """
    if value is None:
        return None

    sql_type_lower = sql_type.lower()

    # String types
    if sql_type_lower in ('varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext'):
        s = str(value)
        if max_length > 0 and len(s) > max_length:
            raise ValueError(
                f"String length {len(s)} exceeds maximum {max_length} "
                f"for type {sql_type}"
            )
        return s

    # Integer types
    elif sql_type_lower in ('int', 'bigint', 'smallint', 'tinyint'):
        if not isinstance(value, (int, bool)):
            try:
                return int(value)
            except (ValueError, TypeError) as e:
                raise TypeError(
                    f"Cannot convert {type(value).__name__} to {sql_type}: {e}"
                )
        return int(value)

    # Decimal/Numeric types
    elif sql_type_lower in ('decimal', 'numeric', 'money', 'smallmoney'):
        if isinstance(value, (int, float, str)):
            try:
                return Decimal(str(value))
            except (ValueError, TypeError) as e:
                raise TypeError(
                    f"Cannot convert {type(value).__name__} to {sql_type}: {e}"
                )
        elif isinstance(value, Decimal):
            return value
        else:
            raise TypeError(
                f"Cannot convert {type(value).__name__} to {sql_type}"
            )

    # Float types
    elif sql_type_lower in ('float', 'real'):
        if not isinstance(value, (int, float)):
            try:
                return float(value)
            except (ValueError, TypeError) as e:
                raise TypeError(
                    f"Cannot convert {type(value).__name__} to {sql_type}: {e}"
                )
        return float(value)

    # Datetime types
    elif sql_type_lower in ('datetime', 'datetime2', 'smalldatetime'):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError as e:
                raise TypeError(
                    f"Cannot parse datetime from string '{value}': {e}"
                )
        elif isinstance(value, datetime):
            return value
        else:
            raise TypeError(
                f"Cannot convert {type(value).__name__} to {sql_type}"
            )

    # Date type
    elif sql_type_lower == 'date':
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except ValueError as e:
                raise TypeError(
                    f"Cannot parse date from string '{value}': {e}"
                )
        elif isinstance(value, datetime):
            return value.date()
        elif isinstance(value, date):
            return value
        else:
            raise TypeError(
                f"Cannot convert {type(value).__name__} to date"
            )

    # Time type
    elif sql_type_lower == 'time':
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(f"2000-01-01T{value}").time()
            except ValueError as e:
                raise TypeError(
                    f"Cannot parse time from string '{value}': {e}"
                )
        elif isinstance(value, datetime):
            return value.time()
        elif isinstance(value, time):
            return value
        else:
            raise TypeError(
                f"Cannot convert {type(value).__name__} to time"
            )

    # Boolean/Bit
    elif sql_type_lower == 'bit':
        return 1 if value else 0

    # UUID/uniqueidentifier
    elif sql_type_lower == 'uniqueidentifier':
        if isinstance(value, str):
            try:
                return str(uuid.UUID(value))  # Validate UUID format
            except ValueError as e:
                raise TypeError(
                    f"Invalid UUID string '{value}': {e}"
                )
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            raise TypeError(
                f"Cannot convert {type(value).__name__} to uniqueidentifier"
            )

    # Binary types
    elif sql_type_lower in ('binary', 'varbinary', 'image'):
        if isinstance(value, bytes):
            if max_length > 0 and len(value) > max_length:
                raise ValueError(
                    f"Binary length {len(value)} exceeds maximum {max_length}"
                )
            return value
        elif isinstance(value, str):
            # Try to encode string as UTF-8 bytes
            encoded = bytes(value, 'utf-8')
            if max_length > 0 and len(encoded) > max_length:
                raise ValueError(
                    f"Binary length {len(encoded)} exceeds maximum {max_length}"
                )
            return encoded
        else:
            raise TypeError(
                f"Cannot convert {type(value).__name__} to {sql_type}"
            )

    # Default: pass through
    return value


def validate_parameter(
    param_name: str,
    value: Any,
    sql_type: str,
    is_nullable: bool = True,
    has_default: bool = False
) -> None:
    """
    Validate that a parameter value is compatible with its SQL type.

    Args:
        param_name: Parameter name (for error messages)
        value: The value to validate
        sql_type: Target SQL Server type
        is_nullable: Whether NULL is allowed
        has_default: Whether parameter has a default value

    Raises:
        ValueError: If validation fails
    """
    # Check NULL constraint
    if value is None:
        if not is_nullable and not has_default:
            raise ValueError(
                f"Parameter '{param_name}' cannot be NULL (not nullable and no default)"
            )
        return  # NULL is valid

    # Check type compatibility
    value_type = type(value)
    sql_type_lower = sql_type.lower()

    compatible = False
    for python_type, sql_types in TYPE_MAPPING.items():
        if isinstance(value, python_type):
            if sql_type_lower in sql_types:
                compatible = True
                break

    if not compatible:
        raise ValueError(
            f"Parameter '{param_name}': Type {value_type.__name__} is not compatible "
            f"with SQL type {sql_type}"
        )


def convert_parameters_for_execution(
    parameters: dict[str, Any],
    param_metadata: list
) -> list[Any]:
    """
    Convert dictionary of parameters to list of SQL-compatible values.

    Args:
        parameters: Dict of parameter names -> values
        param_metadata: List of StoredProcedureParameter objects with metadata

    Returns:
        List of converted parameter values in correct order

    Raises:
        ValueError: If required parameter missing or conversion fails
    """
    converted = []

    for meta in param_metadata:
        param_name = meta.parameter_name

        # Check if parameter provided
        if param_name not in parameters:
            if meta.is_required():
                raise ValueError(
                    f"Required parameter '{param_name}' not provided"
                )
            # Use default or None for optional parameters
            converted.append(None)
            continue

        value = parameters[param_name]

        # Validate
        validate_parameter(
            param_name,
            value,
            meta.data_type,
            meta.is_nullable,
            meta.has_default_value
        )

        # Convert
        converted_value = convert_python_to_sql(
            value,
            meta.data_type,
            meta.max_length,
            meta.precision,
            meta.scale
        )
        converted.append(converted_value)

    return converted
