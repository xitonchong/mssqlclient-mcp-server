# Quick Start Guide - Python MSSQL MCP Server

This guide will help you get the Python-based MSSQL MCP Server up and running quickly.

## Prerequisites

1. **Python 3.10 or higher**
   ```bash
   python --version
   ```

2. **Microsoft ODBC Driver for SQL Server**

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
   - Download from [Microsoft ODBC Driver](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

3. **Access to a SQL Server instance**

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aadversteeg/mssqlclient-mcp-server.git
   cd mssqlclient-mcp-server/python-mcp-server
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv

   # On macOS/Linux:
   source venv/bin/activate

   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file:**
   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` with your connection details:**
   ```bash
   # For Database Mode (specific database):
   MSSQL_CONNECTIONSTRING=Server=localhost;Database=Northwind;User Id=sa;Password=YourPassword;TrustServerCertificate=True;

   # Enable query execution:
   ENABLE_EXECUTE_QUERY=true
   ```

## Running the Server

### Standalone Mode

```bash
python -m mssqlclient_mcp.server
```

The server will:
- Load configuration from `.env`
- Detect Server or Database mode from the connection string
- Start listening for MCP protocol messages on stdin/stdout

### Docker Mode

1. **Build the Docker image:**
   ```bash
   docker build -t mssqlclient-mcp-python:latest .
   ```

2. **Run with Docker:**
   ```bash
   docker run -i \
     -e "MSSQL_CONNECTIONSTRING=Server=your_server;Database=your_db;User Id=sa;Password=YourPassword;TrustServerCertificate=True;" \
     -e "ENABLE_EXECUTE_QUERY=true" \
     mssqlclient-mcp-python:latest
   ```

3. **Or use docker-compose:**
   ```bash
   # Set environment variables in .env
   docker-compose up
   ```

## Configuring with Claude Desktop

### Option 1: Using Virtual Environment

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent location:

```json
{
  "mcpServers": {
    "mssql-python": {
      "command": "/full/path/to/venv/bin/python",
      "args": [
        "-m",
        "mssqlclient_mcp.server"
      ],
      "env": {
        "MSSQL_CONNECTIONSTRING": "Server=localhost;Database=Northwind;User Id=sa;Password=YourPassword;TrustServerCertificate=True;",
        "ENABLE_EXECUTE_QUERY": "true"
      }
    }
  }
}
```

### Option 2: Using Docker

```json
{
  "mcpServers": {
    "mssql-python": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "MSSQL_CONNECTIONSTRING=Server=localhost;Database=Northwind;User Id=sa;Password=YourPassword;TrustServerCertificate=True;",
        "-e", "ENABLE_EXECUTE_QUERY=true",
        "mssqlclient-mcp-python:latest"
      ]
    }
  }
}
```

### Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the new MCP server.

## Testing the Connection

Once configured, you can test in Claude Desktop by asking:

```
Can you list the tables in the database?
```

Or:

```
Show me the schema for the Customers table
```

If query execution is enabled:

```
Execute a query to get the top 5 customers
```

## Example Queries

### Database Mode Examples

```
# List all tables
"List all the tables in the database"

# Get table schema
"Show me the schema for the Orders table"

# Execute a query (if enabled)
"Run a query: SELECT TOP 10 * FROM Customers"

# List stored procedures
"What stored procedures are available?"

# Get stored procedure definition
"Show me the definition of the GetCustomerOrders procedure"
```

### Server Mode Examples

```
# List all databases
"What databases are on this server?"

# List tables in a specific database
"List all tables in the Northwind database"

# Get table schema from specific database
"Show me the schema for the Products table in the Northwind database"

# Execute query in specific database (if enabled)
"Execute this query in the Northwind database: SELECT * FROM Categories"
```

## Troubleshooting

### Connection Fails

1. **Verify SQL Server is running:**
   ```bash
   telnet your_server 1433
   ```

2. **Check connection string syntax**

3. **Verify credentials**

4. **Ensure firewall allows connection**

### ODBC Driver Issues

If you get "Data source name not found":

1. **Check installed drivers:**
   ```bash
   # macOS/Linux
   odbcinst -j

   # List drivers
   odbcinst -q -d
   ```

2. **Reinstall ODBC driver** (see Prerequisites)

### Import Errors

If you get module import errors:

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### MCP Server Not Loading in Claude

1. **Check Claude Desktop logs:**
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

2. **Verify configuration file syntax** (must be valid JSON)

3. **Test server manually:**
   ```bash
   python -m mssqlclient_mcp.server
   ```

4. **Check environment variables are set correctly**

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the [.NET implementation](../dotnet-mcp-server/README.md) for more advanced features
- Check out the [Model Context Protocol documentation](https://github.com/modelcontextprotocol)

## Security Reminders

1. Never commit `.env` files with credentials
2. Use strong passwords
3. Consider using SQL Server authentication with least privileges
4. Only enable query execution when necessary
5. Use read-only accounts when possible

## Getting Help

- File issues on [GitHub](https://github.com/aadversteeg/mssqlclient-mcp-server/issues)
- Check existing issues for solutions
- Review the full README.md for more details
