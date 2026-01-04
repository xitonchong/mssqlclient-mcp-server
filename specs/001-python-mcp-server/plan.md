# Implementation Plan: Python MCP Server Advanced Features

**Branch**: `001-python-mcp-server` | **Date**: 2026-01-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-python-mcp-server/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the existing Python MCP Server with advanced features for SQL Server interaction:
1. **Session Management**: Background query execution without blocking MCP responses
2. **Stored Procedure Execution**: Parameterized SP calls with type conversion
3. **SQL Server Capability Detection**: Automatic feature/version detection
4. **Advanced Table Metadata**: Indexes, foreign keys, constraints, and sizes

The Python implementation currently provides core functionality (query execution, schema discovery) but lacks these advanced capabilities present in the .NET version. This feature closes the gap while maintaining the Python implementation's simplicity.

## Technical Context

**Language/Version**: Python 3.10+ (3.10, 3.11, 3.12 supported)
**Primary Dependencies**: mcp>=1.0.0, pyodbc>=5.0.0, python-dotenv>=1.0.0, asyncio (stdlib)
**Storage**: SQL Server 2016+ (remote database, not owned by MCP server)
**Testing**: pytest with async support, pytest-asyncio
**Target Platform**: Cross-platform (macOS, Linux, Windows) - runs as MCP server process
**Project Type**: Single project (server-side MCP implementation)
**Performance Goals**:
  - Session start/status: <100ms response time
  - Capability detection: <500ms with caching
  - Metadata queries: <5s for typical databases
  - Support 10+ concurrent background sessions
**Constraints**:
  - Must not block MCP protocol responses during query execution
  - Memory-bounded session storage (no persistence across restarts)
  - Backward compatible with existing Python MCP client usage
  - Security: Execution tools disabled by default
**Scale/Scope**:
  - ~1,500 additional lines of Python code
  - 4 new MCP tools for sessions, 3 for stored procedures, 2 for capabilities, 3 for metadata
  - Extends existing 6-file codebase structure

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ NO CONSTITUTION DEFINED

The project does not have a constitution file defined (`.specify/memory/constitution.md` is a template). Therefore, no formal gates apply to this feature.

**Inferred Principles** (based on existing implementation):
1. **MCP Protocol Compliance**: All tools must follow MCP specification
2. **Security First**: Execution capabilities disabled by default, require explicit enablement
3. **Cross-Platform**: Support macOS, Linux, Windows
4. **Documentation**: All tools must be documented with examples
5. **Backward Compatibility**: New features must not break existing usage

**Assessment**: This feature aligns with all inferred principles.
- ✅ Uses MCP protocol for all new tools
- ✅ Session execution requires new env flag (`ENABLE_START_QUERY`)
- ✅ Uses standard Python libraries (asyncio) for cross-platform support
- ✅ Documentation planned for all new tools
- ✅ Extends existing codebase without breaking changes

---

**Post-Phase 1 Re-evaluation** (2026-01-03):

After completing research and design phases, the feature design continues to align with all inferred principles:

1. **MCP Protocol Compliance**: ✅ CONFIRMED
   - All 10 new tools follow MCP tool schema
   - Input/output schemas defined in `/contracts/`
   - Compatible with existing MCP client implementations

2. **Security First**: ✅ CONFIRMED
   - `start_query` and `start_stored_procedure` require explicit environment flag enablement
   - Read-only tools (capabilities, metadata) always enabled
   - No security regressions from new features

3. **Cross-Platform**: ✅ CONFIRMED
   - asyncio and ThreadPoolExecutor are stdlib (no platform-specific deps)
   - pyodbc already proven cross-platform in existing implementation
   - No OS-specific code introduced

4. **Documentation**: ✅ CONFIRMED
   - All tools documented in `contracts/` with JSON schemas
   - Quick start guide created (`quickstart.md`)
   - Complete examples provided for each feature

5. **Backward Compatibility**: ✅ CONFIRMED
   - All new code additive (extends existing modules)
   - No changes to existing tool signatures
   - Existing functionality unchanged

**Final Assessment**: ✅ **APPROVED** - Feature design passes all constitutional principles.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
python-mcp-server/
├── mssqlclient_mcp/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration management
│   ├── models.py                # Data models (existing + new session/param models)
│   ├── database_service.py      # Core DB operations + NEW: sessions, SPs, capabilities
│   ├── formatters.py            # Output formatting (existing + new metadata formatters)
│   └── server.py                # MCP server + NEW: session/SP/capability tools
│
├── tests/                       # NEW: Test suite (to be created)
│   ├── __init__.py
│   ├── test_session_manager.py
│   ├── test_stored_procedures.py
│   ├── test_capabilities.py
│   └── test_metadata.py
│
├── setup.py                     # Package setup (existing)
├── requirements.txt             # Dependencies (existing + pytest-asyncio)
├── requirements-dev.txt         # Dev dependencies (existing)
└── README.md                    # Documentation (to be updated)
```

**Structure Decision**: Single-project structure extending existing Python MCP server. All new functionality added to existing modules:
- `models.py`: Add SessionInfo, SPParameter, ServerCapability data classes
- `database_service.py`: Add SessionManager, SPExecutor, CapabilityDetector classes
- `server.py`: Register new MCP tools for sessions, stored procedures, capabilities, metadata
- `tests/`: Create new test directory (currently missing)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: N/A - No constitution violations detected.

The feature introduces reasonable complexity (async session management, type conversion) that is justified by functional requirements and aligns with inferred project principles.
