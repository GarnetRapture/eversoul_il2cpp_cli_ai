# Eversoul IL2CPP CLI Engine v0.0.1

Enterprise-grade utility designed to parse, normalize, index, compress, and query complex Unity IL2CPP metadata dumps, game static TBL tables, Protobuf network definitions, and JSON response schemas using a partitioned 10-database SQLite sharding architecture.

---

## Technical Overview

The IL2CPP Multi-DB Sharded Engine provides a high-performance command-line interface capable of querying type hierarchies, virtual addresses, method definitions, native C++ signatures, metadata pointers, static TBL records, Protobuf packets, and network response schemas in under 0.01 seconds.

### Key Architectural Highlights

- **10-Database Sharding Strategy (< 100MB Limit)**: Partitioned into exactly 10 databases to satisfy GitHub's 100MB single-file release limit while complying with SQLite's engine maximum attachment limit (1 `main` + 9 `ATTACH` slots):
  - `signatures_1.db` ~ `signatures_3.db` (3-way C++ signature sharding)
  - `methods_1.db` ~ `methods_2.db` (2-way method definitions sharding)
  - `symbols_tbl1.db` & `symbols_tbl2.db` (2-way zlib-compressed TBL game data sharding)
  - `symbols_meta.db` (Protobuf definitions, JSON response schemas, fields, RVAs)
  - `index.db` (Master index for assemblies, types, .NET signatures)
  - `pointers.db` (TypeInfo, TypeRef, MethodInfo metadata pointers)
- **zlib (Level 9) Binary BLOB Decompression Engine**: 340 game static data tables (including `Talk.json`, `StringTalk.json`, `HeroTbl`) are compressed using zlib level 9 before SQLite insertion into BLOB columns (`content`). This reduces total TBL storage by over 80% while enabling transparent sub-millisecond runtime decompression (`zlib.decompress`).
- **Multi-Domain Extended System & `sno` Relationship Tracer**: Cross-queries IL2CPP C# metadata, game static tables (`symbols_tbl1.db`, `symbols_tbl2.db`), Protobuf network definitions, and response schemas (`symbols_meta.db`). Dynamically traces the end-to-end relationship chain of `sno` (Static Data Primary Key) across C# metadata, game tables, network payloads, and APK client bindings:
  `IL2CPP Class (VA 0x...) <---> sno Field (PK) <---> Live TBL Game Data <---> Protobuf Packet <---> Network Response Schema <---> APK Client UI Binding`
- **Interactive Console REPL Mode**: When launched without command-line search arguments (e.g. double-clicking `cli_search.exe`), the engine enters an interactive loop (`cli_search > `) allowing continuous queries without closing the terminal.
- **SQLite Performance Tuning & PRAGMA Optimizations**: Applied `PRAGMA synchronous = OFF`, `PRAGMA journal_mode = OFF`, `PRAGMA page_size = 65536`, and `PRAGMA temp_store = MEMORY` to maximize memory caching and eliminate disk I/O bottlenecks.
- **Hybrid Auto-Relocation & Path Compatibility**: Automatically detects whether `.db` files exist in the root folder or a `database/` subfolder. If `.db` files are found in the root executable directory, the engine automatically creates a `database/` directory, relocates all `.db` files into it, and proceeds with execution seamlessly.
- **Absolute Path Resolution**: The binary dynamically resolves database file paths relative to its execution binary location on both Windows and Unix-like operating systems.
- **Cross-Platform Support**:
  - **Windows**: Pre-compiled 64-bit standalone executable (`cli_search.exe`).
  - **Linux / macOS**: Executable shell wrapper script (`cli_search.sh`).
- **Multilingual and Structured JSON Modes**: Supports English (`en`), Korean (`ko`), and raw structured JSON formatting for external prompt injection.

---

## Complete Usage Examples

### 1. Class Name & Memory Address Query

```cmd
:: Class Name Search
cli_search.exe CameraCapturedBlurImage

:: Virtual Address (VA) Search
cli_search.exe 0x0417BE60
```

### 2. Static Game TBL Table Search

```cmd
:: Search Hero Table Data
cli_search.exe HeroTbl --json

:: Search Talk Dialogue Table Data
cli_search.exe Talk --json
```

### 3. Protobuf & Network Schema Search

```cmd
:: Search Hero Protobuf Payload Definition
cli_search.exe sHeroInfo --json

:: Search Login Response Schema
cli_search.exe Login --json
```

### 4. End-to-End `sno` Primary Key Tracer

```cmd
:: Trace All Relationships for Hero / Item Static ID 1001
cli_search.exe 1001 --json
```

### 5. Multilingual & Formatting Options

```cmd
:: Output in Korean Language Mode
cli_search.exe NetworkManager --lang ko

:: Output in Raw JSON Mode for AI Prompt Ingestion
cli_search.exe NetworkManager --json
```

---

## Command-Line Arguments Specification

| Option / Flag | Aliases | Data Type | Description |
| :--- | :--- | :--- | :--- |
| `<query>` | `-q`, `--query` | String / Hex / Int | Target class name, method name, `sno` ID, TBL name, Proto name, or Virtual Address (`0x...`) |
| `--lang` | `-l`, `--language` | String (`en` / `ko`) | Display language for terminal output tables (Default: `en`) |
| `--json` | `-j` | Flag | Formats search output as structured JSON for AI ingestion |
| `--help` | `-h` | Flag | Displays full command usage reference and flag descriptions |
| `--version` | `-v` | Flag | Displays engine version specification |

---

## Database Partition Specifications (Measured Sizes)

| Database File | Partition Target | Size Constraint | Measured Size | Status |
| :--- | :--- | :--- | :--- | :--- |
| `database/index.db` | Assemblies, Master Types, DotNet Signatures | < 100 MB | 43.75 MB | `PASSED` |
| `database/methods_1.db` | Method Definitions & Generic Methods (Part 1) | < 100 MB | 55.81 MB | `PASSED` |
| `database/methods_2.db` | Method Definitions & Generic Methods (Part 2) | < 100 MB | 87.62 MB | `PASSED` |
| `database/signatures_1.db` | Native C++ Signatures Shard 1 | < 100 MB | 86.94 MB | `PASSED` |
| `database/signatures_2.db` | Native C++ Signatures Shard 2 | < 100 MB | 77.69 MB | `PASSED` |
| `database/signatures_3.db` | Native C++ Signatures Shard 3 | < 100 MB | 73.81 MB | `PASSED` |
| `database/pointers.db` | TypeInfo, TypeRef, and MethodInfo Pointers | < 100 MB | 21.12 MB | `PASSED` |
| `database/symbols_meta.db` | Protobuf Definitions, Network Response Schemas | < 100 MB | 21.12 MB | `PASSED` |
| `database/symbols_tbl1.db` | Static TBL Game Data A-R (zlib compressed BLOB) | < 100 MB | 1.88 MB | `PASSED` |
| `database/symbols_tbl2.db` | Static TBL Game Data S-Z (zlib compressed BLOB) | < 100 MB | 24.00 MB | `PASSED` |

---

## Directory Setup & Asset Placement Requirement

GitHub Releases assets are downloaded individually. The engine binary (`cli_search.exe` / `cli_search.sh`) requires all 10 `.db` files to reside in a `database/` subfolder relative to the executable path.

Required directory structure:

```
.
├── cli_search.exe                 (Windows Binary)
├── cli_search.sh                  (Linux/macOS Shell Script)
├── README.md
├── RELEASE_NOTES.md
├── LICENSE
└── database/                      (10 Partition Files Required)
    ├── index.db
    ├── methods_1.db
    ├── methods_2.db
    ├── signatures_1.db
    ├── signatures_2.db
    ├── signatures_3.db
    ├── pointers.db
    ├── symbols_meta.db
    ├── symbols_tbl1.db
    └── symbols_tbl2.db
```

---

## Author and License Information

- Author: GarnetRapture (https://github.com/GarnetRapture)
- License: MIT License (See `LICENSE` file for details)



