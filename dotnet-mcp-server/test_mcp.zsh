#!/usr/bin/env zsh

# Test script for MCP Server
# This sends a simple MCP initialization request

export MSSQL_CONNECTIONSTRING="Server=localhost,1433;User Id=sa;Password=Password@1234;TrustServerCertificate=True;"

cd "$(dirname "$0")/src/Core.Infrastructure.McpServer"

# Send an initialize request to the MCP server (must be on a single line)
# Keep the connection open for 2 seconds to receive the response
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'; sleep 2) | dotnet run

echo ""
echo "Test completed!"
