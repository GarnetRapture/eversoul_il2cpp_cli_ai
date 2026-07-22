# IL2CPP Multi-DB Sharded Engine & AI Context CLI Tool

**Version**: 0.0.1  
**Author**: GarnetRapture (https://github.com/GarnetRapture)  
**License**: MIT License  

---

## Overview

The IL2CPP Multi-DB Sharded Engine is an enterprise-grade utility designed to parse, normalize, and index complex Unity IL2CPP C/JSON metadata dumps (`il2cpp.json`) into partitioned SQLite3 databases (`database/*.db`). It provides a high-performance Command Line Interface (CLI) tool (`cli_search`) capable of querying type hierarchies, virtual addresses, method definitions, signatures, and cross-referenced pointers in under 0.01 seconds while providing full context for Artificial Intelligence (AI) prompt ingestion.

---

## Key Architectural Features

### 1. GitHub Release Compliance (< 100MB Sharding)
To strictly adhere to GitHub file size limits (maximum 100MB per file), large dataset tables such as `signatures` and `methods` are sharded into balanced sub-databases:
- `signatures_1.db` through `signatures_4.db` (4-way partition)
- `methods_1.db` through `methods_2.db` (2-way partition)

### 2. Multi-Database Cross-Attach Querying
The CLI engine utilizes SQLite's `ATTACH DATABASE` capability to dynamically attach all 9 sub-databases into a unified memory space. This technique enables cross-database JOINs and UNION operations across sharded tables without sacrificing relational query integrity.

### 3. Absolute Executable-Relative Path Resolution
The executable automatically resolves the location of the `database/*.db` directory relative to its binary path, allowing execution from any directory on Windows or Linux.

### 4. Cross-Platform & Dual Execution Modes
- **Windows**: Native standalone binary (`cli_search.exe`) with embedded custom icon.
- **Linux / macOS**: Standalone Shell wrapper script (`cli_search.sh`) with fully embedded search logic.

---

## Project Structure

```
.
├── cli_search.exe                 # Standalone 64-bit Windows binary
├── cli_search.sh                  # Executable Bash script for Linux/macOS
├── cli_search.py                  # CLI Python source code
├── build_sqlite_db.py             # Database migration and sharding script
├── requirements.txt               # Project dependency package specification
├── VENV_GUIDE.md                  # Python 3.10+ Virtual Environment Setup Guide
├── GarnetRapture_Costume01_512.png # Author custom icon source
├── app_icon.ico                   # Embedded executable icon file
├── LICENSE                        # Open-source MIT License
├── README.md                      # Technical documentation
└── database/                      # Partitioned SQLite databases
    ├── index.db                   # Assemblies, Types, and DotNet Signatures Master
    ├── methods_1.db               # Sharded Methods (Partition 1, <100MB)
    ├── methods_2.db               # Sharded Methods (Partition 2, <100MB)
    ├── signatures_1.db            # Sharded Signatures (Partition 1, <100MB)
    ├── signatures_2.db            # Sharded Signatures (Partition 2, <100MB)
    ├── signatures_3.db            # Sharded Signatures (Partition 3, <100MB)
    ├── signatures_4.db            # Sharded Signatures (Partition 4, <100MB)
    ├── pointers.db                # Metadata Pointers (TypeInfo, MethodInfo, TypeRef)
    └── symbols.db                 # String Literals, Symbols, APIs, Exports
```

---

## Virtual Environment & Requirements

Refer to [VENV_GUIDE.md](VENV_GUIDE.md) for step-by-step instructions on configuring Python 3.10+ virtual environments.

Quick setup:

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## Database Partition Specifications

| Database File | Purpose | Size Constraint |
| :--- | :--- | :--- |
| `database/index.db` | Assemblies, Types, DotNet Signatures Master Index | < 100 MB |
| `database/methods_1.db` | Method Definitions & Constructed Generic Methods (Part 1) | < 100 MB |
| `database/methods_2.db` | Method Definitions & Constructed Generic Methods (Part 2) | < 100 MB |
| `database/signatures_1.db` | C++ Native Signatures (Part 1) | < 100 MB |
| `database/signatures_2.db` | C++ Native Signatures (Part 2) | < 100 MB |
| `database/signatures_3.db` | C++ Native Signatures (Part 3) | < 100 MB |
| `database/signatures_4.db` | C++ Native Signatures (Part 4) | < 100 MB |
| `database/pointers.db` | TypeInfo, TypeRef, and MethodInfo Metadata Pointers | < 100 MB |
| `database/symbols.db` | String Literals, Symbols, Fields, Field RVAs, APIs, Exports | < 100 MB |

---

## Usage Guide

### Windows (Executable)

```cmd
:: Search by Class Name
cli_search.exe CameraCapturedBlurImage

:: Search by Virtual Address (VA)
cli_search.exe 0x0417BE60

:: Output in Korean Language Mode
cli_search.exe NetworkManager --lang ko

:: Output in Raw JSON Mode
cli_search.exe NetworkManager --json

:: Display Detailed Help
cli_search.exe --help
cli_search.exe 도움말
```

### Linux / macOS (Shell Script)

Ensure execution permissions are set:

```bash
chmod +x cli_search.sh
```

Execute via script:

```bash
# Search by Class Name
./cli_search.sh CameraCapturedBlurImage

# Search by Virtual Address (VA)
./cli_search.sh 0x0417BE60

# Output in Korean Language Mode
./cli_search.sh NetworkManager --lang ko

# Output in Raw JSON Mode
./cli_search.sh NetworkManager --json

# Display Detailed Help
./cli_search.sh --help
./cli_search.sh 도움말
```

---

## Command Line Arguments Reference

| Argument / Option | Aliases | Description |
| :--- | :--- | :--- |
| `<query>` | `-q`, `--query`, `--검색어` | Target Class Name, Method Name, DotNet Signature, or Virtual Address (`0x...`) |
| `--lang <lang>` | `-l`, `--언어` | Output display language (`en` for English, `ko` for Korean). Default: `en` |
| `--json` | `-j`, `--제이슨` | Formats output as structured RAW JSON for AI prompt injection |
| `--help` | `-h`, `help`, `도움말` | Displays the interactive CLI user guide |
| `--version` | `-v`, `version`, `버전` | Outputs current engine version (`v0.0.1`) |

---

## Author & Licensing

- **Author**: GarnetRapture (https://github.com/GarnetRapture)
- **License**: MIT License (See `LICENSE` file for details)
