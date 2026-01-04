#!/bin/bash
export MSSQL_CONNECTIONSTRING='DRIVER={ODBC Driver 17 for SQL Server};Server=localhost,1433;Database=master;UID=sa;PWD=YourStrongPassword123\!;TrustServerCertificate=yes;'
export ENABLE_EXECUTE_QUERY=true
export ENABLE_EXECUTE_STORED_PROCEDURE=true

echo "Starting MCP server..."
.venv/bin/python -m mssqlclient_mcp.server 2>&1 &
PID=$!
sleep 2
kill $PID 2>/dev/null
wait $PID 2>/dev/null
echo -e "\n✓ Server startup test completed"
