# Multi-stage build for Python MSSQL MCP Server
FROM python:3.12-slim AS base

# Install ODBC Driver for SQL Server
RUN apt-get update && \
    apt-get install -y curl gnupg2 && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mssqlclient_mcp/ ./mssqlclient_mcp/
COPY setup.py pyproject.toml ./

# Install the package
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MSSQL_CONNECTIONSTRING=""

# Run the server
ENTRYPOINT ["python", "-m", "mssqlclient_mcp.server"]
