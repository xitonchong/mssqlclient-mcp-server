# SQL Server MCP Client - Python Implementation

A Microsoft SQL Server client implementing the Model Context Protocol (MCP) in Python. This server provides SQL Server capabilities including query execution, schema discovery, and stored procedure management through the MCP interface.

## Overview

This is a Python implementation of the SQL Server MCP client, designed to be a lightweight and easy-to-use alternative to the .NET version. It provides the same core functionality for interacting with Microsoft SQL Server databases through the Model Context Protocol.

The MCP client operates in one of two modes:
- **Database Mode**: When a specific database is specified in the connection string, only operations within that database context are available
- **Server Mode**: When no database is specified in the connection string, server-wide operations across all databases are available

## How to Login into MSSQL database 
```bash
sqlcmd -S localhost,1433 -U sa -P 'YourStrongPassword123\!'   
```
once login, 
use testdb; 
go
then it will show the result after go; 



## Features

### Core Database Operations
- Execute SQL queries on connected SQL Server databases
- List all tables with schema and row count information
- Retrieve detailed schema information for specific tables
- Stored procedure management and execution

### Supported Tools

The Python implementation currently supports the following tools:

#### Common Tools (Both Modes)
- `server_capabilities` - Get SQL Server capabilities and features

#### Database Mode Tools
- `list_tables` - List all tables in the connected database
- `get_table_schema` - Get schema for a specific table
- `execute_query` - Execute a SQL query (when enabled)
- `list_stored_procedures` - List all stored procedures
- `get_stored_procedure_definition` - Get stored procedure definition

#### Server Mode Tools
- `list_databases` - List all databases on the server
- `list_tables_in_database` - List tables in a specific database
- `get_table_schema_in_database` - Get table schema from a specific database
- `execute_query_in_database` - Execute query in a specific database (when enabled)
- `list_stored_procedures_in_database` - List stored procedures in a specific database
- `get_stored_procedure_definition_in_database` - Get stored procedure definition from a specific database

## Prerequisites

- Python 3.10 or higher
- Microsoft ODBC Driver for SQL Server
  - Windows: Usually pre-installed
  - macOS: `brew install msodbcsql18`
  - Linux: Install from Microsoft's repository

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/aadversteeg/mssqlclient-mcp-server.git
   cd mssqlclient-mcp-server/python-mcp-server
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install in development mode:
   ```bash
   pip install -e .
   ```

## Configuration

### Environment Variables

Create a `.env` file in the `python-mcp-server` directory (see `.env.example`):

```bash
# Required: SQL Server connection string
MSSQL_CONNECTIONSTRING=Server=your_server;Database=your_db;User Id=your_user;Password=your_password;TrustServerCertificate=True;

# Optional: Enable execution tools (default: false)
ENABLE_EXECUTE_QUERY=true
ENABLE_EXECUTE_STORED_PROCEDURE=false
ENABLE_START_QUERY=false
ENABLE_START_STORED_PROCEDURE=false

# Optional: Timeout configuration
DEFAULT_COMMAND_TIMEOUT_SECONDS=30
CONNECTION_TIMEOUT_SECONDS=15
TOTAL_TOOL_CALL_TIMEOUT_SECONDS=120
```

### Connection String Formats

#### Database Mode (Connect to specific database)
```
Server=your_server;Database=Northwind;User Id=sa;Password=YourPassword;TrustServerCertificate=True;
```

#### Server Mode (No specific database)
```
Server=your_server;User Id=sa;Password=YourPassword;TrustServerCertificate=True;
```

## Usage

### Running the Server

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the server
python -m mssqlclient_mcp.server
```

Or if installed:

```bash
mssqlclient-mcp
```

### Using with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mssql-python": {
      "command": "python",
      "args": [
        "-m",
        "mssqlclient_mcp.server"
      ],
      "cwd": "/path/to/mssqlclient-mcp-server/python-mcp-server",
      "env": {
        "MSSQL_CONNECTIONSTRING": "Server=your_server;Database=your_db;User Id=your_user;Password=your_password;TrustServerCertificate=True;",
        "ENABLE_EXECUTE_QUERY": "true"
      }
    }
  }
}
```

Or using a virtual environment:

```json
{
  "mcpServers": {
    "mssql-python": {
      "command": "/path/to/venv/bin/python",
      "args": [
        "-m",
        "mssqlclient_mcp.server"
      ],
      "env": {
        "MSSQL_CONNECTIONSTRING": "Server=your_server;Database=your_db;User Id=your_user;Password=your_password;TrustServerCertificate=True;",
        "ENABLE_EXECUTE_QUERY": "true"
      }
    }
  }
}
```

## Security

### Tool Enablement

For security, SQL execution tools are disabled by default. Enable them explicitly:

- `ENABLE_EXECUTE_QUERY` - Enable query execution
- `ENABLE_EXECUTE_STORED_PROCEDURE` - Enable stored procedure execution
- `ENABLE_START_QUERY` - Enable background query sessions
- `ENABLE_START_STORED_PROCEDURE` - Enable background stored procedure sessions

### Best Practices

1. Use read-only database accounts when possible
2. Only enable execution tools when necessary
3. Use strong passwords
4. Enable TLS/SSL connections in production
5. Limit database permissions to necessary operations

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

### Code Formatting

```bash
# Format code
black mssqlclient_mcp/

# Lint code
ruff check mssqlclient_mcp/

# Type checking
mypy mssqlclient_mcp/
```

## Comparison with .NET Implementation

### Currently Implemented
- ✅ Database and Server mode detection
- ✅ Table listing and schema retrieval
- ✅ Query execution
- ✅ Stored procedure listing and definition retrieval
- ✅ Database listing (server mode)
- ✅ Basic configuration via environment variables

### Not Yet Implemented
- ⏳ Session-based query execution (background sessions)
- ⏳ Stored procedure execution with parameters
- ⏳ Stored procedure parameter discovery
- ⏳ SQL Server capability detection
- ⏳ Timeout management tools
- ⏳ Advanced table metadata (indexes, foreign keys, sizes)
- ⏳ Session management tools
- ⏳ Parameter type conversion and validation

### Advantages of Python Implementation
- Simpler setup and deployment
- No compilation required
- Easier to modify and extend
- Cross-platform Python ecosystem
- Lighter resource usage

### Advantages of .NET Implementation
- More comprehensive feature set
- Better type safety
- More sophisticated error handling
- Session management for long-running operations
- Advanced SQL Server feature detection

## Troubleshooting

### ODBC Driver Not Found

If you get an error about ODBC driver not being found:

**macOS:**
```bash
brew install msodbcsql18
```

**Ubuntu/Debian:**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

**Windows:**
- Download from [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### Connection Issues

1. Verify SQL Server is accessible: `telnet your_server 1433`
2. Check firewall settings
3. Ensure SQL Server allows remote connections
4. Verify credentials
5. For local SQL Server on Windows Docker, ensure TCP/IP is enabled in SQL Server Configuration Manager

## Architecture

The Python implementation follows a simplified architecture compared to the .NET version:

```
mssqlclient_mcp/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── models.py                # Data models
├── database_service.py      # Core database operations
├── formatters.py            # Output formatting
└── server.py                # MCP server implementation
```

### Key Components

- **DatabaseConfiguration**: Manages connection strings and feature flags
- **DatabaseService**: Core database operations using pyodbc
- **Formatters**: Convert database results to readable markdown tables
- **Server**: MCP protocol implementation with tool handlers

## Contributing

Contributions are welcome! Areas for improvement:

1. Implement remaining features from .NET version
2. Add comprehensive test coverage
3. Improve error handling
4. Add SQL injection protection
5. Implement connection pooling
6. Add support for Azure Active Directory authentication

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Related Projects

- [.NET Implementation](../dotnet-mcp-server/README.md) - Full-featured C# implementation
- [Model Context Protocol](https://github.com/modelcontextprotocol) - MCP specification and SDKs
