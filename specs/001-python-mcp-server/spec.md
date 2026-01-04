# Feature Specification: Python MCP Server Advanced Features

**Feature**: Advanced SQL Server MCP Client Capabilities for Python Implementation
**Status**: Planning
**Created**: 2026-01-03
**Branch**: `001-python-mcp-server`

## Overview

Enhance the existing Python MCP Server implementation with advanced features to achieve feature parity with the .NET implementation. The core Python MCP server is functional with basic database operations, but lacks session management, stored procedure execution with parameters, and advanced SQL Server capabilities.

## Background

The Python MCP Server currently provides:
- ✅ Basic query execution
- ✅ Table and schema discovery
- ✅ Stored procedure listing
- ✅ Database/Server mode switching
- ✅ Security feature flags

Missing capabilities identified in README.md:
- ❌ Session-based query execution (background sessions)
- ❌ Stored procedure execution with parameters
- ❌ Stored procedure parameter discovery
- ❌ SQL Server capability detection
- ❌ Timeout management tools
- ❌ Advanced table metadata (indexes, foreign keys, sizes)
- ❌ Session management tools
- ❌ Parameter type conversion and validation

## Goals

### Primary Goals
1. **Session Management** - Enable long-running queries to execute in background sessions
2. **Stored Procedure Execution** - Support parameterized stored procedure calls with proper type conversion
3. **SQL Server Capability Detection** - Automatically detect and report server features/version
4. **Advanced Metadata** - Provide comprehensive table information including indexes, foreign keys, and sizes

### Secondary Goals
5. **Timeout Management** - Tools to manage and monitor query timeouts
6. **Parameter Discovery** - Automatic detection of stored procedure parameters
7. **Type Conversion** - Robust Python-to-SQL type mapping and validation

## Requirements

### Functional Requirements

#### FR1: Session Management
- **FR1.1**: Start query execution in a background session that doesn't block
- **FR1.2**: List all active sessions with status (running, completed, failed)
- **FR1.3**: Retrieve results from completed sessions
- **FR1.4**: Cancel running sessions
- **FR1.5**: Session timeout configuration
- **FR1.6**: Automatic session cleanup after completion

#### FR2: Stored Procedure Execution
- **FR2.1**: Discover stored procedure parameters (name, type, direction, default)
- **FR2.2**: Execute stored procedures with typed parameters
- **FR2.3**: Support INPUT, OUTPUT, and RETURN parameters
- **FR2.4**: Return multiple result sets from procedures
- **FR2.5**: Handle procedure errors and return codes

#### FR3: SQL Server Capability Detection
- **FR3.1**: Detect SQL Server version and edition
- **FR3.2**: Report supported features (JSON, temporal tables, Always Encrypted, etc.)
- **FR3.3**: Detect available system databases
- **FR3.4**: Report server-level permissions for current user
- **FR3.5**: Cache capability information per connection

#### FR4: Advanced Table Metadata
- **FR4.1**: List indexes with type, columns, and uniqueness
- **FR4.2**: Discover foreign key relationships
- **FR4.3**: Report table sizes (row count, data size, index size)
- **FR4.4**: Identify primary keys and constraints
- **FR4.5**: Show computed columns and formulas

### Non-Functional Requirements

#### NFR1: Performance
- Session operations should not block the main MCP response
- Capability detection should cache results to avoid repeated queries
- Metadata queries should complete within 5 seconds for typical databases

#### NFR2: Reliability
- Sessions must handle connection failures gracefully
- Parameter type conversion must validate before execution
- Error messages must clearly indicate the failure point

#### NFR3: Security
- Session execution tools disabled by default (like execute_query)
- Session access restricted to creating user/connection
- Parameter validation to prevent SQL injection
- Sensitive data (passwords) not logged in session management

#### NFR4: Compatibility
- Maintain compatibility with existing Python implementation
- Support SQL Server 2016+ (same as .NET version)
- Work with both Database and Server modes
- Backward compatible with existing MCP clients

### Success Criteria

1. **Session Management**: Can execute 10+ concurrent background queries without blocking
2. **Stored Procedures**: Can execute procedures with all parameter types (int, string, datetime, decimal, etc.)
3. **Capabilities**: Accurately detects server version and 10+ SQL Server features
4. **Metadata**: Provides complete schema information matching SQL Server Management Studio
5. **Tests**: 80%+ code coverage on new functionality
6. **Documentation**: All new tools documented with examples

## User Stories

### US1: Data Analyst - Long Running Queries
**As a** data analyst
**I want to** start a complex query in the background
**So that** I can continue working while it executes

**Acceptance Criteria**:
- Can start query with `start_query` tool
- Can check query status without blocking
- Can retrieve results when complete
- Can cancel if taking too long

### US2: Developer - Stored Procedure Integration
**As a** developer
**I want to** execute stored procedures with parameters
**So that** I can leverage existing database logic

**Acceptance Criteria**:
- Can discover procedure parameters automatically
- Can pass typed parameters (int, string, datetime, etc.)
- Can retrieve OUTPUT parameter values
- Can handle multiple result sets

### US3: Database Administrator - Server Assessment
**As a** database administrator
**I want to** understand SQL Server capabilities
**So that** I can recommend appropriate features

**Acceptance Criteria**:
- Reports SQL Server version and edition
- Lists supported advanced features
- Shows current user permissions
- Runs efficiently without impacting server

### US4: Data Engineer - Schema Analysis
**As a** data engineer
**I want to** see complete table metadata
**So that** I can understand data relationships and structure

**Acceptance Criteria**:
- Shows all indexes and their properties
- Displays foreign key relationships
- Reports table and index sizes
- Identifies primary keys and constraints

## Technical Approach

### Architecture Decisions

**AD1: Async Session Management**
- Use Python asyncio for non-blocking background execution
- Store session state in-memory (dictionary keyed by session ID)
- Implement session cleanup on timeout or explicit cancel

**AD2: Type Mapping Strategy**
- Create bidirectional Python ↔ SQL type mapping table
- Validate parameter types before execution
- Support common Python types: int, float, str, datetime, Decimal, bool, bytes

**AD3: Capability Caching**
- Query server capabilities on first use
- Cache per connection string
- TTL of 1 hour for capability cache

**AD4: Metadata Query Approach**
- Use SQL Server system views (sys.indexes, sys.foreign_keys, etc.)
- Batch metadata queries where possible
- Format as markdown tables for readability

### Technology Choices

- **Python 3.10+**: Required for modern async/await and type hints
- **pyodbc**: Existing SQL Server driver (no change)
- **asyncio**: Built-in async support for session management
- **typing**: Enhanced type hints for parameter validation
- **dataclasses**: For structured session/parameter metadata

### Integration Points

- Extends existing `DatabaseService` class with new methods
- Adds new MCP tools to `server.py` tool registry
- Reuses existing `DatabaseConfiguration` for new feature flags
- Maintains compatibility with existing formatters

## Out of Scope

The following are explicitly **not included** in this feature:

1. **Connection Pooling** - Will be separate feature
2. **Azure AD Authentication** - Separate authentication feature
3. **Query Result Streaming** - Performance optimization for future
4. **SQL Injection Protection** - Should be added but separate security audit
5. **Comprehensive Test Suite** - Tests will be minimal; full coverage is separate effort
6. **Query Performance Analysis** - Advanced monitoring feature for future
7. **Multi-statement Transactions** - Complex feature requiring separate design

## Dependencies

- Existing Python MCP Server implementation (already complete)
- SQL Server 2016 or higher
- Python 3.10 or higher
- pyodbc 5.0+
- mcp SDK 1.0+

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Session memory leaks | High | Medium | Implement aggressive timeout and cleanup |
| Type conversion errors | Medium | High | Comprehensive validation before execution |
| Capability detection fails | Low | Low | Fall back to minimal feature set |
| Breaking existing functionality | High | Low | Comprehensive regression testing |
| Performance degradation | Medium | Medium | Benchmark and optimize metadata queries |

## Open Questions

1. **Session Storage**: Should sessions persist across server restarts? (Answer: No, in-memory only)
2. **Parameter Defaults**: How to handle stored procedure default parameters? (Answer: Make all params required)
3. **Result Size Limits**: Should we limit session result sizes? (Answer: Use existing timeout mechanisms)
4. **Capability Cache**: Per-connection or global cache? (Answer: Per connection string)

## References

- [Python MCP Server README](../../python-mcp-server/README.md)
- [.NET Implementation](../../dotnet-mcp-server/) - Reference for feature parity
- [MCP Protocol Specification](https://github.com/modelcontextprotocol)
- [SQL Server System Views](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/)
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial specification for advanced features |
