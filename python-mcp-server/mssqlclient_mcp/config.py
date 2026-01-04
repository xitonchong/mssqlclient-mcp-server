"""Configuration management for MSSQL MCP Server."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfiguration:
    """Configuration for database connection and operation timeouts."""

    connection_string: str
    enable_execute_query: bool = False
    enable_execute_stored_procedure: bool = False
    enable_start_query: bool = False
    enable_start_stored_procedure: bool = False
    default_command_timeout_seconds: int = 30
    connection_timeout_seconds: int = 15
    max_concurrent_sessions: int = 10
    session_cleanup_interval_minutes: int = 60
    total_tool_call_timeout_seconds: Optional[int] = 120

    @classmethod
    def from_env(cls) -> "DatabaseConfiguration":
        """Create configuration from environment variables."""
        connection_string = os.getenv("MSSQL_CONNECTIONSTRING")
        if not connection_string:
            raise ValueError(
                "MSSQL_CONNECTIONSTRING environment variable is required"
            )

        return cls(
            connection_string=connection_string,
            enable_execute_query=os.getenv("ENABLE_EXECUTE_QUERY", "false").lower() == "true",
            enable_execute_stored_procedure=os.getenv("ENABLE_EXECUTE_STORED_PROCEDURE", "false").lower() == "true",
            enable_start_query=os.getenv("ENABLE_START_QUERY", "false").lower() == "true",
            enable_start_stored_procedure=os.getenv("ENABLE_START_STORED_PROCEDURE", "false").lower() == "true",
            default_command_timeout_seconds=int(os.getenv("DEFAULT_COMMAND_TIMEOUT_SECONDS", "30")),
            connection_timeout_seconds=int(os.getenv("CONNECTION_TIMEOUT_SECONDS", "15")),
            max_concurrent_sessions=int(os.getenv("MAX_CONCURRENT_SESSIONS", "10")),
            session_cleanup_interval_minutes=int(os.getenv("SESSION_CLEANUP_INTERVAL_MINUTES", "60")),
            total_tool_call_timeout_seconds=int(timeout) if (timeout := os.getenv("TOTAL_TOOL_CALL_TIMEOUT_SECONDS")) else 120,
        )

    @staticmethod
    def is_server_mode(connection_string: str) -> bool:
        """
        Determine if the connection should use Server mode by checking if a specific
        database is specified in the connection string.

        Returns True if no database is specified (Server mode),
        False if a specific database is targeted (Database mode).
        """
        connection_string = connection_string.lower()

        # Check for Database= or Initial Catalog=
        has_database = (
            "database=" in connection_string or
            "initial catalog=" in connection_string
        )

        if not has_database:
            return True

        # Parse the database name value
        for prefix in ["database=", "initial catalog="]:
            if prefix in connection_string:
                start = connection_string.find(prefix) + len(prefix)
                end = connection_string.find(";", start)
                if end == -1:
                    end = len(connection_string)
                db_name = connection_string[start:end].strip()

                # If database name is empty or whitespace, we're in server mode
                if not db_name:
                    return True

                return False

        return True
