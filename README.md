# IL2CPP Multi-DB Sharded Engine & Multi-Domain AI Context CLI Tool

**Version**: 0.0.1  
**Author**: GarnetRapture (https://github.com/GarnetRapture)  
**License**: MIT License  

---

## Overview

The IL2CPP Multi-DB Sharded Engine is an enterprise-grade high-performance CLI utility designed to ingest, compress, and index complex Unity IL2CPP C/JSON metadata dumps, game static TBL tables, Protobuf network definitions, and JSON response schemas into a sharded SQLite3 database system (`database/*.db`).

It provides a high-speed Command Line Interface (`cli_search`) capable of resolving type hierarchies, virtual addresses, method definitions, signatures, metadata pointers, static TBL records, and Protobuf network payloads in under 0.01 seconds while generating structured RAW JSON contexts for Artificial Intelligence (AI) prompt injection.

---

## Key Architectural Features

### 1. 10-Database Sharding & GitHub Release Compliance (< 100MB Limit)
To strictly adhere to GitHub's file size limit (maximum 100MB per file) while remaining within SQLite's engine attachment limit (maximum 10 attached database slots: 1 `main` + 9 `ATTACH`), all metadata is partitioned into 10 dedicated SQLite databases:
- `signatures_1.db` ~ `signatures_3.db` (3-way sharding for C++ signatures)
- `methods_1.db` ~ `methods_2.db` (2-way sharding for method definitions)
- `symbols_tbl1.db` & `symbols_tbl2.db` (2-way sharding for Game TBL tables)
- `symbols_meta.db` (Protobuf definitions, JSON response schemas, fields, RVAs)
- `index.db` (Master index for assemblies, types, and .NET signatures)
- `pointers.db` (TypeInfo, TypeRef, and MethodInfo metadata pointers)

### 2. zlib (Level 9) Binary BLOB Compression Layer
Game static data tables (340 TBL files) are compressed using `zlib` at compression level 9 before insertion into SQLite `BLOB` columns (`content`). This optimization achieves over 80% reduction in disk storage requirements, allowing large datasets like `Talk.json` (97MB) and `StringTalk.json` (46MB) to fit into lightweight DB partitions while enabling transparent sub-millisecond runtime decompression (`zlib.decompress`).

### 3. Multi-Domain Cross-Attach Query Engine
The CLI search engine utilizes SQLite's `ATTACH DATABASE` interface to dynamically mount 9 sharded database files into a single connection memory workspace (`sig1_db` .. `sig3_db`, `m1_db`, `m2_db`, `pointers_db`, `sym_meta`, `sym_tbl1`, `sym_tbl2`). This allows seamless multi-domain cross-database queries without disk JSON file dependencies.

### 4. End-to-End `sno` Relationship Tracer
The engine provides an automated tracer for `sno` (Serial Number / Sequence Number / Static Data Unique ID):
`IL2CPP Class (VA 0x...) <---> sno Field (PK) <---> Live TBL Game Data <---> Protobuf Packet <---> Network Response Schema <---> APK Client UI Binding`

### 5. Absolute Executable-Relative Resolution & Cross-Platform Support
- **Windows**: Native 64-bit standalone executable (`cli_search.exe`).
- **Linux / macOS**: Shell wrapper script (`cli_search.sh`).
- Both executables resolve the `database/*.db` location relative to their runtime binary directory.

---

## Project Structure

```
.
├── cli_search.exe                 # Standalone 64-bit Windows binary
├── cli_search.sh                  # Executable Bash script for Linux/macOS
├── cli_search.py                  # CLI Python search engine implementation
├── build_sqlite_db.py             # SQLite database ingestion & sharding builder
├── requirements.txt               # Project dependency package specification
├── VENV_GUIDE.md                  # Python 3.10+ Virtual Environment Setup Guide
├── GarnetRapture_Costume01_512.png # Author custom icon source
├── app_icon.ico                   # Embedded executable icon file
├── LICENSE                        # Open-source MIT License
├── README.md                      # Technical documentation
└── database/                      # Partitioned SQLite databases (All < 100MB)
    ├── index.db                   # Master Index (Assemblies, Types, DotNet Signatures) (~43.75 MB)
    ├── methods_1.db               # Sharded Method Definitions Part 1 (~55.81 MB)
    ├── methods_2.db               # Sharded Method Definitions Part 2 (~87.62 MB)
    ├── signatures_1.db            # Sharded C++ Signatures Part 1 (~86.94 MB)
    ├── signatures_2.db            # Sharded C++ Signatures Part 2 (~77.69 MB)
    ├── signatures_3.db            # Sharded C++ Signatures Part 3 (~73.81 MB)
    ├── pointers.db                # Metadata Pointers (TypeInfo, MethodInfo, TypeRef) (~21.12 MB)
    ├── symbols_meta.db            # Protobufs, Response Schemas, Fields, RVAs (~21.12 MB)
    ├── symbols_tbl1.db            # Game TBL Data (Minified A-R zlib compressed) (~1.88 MB)
    └── symbols_tbl2.db            # Game TBL Data (Minified S-Z zlib compressed) (~24.00 MB)
```

---

## Database Partition Specifications

| Database File | Partition Target & Contents | Max Size | Status |
| :--- | :--- | :--- | :--- |
| `database/index.db` | Assemblies, Master Types, DotNet Signatures | < 100 MB | `PASSED` (43.75 MB) |
| `database/methods_1.db` | Method Definitions & Generic Methods (Part 1) | < 100 MB | `PASSED` (55.81 MB) |
| `database/methods_2.db` | Method Definitions & Generic Methods (Part 2) | < 100 MB | `PASSED` (87.62 MB) |
| `database/signatures_1.db` | Native C++ Signatures Shard 1 | < 100 MB | `PASSED` (86.94 MB) |
| `database/signatures_2.db` | Native C++ Signatures Shard 2 | < 100 MB | `PASSED` (77.69 MB) |
| `database/signatures_3.db` | Native C++ Signatures Shard 3 | < 100 MB | `PASSED` (73.81 MB) |
| `database/pointers.db` | TypeInfo, TypeRef, and MethodInfo Pointers | < 100 MB | `PASSED` (21.12 MB) |
| `database/symbols_meta.db` | Protobuf Definitions, Network Response Schemas | < 100 MB | `PASSED` (21.12 MB) |
| `database/symbols_tbl1.db` | Static TBL Game Data A-R (zlib compressed BLOB) | < 100 MB | `PASSED` (1.88 MB) |
| `database/symbols_tbl2.db` | Static TBL Game Data S-Z (zlib compressed BLOB) | < 100 MB | `PASSED` (24.00 MB) |

---

## Multi-Domain Integration & Data Features

The engine seamlessly unifies four distinct architectural domains into a single querying interface:

### 1. Static Game TBL Data (340 Game Tables)
- **Ingestion & Decompression**: Parses 340 game static data tables (e.g., `HeroTbl`, `ItemTbl`, `SkillTbl`, `Talk`, `StringTalk`) and stores them inside SQLite `symbols_tbl1.db` and `symbols_tbl2.db` using high-efficiency `zlib` BLOB compression.
- **Query Capabilities**: Supports searching by table name (case-insensitive wildcards) or inspecting row count and sample key structures.

### 2. Protobuf Network Definitions (486 `.proto` Definitions)
- **Ingestion**: Parses 486 Google Protobuf protocol files (`Global/**/*.proto`) and indexes message fields, enums, packet structures, and field types in `symbols_meta.db`.
- **Query Capabilities**: Enables instant lookup of request/response Protobuf message layouts, enum values, and field data types.

### 3. Network Response JSON Schemas (159 Network Schemas)
- **Ingestion**: Indexes 159 server-client API JSON response payload schemas (`schema/*.json`) within `symbols_meta.db`.
- **Query Capabilities**: Maps server response structures directly to client-side IL2CPP data models.

### 4. End-to-End `sno` Relationship & APK Integration System
- **`sno` (Serial Number / Static Data Unique ID)**: Represents the Primary Key (PK) field across Unity IL2CPP C# data tables (referenced by methods like `TblManager.GetHeroTbl(int sno)`).
- **APK Response Architecture**: Game server responses send lightweight integer `sno` identifiers in Protobuf/JSON packets instead of heavy string resources. The client APK uses `sno` to resolve localized text, icons, and hero attributes from Live TBL data tables.
- **Full Relationship Chain**:
  `IL2CPP Class (VA 0x...) <---> sno Field (PK) <---> Live TBL Game Data <---> Protobuf Packet <---> Network Response Schema <---> APK Client UI Binding`

---

## Detailed Usage Guide & Examples

### Windows Executable Examples

#### 1. Search IL2CPP Class & Virtual Addresses
```cmd
:: Search by Class Name
cli_search.exe CameraCapturedBlurImage

:: Search by Virtual Address (VA)
cli_search.exe 0x0417BE60
```

#### 2. Search Static Game TBL Tables
```cmd
:: Search Hero Data Table
cli_search.exe HeroTbl --json

:: Search Script Talk Table
cli_search.exe Talk --json
```

#### 3. Search Protobuf Packets & Network Schemas
```cmd
:: Search Hero Info Protobuf Payload
cli_search.exe sHeroInfo --json

:: Search Login Response Schema
cli_search.exe Login --json
```

#### 4. End-to-End `sno` Tracing (Static ID Search)
```cmd
:: Trace All Relationships for Hero / Item sno 1001
cli_search.exe 1001 --json
```

#### 5. Multi-Language & Formatting Options
```cmd
:: Output in Korean Language Mode
cli_search.exe NetworkManager --lang ko

:: Output in Structured RAW JSON Mode for AI Prompt Injection
cli_search.exe NetworkManager --json
```

---

## Command Line Arguments Reference

| Argument / Option | Aliases | Description |
| :--- | :--- | :--- |
| `<query>` | `-q`, `--query` | Target Class Name, Method Name, DotNet Signature, `sno` ID, TBL Name, Proto Message Name, or Virtual Address (`0x...`) |
| `--lang <lang>` | `-l` | Output display language (`en` for English, `ko` for Korean). Default: `en` |
| `--json` | `-j` | Formats output as structured RAW JSON for AI prompt injection |
| `--help` | `-h` | Displays interactive CLI user guide |
| `--version` | `-v` | Outputs engine version (`v0.0.1`) |


---

## Author & Licensing

- **Author**: GarnetRapture (https://github.com/GarnetRapture)
- **License**: MIT License (See `LICENSE` file for details)

