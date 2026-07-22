# Python Virtual Environment Setup & Installation Guide

**Project**: IL2CPP Multi-DB Sharded Engine  
**Required Python Version**: Python 3.10 or higher (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)  
**Author**: GarnetRapture (https://github.com/GarnetRapture)  

---

## 1. Prerequisites & Version Requirements

Ensure Python 3.10+ is installed on your system. Verify your version by running:

```bash
python --version
# or
python3 --version
```

Required version range: `Python >= 3.10.0`

---

## 2. Virtual Environment Setup

Setting up an isolated virtual environment (`.venv`) is recommended to avoid dependency conflicts.

### Windows (PowerShell / Command Prompt)

1. Open terminal in the project root directory.
2. Create virtual environment:
   ```powershell
   python -m venv .venv
   ```
3. Activate virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   # Or for CMD:
   .\.venv\Scripts\activate.bat
   ```

### Linux / macOS (Bash / Zsh)

1. Open terminal in the project root directory.
2. Create virtual environment:
   ```bash
   python3 -m venv .venv
   ```
3. Activate virtual environment:
   ```bash
   source .venv/bin/activate
   ```

---

## 3. Dependency Installation

Once the virtual environment is activated, upgrade `pip` and install all required dependencies from `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Dependency Package Overview
- `Pillow`: Image processing library used for icon conversion (`PNG` to `ICO`).
- `pyinstaller`: Binary compiler used for building standalone executable files (`cli_search.exe`).
- `sqlite3`: Standard built-in library (no external installation required).

---

## 4. Execution Workflow

### A. Database Migration (Partitioning JSON to Multi-DB)

Execute the database migration script to generate `database/*.db`:

```bash
python build_sqlite_db.py
```

### B. Running Search CLI via Python Source

```bash
python cli_search.py CameraCapturedBlurImage
```

### C. Building Standalone Windows Executable (.exe)

```powershell
pyinstaller --onefile --icon=app_icon.ico cli_search.py
```

The compiled binary will be placed inside the `dist/` directory as `dist/cli_search.exe`.

### D. Running Linux Shell Script (.sh)

```bash
chmod +x cli_search.sh
./cli_search.sh CameraCapturedBlurImage
```

---

## 5. Deactivating Virtual Environment

When finished working:

```bash
deactivate
```
