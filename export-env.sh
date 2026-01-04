#!/bin/bash
# Export environment variables for MSSQL MCP Server
# Add these lines to your ~/.zshrc or ~/.bashrc

# SQL Server Connection String - UPDATE WITH YOUR ACTUAL CREDENTIALS
# export MSSQL_CONNECTIONSTRING="Server=your_server;Database=your_db;User Id=your_user;Password=your_password;TrustServerCertificate=True;"
export MSSQL_CONNECTIONSTRING="DRIVER={ODBC Driver 17 for SQL Server};Server=localhost,1433;Database=TestDB;UID=sa;PWD=YourStrongPassword123\\!;TrustServerCertificate=yes;"

# Tool enablement
export ENABLE_EXECUTE_QUERY=true
export ENABLE_EXECUTE_STORED_PROCEDURE=true
export ENABLE_START_QUERY=true
export ENABLE_START_STORED_PROCEDURE=true

# Timeout configuration
export DEFAULT_COMMAND_TIMEOUT_SECONDS=30
export CONNECTION_TIMEOUT_SECONDS=15
export MAX_CONCURRENT_SESSIONS=10
export SESSION_CLEANUP_INTERVAL_MINUTES=60
export TOTAL_TOOL_CALL_TIMEOUT_SECONDS=120
