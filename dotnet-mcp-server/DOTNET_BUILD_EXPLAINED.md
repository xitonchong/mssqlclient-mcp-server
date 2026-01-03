# Understanding `dotnet build` Execution Flow

This document explains in detail what happens when you run `dotnet build` on the mssqlclient-mcp-server project, including which files are processed, in what order, and what each component does.

## Overview

When you run `dotnet build` from the root directory or `dotnet build src/mssqlclient.sln`, the .NET SDK orchestrates a complex build process that compiles all projects in the solution in the correct dependency order.

---

## Phase 1: Solution Discovery and Parsing

### Entry Point: `dotnet build` Command
**Location**: CLI command
**What triggers it**: Running `dotnet build` in terminal

### File: `src/mssqlclient.sln`
**Path**: `/src/mssqlclient.sln`
**Purpose**: Defines all projects in the solution and their configurations
**What gets parsed**:
- **Projects discovered** (lines 5-16):
  1. `Core.Infrastructure.McpServer` (Main executable) - GUID: {D63AB00C-3AD7-49A1-A1C9-C8F3D4723D7C}
  2. `UnitTests.Infrastructure.McpServer` (Tests) - GUID: {FEBF9B1F-A3E5-4AA3-AC74-3CFD233D7FCE}
  3. `Core.Infrastructure.SqlClient` (Library) - GUID: {7D1B88A4-E2B1-4C41-86FC-86C5CCE6D2E3}
  4. `Core.Application` (Library) - GUID: {2CAEB32E-061B-4524-91D8-61C19EC9CCF7}
  5. `UnitTests.Infrastructure.SqlClient` (Tests) - GUID: {1E8CA6DD-3F8A-4BDB-A2F8-34D93F2BB777}
  6. `UnitTests.Application` (Tests) - GUID: {8F9A1C2D-4E5B-6C7D-8E9F-0A1B2C3D4E5F}

- **Build configurations** (lines 20-48):
  - Debug|Any CPU
  - Release|Any CPU

---

## Phase 2: MSBuild Initialization

### Global MSBuild Files Loaded (in order)

1. **.NET SDK Directory.Build.props**
   - **Location**: `{DOTNET_SDK}/Sdks/Microsoft.NET.Sdk/Sdk/Sdk.props`
   - **Purpose**: Defines default properties for all .NET projects
   - **Sets**: Default language version, nullable reference types support, implicit usings

2. **Custom Directory.Build.props** (if exists)
   - **Location**: Searched from project directory upward to root
   - **Purpose**: Custom project-wide MSBuild properties
   - **Note**: This project doesn't have one currently

3. **NuGet Configuration**
   - **File**: `/nuget.config`
   - **Purpose**: Defines NuGet package sources
   - **What happens**: MSBuild reads this to know where to restore packages from

---

## Phase 3: Dependency Graph Resolution

MSBuild analyzes all `.csproj` files to determine build order based on `<ProjectReference>` dependencies.

### Dependency Tree Analysis:

```
Core.Application (no dependencies)
    ↓
    ├── Core.Infrastructure.SqlClient → references Core.Application
    │       ↓
    │       └── Core.Infrastructure.McpServer → references both Core.Application and Core.Infrastructure.SqlClient
    │
    └── UnitTests.Application → references Core.Application

Core.Infrastructure.SqlClient
    └── UnitTests.Infrastructure.SqlClient → references Core.Infrastructure.SqlClient

Core.Infrastructure.McpServer
    └── UnitTests.Infrastructure.McpServer → references Core.Infrastructure.McpServer
```

### Build Order Determined:
1. **Core.Application** (no dependencies - builds first)
2. **Core.Infrastructure.SqlClient** (depends on Core.Application)
3. **Core.Infrastructure.McpServer** (depends on Core.Application + Core.Infrastructure.SqlClient)
4. **UnitTests.Application** (depends on Core.Application)
5. **UnitTests.Infrastructure.SqlClient** (depends on Core.Infrastructure.SqlClient)
6. **UnitTests.Infrastructure.McpServer** (depends on Core.Infrastructure.McpServer)

---

## Phase 4: Per-Project Build Process

For each project in dependency order, MSBuild executes the following steps:

### 4.1: Core.Application Build

#### File: `src/Core.Application/Core.Application.csproj`
**Path**: `/src/Core.Application/Core.Application.csproj`

**Build Steps**:

1. **SDK Import** (line 1)
   - `<Project Sdk="Microsoft.NET.Sdk">`
   - Imports: `Microsoft.NET.Sdk/Sdk/Sdk.props` and `Sdk.targets`

2. **Property Evaluation** (lines 3-7)
   - `TargetFramework`: net9.0
   - `ImplicitUsings`: enabled (auto-imports common namespaces)
   - `Nullable`: enabled (nullable reference types)

3. **NuGet Package Restore** (lines 9-13)
   - Restores from NuGet.org (via nuget.config)
   - Packages downloaded to `~/.nuget/packages/`:
     - `Microsoft.Data.SqlClient` v6.0.2
     - `Microsoft.Extensions.Logging.Abstractions` v9.0.4
     - `Microsoft.Extensions.Options` v9.0.4

4. **Compilation**
   - **Discovers source files**: All `*.cs` files in directory
   - **Compiler**: Roslyn (csc.exe)
   - **Compilation inputs**:
     - All .cs files in `src/Core.Application/`
     - Referenced NuGet package DLLs
   - **Compilation output**:
     - `bin/Debug/net9.0/Core.Application.dll`
     - `obj/Debug/net9.0/Core.Application.pdb` (debug symbols)

5. **Target Execution**
   - CoreCompile target
   - CopyFilesToOutputDirectory target

---

### 4.2: Core.Infrastructure.SqlClient Build

#### File: `src/Core.Infrastructure.SqlClient/Core.Infrastructure.SqlClient.csproj`
**Path**: `/src/Core.Infrastructure.SqlClient/Core.Infrastructure.SqlClient.csproj`

**Build Steps**:

1. **SDK Import** (line 1)
   - Same as Core.Application

2. **Property Evaluation** (lines 3-7)
   - Same settings as Core.Application

3. **Project Reference Resolution** (lines 9-11)
   - `<ProjectReference Include="..\Core.Application\Core.Application.csproj" />`
   - **Triggers**: MSBuild ensures Core.Application is built first
   - **References**: `bin/Debug/net9.0/Core.Application.dll`

4. **NuGet Package Restore** (lines 13-19)
   - Restores additional packages:
     - `Microsoft.Data.SqlClient` v6.0.2
     - `Microsoft.Extensions.Hosting.Abstractions` v9.0.0
     - `Microsoft.Extensions.Logging.Abstractions` v9.0.4
     - `Microsoft.Extensions.Options` v9.0.4
     - `Microsoft.Extensions.DependencyInjection.Abstractions` v9.0.4

5. **Compilation**
   - **Compiler inputs**:
     - All .cs files in `src/Core.Infrastructure.SqlClient/`
     - Core.Application.dll (from project reference)
     - NuGet package DLLs
   - **Output**:
     - `bin/Debug/net9.0/Core.Infrastructure.SqlClient.dll`

---

### 4.3: Core.Infrastructure.McpServer Build (Main Executable)

#### File: `src/Core.Infrastructure.McpServer/Core.Infrastructure.McpServer.csproj`
**Path**: `/src/Core.Infrastructure.McpServer/Core.Infrastructure.McpServer.csproj`

**Build Steps**:

1. **SDK Import** (line 1)
   - Same SDK as other projects

2. **Property Evaluation** (lines 3-15)
   - `OutputType`: **Exe** (this is an executable, not a library!)
   - `TargetFramework`: net9.0
   - `ImplicitUsings`: enabled
   - `Nullable`: enabled
   - `RestorePackagesWithLockFile`: false
   - `DisableImplicitNuGetFallbackFolder`: true
   - `DockerDefaultTargetOS`: Linux
   - `AssemblyVersion`: 0.0.0
   - `FileVersion`: 0.0.0
   - `Version`: 0.0.0
   - `UserSecretsId`: 82672015-640b-4a7a-9625-5771a49fe256

3. **NuGet Package Restore** (lines 17-22)
   - Restores:
     - `Microsoft.Data.SqlClient` v6.0.2
     - `Microsoft.Extensions.Hosting` v9.0.0
     - `Microsoft.VisualStudio.Azure.Containers.Tools.Targets` v1.21.0
     - `ModelContextProtocol` v0.1.0-preview.8

4. **Project References Resolution** (lines 24-27)
   - References:
     - `Core.Application.csproj` → `Core.Application.dll`
     - `Core.Infrastructure.SqlClient.csproj` → `Core.Infrastructure.SqlClient.dll`

5. **Content Files Configuration** (lines 29-37)
   - `appsettings.json` → copied to output directory (PreserveNewest)
   - `appsettings.*.json` → copied to output directory (PreserveNewest)

6. **Compilation**
   - **Entry Point Discovery**:
     - **File**: `src/Core.Infrastructure.McpServer/Program.cs`
     - **Method**: `Program.Main(string[] args)` (line 90)
     - This is the C# entry point that gets called when the executable runs

   - **Compiler Inputs**:
     - All .cs files in `src/Core.Infrastructure.McpServer/`
     - Core.Application.dll
     - Core.Infrastructure.SqlClient.dll
     - NuGet package DLLs

   - **Compiler Output**:
     - **Executable**: `bin/Debug/net9.0/Core.Infrastructure.McpServer.dll` (on .NET, this is the executable)
     - **Runtime Config**: `bin/Debug/net9.0/Core.Infrastructure.McpServer.runtimeconfig.json`
     - **Dependencies**: `bin/Debug/net9.0/Core.Infrastructure.McpServer.deps.json`
     - **Debug Symbols**: `obj/Debug/net9.0/Core.Infrastructure.McpServer.pdb`
     - **Launcher** (macOS/Linux): `bin/Debug/net9.0/Core.Infrastructure.McpServer` (native launcher)
     - **Launcher** (Windows): `bin/Debug/net9.0/Core.Infrastructure.McpServer.exe`

7. **Post-Build Targets**:
   - Copy referenced DLLs to output directory
   - Copy appsettings.json files
   - Generate runtime configuration

---

### 4.4: Test Projects Build

The three test projects build similarly:
- **UnitTests.Application**
- **UnitTests.Infrastructure.SqlClient**
- **UnitTests.Infrastructure.McpServer**

Each follows the same pattern as the libraries, but with test framework packages.

---

## Phase 5: Global Targets Execution

After all projects compile:

1. **ResolveReferences** target
   - Resolves all assembly references
   - Copies dependencies to output directories

2. **CopyFilesToOutputDirectory** target
   - Copies all build outputs to bin/Debug/net9.0/
   - Includes DLLs, PDBs, config files

3. **GetCopyToOutputDirectoryItems** target
   - Determines which content files to copy (like appsettings.json)

4. **Build Success Reporting**
   - Generates build summary
   - Reports any warnings or errors

---

## Entry Points Summary

### Build-Time Entry Point
- **Command**: `dotnet build`
- **First file read**: `src/mssqlclient.sln`
- **MSBuild entry**: MSBuild engine processes .sln → .csproj files

### Runtime Entry Point (After Build)
When you run the compiled application:
- **Executable**: `bin/Debug/net9.0/Core.Infrastructure.McpServer` (or .exe on Windows)
- **.NET Runtime**: Loads the runtime and executes the DLL
- **Entry Method**: `Core.Infrastructure.McpServer.Program.Main(string[] args)` at line 90 of Program.cs
- **First action**: Line 92 - "Starting MCP MSSQLClient Server..."

---

## Build Artifacts Structure

After `dotnet build`, the output directory looks like:

```
src/Core.Infrastructure.McpServer/bin/Debug/net9.0/
├── Core.Infrastructure.McpServer.dll           ← Main executable assembly
├── Core.Infrastructure.McpServer.exe/launcher  ← Native launcher (platform-specific)
├── Core.Infrastructure.McpServer.runtimeconfig.json  ← Runtime configuration
├── Core.Infrastructure.McpServer.deps.json     ← Dependency manifest
├── Core.Infrastructure.McpServer.pdb           ← Debug symbols
├── Core.Application.dll                        ← Referenced project
├── Core.Infrastructure.SqlClient.dll           ← Referenced project
├── appsettings.json                            ← Configuration file
├── Microsoft.Data.SqlClient.dll                ← NuGet package
├── Microsoft.Extensions.Hosting.dll            ← NuGet package
├── ModelContextProtocol.dll                    ← NuGet package
└── [... other NuGet package DLLs ...]
```

---

## Key MSBuild Targets Executed (In Order)

For each project, these standard targets run:

1. **BeforeBuild** - Hook for custom pre-build tasks
2. **CoreCompile** - Invokes C# compiler (csc.exe/Roslyn)
3. **_CopyFilesMarkedCopyLocal** - Copies referenced assemblies
4. **_CopyOutOfDateSourceItemsToOutputDirectory** - Copies content files
5. **GetTargetPath** - Determines output path
6. **AfterBuild** - Hook for custom post-build tasks

---

## Special Behaviors in This Project

### 1. Implicit Usings (All projects)
Because `<ImplicitUsings>enable</ImplicitUsings>` is set, these namespaces are auto-imported:
- System
- System.Collections.Generic
- System.IO
- System.Linq
- System.Net.Http
- System.Threading
- System.Threading.Tasks

### 2. Nullable Reference Types (All projects)
`<Nullable>enable</Nullable>` means the compiler enforces null safety checks.

### 3. User Secrets (Core.Infrastructure.McpServer)
Line 14: `<UserSecretsId>82672015-640b-4a7a-9625-5771a49fe256</UserSecretsId>`
- Enables secure configuration storage during development
- Accessed in Program.cs lines 109-112

### 4. Configuration Files
Lines 30-36 in Core.Infrastructure.McpServer.csproj:
- `appsettings.json` and environment-specific configs are copied to output
- Used by Program.cs lines 99-107 for runtime configuration

---

## Performance Optimizations

MSBuild uses several optimizations:

1. **Incremental Build**
   - Only rebuilds projects with changed files
   - Tracked in `obj/` directory

2. **Parallel Build**
   - Projects with no dependencies build in parallel
   - Controlled by `-m` or `/maxcpucount` flag

3. **Package Caching**
   - NuGet packages cached in `~/.nuget/packages/`
   - Shared across all projects on the machine

---

## Summary: The Complete Flow

```
dotnet build command
    ↓
Parse mssqlclient.sln
    ↓
Load nuget.config
    ↓
Analyze dependency graph
    ↓
Build Core.Application
    ├─ Load Core.Application.csproj
    ├─ Import Microsoft.NET.Sdk
    ├─ Restore NuGet packages
    ├─ Compile *.cs files → Core.Application.dll
    ↓
Build Core.Infrastructure.SqlClient
    ├─ Load Core.Infrastructure.SqlClient.csproj
    ├─ Reference Core.Application.dll
    ├─ Restore NuGet packages
    ├─ Compile *.cs files → Core.Infrastructure.SqlClient.dll
    ↓
Build Core.Infrastructure.McpServer (Main Executable)
    ├─ Load Core.Infrastructure.McpServer.csproj
    ├─ Reference Core.Application.dll + Core.Infrastructure.SqlClient.dll
    ├─ Restore NuGet packages
    ├─ Compile Program.cs + other *.cs files
    ├─ Generate Core.Infrastructure.McpServer.dll (executable)
    ├─ Copy appsettings.json to output
    ├─ Copy all dependencies to bin/Debug/net9.0/
    ↓
Build test projects in parallel
    ├─ UnitTests.Application
    ├─ UnitTests.Infrastructure.SqlClient
    ├─ UnitTests.Infrastructure.McpServer
    ↓
Build complete ✓
```

When you then run: `dotnet run --project src/Core.Infrastructure.McpServer`
- .NET Runtime loads: `Core.Infrastructure.McpServer.dll`
- Executes: `Program.Main()` at Program.cs:90
- Application starts with: "Starting MCP MSSQLClient Server..." (line 92)
