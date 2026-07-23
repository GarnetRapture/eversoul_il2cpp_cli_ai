# Eversoul IL2CPP CLI Engine v0.0.1

Enterprise-grade utility designed to parse, normalize, index, and query complex Unity IL2CPP metadata dumps (`il2cpp.json`) using a partitioned multi-database SQLite sharding architecture.

---

## Technical Overview

The IL2CPP Multi-DB Sharded Engine provides a high-performance command-line interface capable of querying type hierarchies, virtual addresses, method definitions, signatures, and cross-referenced pointers in under 0.01 seconds.

### Key Architectural Highlights

- **Interactive Console REPL Mode**: When launched without command-line search arguments (e.g. double-clicking `cli_search.exe`), the engine enters an interactive loop (`cli_search > `) allowing continuous queries without closing the terminal.
- **High-Performance Database Engine**: Utilizes SQLite's dynamic `ATTACH DATABASE` feature to cross-query 9 sub-databases concurrently in a unified relational schema.

- **SQLite Performance Tuning & PRAGMA Optimizations**: Applied `PRAGMA synchronous = OFF`, `PRAGMA journal_mode = OFF`, `PRAGMA cache_size = 20000`, and `PRAGMA temp_store = MEMORY` to maximize memory caching and eliminate disk I/O bottlenecks.
- **Hybrid Auto-Relocation & Path Compatibility**: Automatically detects whether `.db` files exist in the root folder or a `database/` subfolder. If `.db` files are found in the root executable directory, the engine automatically creates a `database/` directory, relocates all `.db` files into it, and proceeds with execution seamlessly.
- **Sharding Strategy for GitHub File Size Limits**: Automatically shards large metadata tables (`signatures` and `methods`) into balanced partitions (< 100 MB per file) to adhere strictly to version control storage constraints.
  - Partition Breakdown: `signatures_1.db` through `signatures_4.db` (4-way partition) and `methods_1.db` through `methods_2.db` (2-way partition).
- **Absolute Path Resolution**: The binary dynamically resolves database file paths relative to its execution binary location on both Windows and Unix-like operating systems.
- **Cross-Platform Support**:
  - **Windows**: Pre-compiled 64-bit standalone executable (`cli_search.exe`).
  - **Linux / macOS**: Executable shell wrapper script (`cli_search.sh`).
- **Multilingual and Structured JSON Modes**: Supports English (`en`), Korean (`ko`), and raw structured JSON formatting for external ingestion.


---

## Complete Usage Examples

### 1. Class Name Search (Windows & Linux)

Query metadata by targeted Unity C# class or assembly type name.

Windows Command Prompt / PowerShell:
```cmd
cli_search.exe CameraCapturedBlurImage
```

Linux / macOS Shell:
```bash
./cli_search.sh CameraCapturedBlurImage
```

### 2. Virtual Address (VA) Memory Pointer Query

Look up method definitions, RVA offsets, and native C++ signatures directly by 64-bit hex memory address.

```cmd
cli_search.exe 0x0417BE60
```

### 3. Display Output in Korean Language Mode

Pass the `--lang` flag to format field descriptions and titles in Korean.

```cmd
cli_search.exe NetworkManager --lang ko
```

### 4. Raw JSON Output Generation

Output results formatted as structured JSON for programmatic consumption.

```cmd
cli_search.exe NetworkManager --json
```

### 5. Executable Help and Version Query

```cmd
cli_search.exe --help
cli_search.exe --version
```

---

## Command-Line Arguments Specification

| Option / Flag | Aliases | Data Type | Description |
| :--- | :--- | :--- | :--- |
| `<query>` | `-q`, `--query` | String / Hex | Target class name, method name, signature substring, or Virtual Address (`0x...`) |
| `--lang` | `-l`, `--language` | String (`en` / `ko`) | Display language for terminal output tables (Default: `en`) |
| `--json` | `-j` | Flag | Formats search output as structured JSON |
| `--help` | `-h` | Flag | Displays full command usage reference and flag descriptions |
| `--version` | `-v` | Flag | Displays engine version specification |

---

## Database Partition Architecture

| Database File | Partition Target | Size Constraint | Purpose |
| :--- | :--- | :--- | :--- |
| `database/index.db` | Assemblies & Types | < 100 MB | Master Index containing Assembly manifests and Type definitions |
| `database/methods_1.db` | Methods (Part 1) | < 100 MB | Method definitions and constructed generic methods (Partition 1) |
| `database/methods_2.db` | Methods (Part 2) | < 100 MB | Method definitions and constructed generic methods (Partition 2) |
| `database/signatures_1.db` | Signatures (Part 1) | < 100 MB | Native C++ method signatures and parameters (Partition 1) |
| `database/signatures_2.db` | Signatures (Part 2) | < 100 MB | Native C++ method signatures and parameters (Partition 2) |
| `database/signatures_3.db` | Signatures (Part 3) | < 100 MB | Native C++ method signatures and parameters (Partition 3) |
| `database/signatures_4.db` | Signatures (Part 4) | < 100 MB | Native C++ method signatures and parameters (Partition 4) |
| `database/pointers.db` | Pointers & RVAs | < 100 MB | Metadata pointers including TypeInfo, MethodInfo, and TypeRef |
| `database/symbols.db` | Symbols & APIs | < 100 MB | String literals, symbol tables, and exported API entrypoints |

---

## Directory Setup & Asset Placement Requirement

GitHub Releases assets are downloaded individually. The engine binary (`cli_search.exe` / `cli_search.sh`) requires all `.db` files to reside in a `database/` subfolder relative to the executable path.

Required directory structure:

```
.
├── cli_search.exe                 (Windows Binary)
├── cli_search.sh                  (Linux/macOS Shell Script)
├── README.md
├── LICENSE
└── database/                      (Subfolder Required)
    ├── index.db
    ├── methods_1.db
    ├── methods_2.db
    ├── signatures_1.db
    ├── signatures_2.db
    ├── signatures_3.db
    ├── signatures_4.db
    ├── pointers.db
    └── symbols.db
```

---

## Author and License Information

- Author: GarnetRapture (https://github.com/GarnetRapture)
- License: MIT License (See `LICENSE` file for details)


