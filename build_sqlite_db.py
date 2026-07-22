import json
import sqlite3
import os
import time

DB_DIR = "database"
JSON_PATH = "il2cpp.json"

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

for fname in os.listdir(DB_DIR):
    if fname.endswith(".db"):
        os.remove(os.path.join(DB_DIR, fname))

if os.path.exists("il2cpp.db"):
    os.remove("il2cpp.db")

db_files = {
    "index": sqlite3.connect(os.path.join(DB_DIR, "index.db")),
    "sig1": sqlite3.connect(os.path.join(DB_DIR, "signatures_1.db")),
    "sig2": sqlite3.connect(os.path.join(DB_DIR, "signatures_2.db")),
    "sig3": sqlite3.connect(os.path.join(DB_DIR, "signatures_3.db")),
    "sig4": sqlite3.connect(os.path.join(DB_DIR, "signatures_4.db")),
    "m1": sqlite3.connect(os.path.join(DB_DIR, "methods_1.db")),
    "m2": sqlite3.connect(os.path.join(DB_DIR, "methods_2.db")),
    "pointers": sqlite3.connect(os.path.join(DB_DIR, "pointers.db")),
    "symbols": sqlite3.connect(os.path.join(DB_DIR, "symbols.db"))
}

for conn in db_files.values():
    conn.execute("PRAGMA page_size = 65536;")
    conn.execute("PRAGMA journal_mode = OFF;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA temp_store = MEMORY;")

db_files["index"].executescript("""
CREATE TABLE assemblies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assembly_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    FOREIGN KEY(assembly_id) REFERENCES assemblies(id)
);

CREATE TABLE dotnet_signatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dotnet_signature TEXT UNIQUE NOT NULL
);
""")

for k in ["sig1", "sig2", "sig3", "sig4"]:
    db_files[k].executescript("""
    CREATE TABLE signatures (
        id INTEGER PRIMARY KEY,
        signature TEXT UNIQUE NOT NULL
    );
    """)

for k in ["m1", "m2"]:
    db_files[k].executescript("""
    CREATE TABLE methods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        virtual_address TEXT,
        name TEXT NOT NULL,
        signature_id INTEGER,
        dotnet_signature_id INTEGER,
        type_id INTEGER,
        is_generic INTEGER DEFAULT 0
    );
    """)

db_files["pointers"].executescript("""
CREATE TABLE type_info_pointers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    type TEXT,
    dotnet_type TEXT
);

CREATE TABLE type_ref_pointers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    dotnet_type TEXT
);

CREATE TABLE method_info_pointers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    dotnet_signature_id INTEGER,
    method_address TEXT
);

CREATE TABLE method_invokers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    signature_id INTEGER
);
""")

db_files["symbols"].executescript("""
CREATE TABLE string_literals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    value TEXT NOT NULL
);

CREATE TABLE apis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    signature_id INTEGER
);

CREATE TABLE exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT
);

CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    symbol_type TEXT
);

CREATE TABLE fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    value TEXT
);

CREATE TABLE field_rvas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    virtual_address TEXT,
    name TEXT,
    value TEXT
);

CREATE TABLE function_addresses (
    func_index INTEGER PRIMARY KEY,
    virtual_address TEXT
) WITHOUT ROWID;
""")

print("Loading JSON source file...")
t0 = time.time()
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
address_map = data["addressMap"]
print(f"JSON load completed in {time.time() - t0:.2f} seconds.")

assembly_cache = {}
type_cache = {}

cur_index = db_files["index"].cursor()

def get_assembly_id(asm_name):
    if asm_name not in assembly_cache:
        cur_index.execute("INSERT INTO assemblies (name) VALUES (?) ON CONFLICT(name) DO NOTHING;", (asm_name,))
        cur_index.execute("SELECT id FROM assemblies WHERE name = ?;", (asm_name,))
        asm_id = cur_index.fetchone()[0]
        assembly_cache[asm_name] = asm_id
        return asm_id
    return assembly_cache[asm_name]

def get_type_id(group_str):
    if not group_str:
        return None
    if "/" in group_str:
        asm_name, type_name = group_str.split("/", 1)
    else:
        asm_name, type_name = "Unknown", group_str
    asm_id = get_assembly_id(asm_name)
    key = (asm_id, type_name)
    if key not in type_cache:
        cur_index.execute("INSERT INTO types (assembly_id, full_name) VALUES (?, ?);", (asm_id, type_name))
        tid = cur_index.lastrowid
        type_cache[key] = tid
        return tid
    return type_cache[key]

print("Migrating signatures into 4-way sharded DBs...")
all_sigs = set()
all_dotnet_sigs = set()

for m in address_map.get("methodDefinitions", []) + address_map.get("constructedGenericMethods", []):
    if m.get("signature"): all_sigs.add(m["signature"])
    if m.get("dotNetSignature"): all_dotnet_sigs.add(m["dotNetSignature"])

for m in address_map.get("methodInvokers", []) + address_map.get("apis", []):
    if m.get("signature"): all_sigs.add(m["signature"])

for m in address_map.get("methodInfoPointers", []):
    if m.get("dotNetSignature"): all_dotnet_sigs.add(m["dotNetSignature"])

cur_index.executemany("INSERT INTO dotnet_signatures (dotnet_signature) VALUES (?);", [(s,) for s in all_dotnet_sigs])
cur_index.execute("SELECT dotnet_signature, id FROM dotnet_signatures;")
dotnet_sig_cache = dict(cur_index.fetchall())

sorted_sigs = sorted(list(all_sigs))
q = len(sorted_sigs) // 4

sig1_rows = [(idx + 1, sig) for idx, sig in enumerate(sorted_sigs[:q])]
sig2_rows = [(q + idx + 1, sig) for idx, sig in enumerate(sorted_sigs[q:2*q])]
sig3_rows = [(2*q + idx + 1, sig) for idx, sig in enumerate(sorted_sigs[2*q:3*q])]
sig4_rows = [(3*q + idx + 1, sig) for idx, sig in enumerate(sorted_sigs[3*q:])]

db_files["sig1"].cursor().executemany("INSERT INTO signatures (id, signature) VALUES (?, ?);", sig1_rows)
db_files["sig2"].cursor().executemany("INSERT INTO signatures (id, signature) VALUES (?, ?);", sig2_rows)
db_files["sig3"].cursor().executemany("INSERT INTO signatures (id, signature) VALUES (?, ?);", sig3_rows)
db_files["sig4"].cursor().executemany("INSERT INTO signatures (id, signature) VALUES (?, ?);", sig4_rows)

sig_cache = {}
for sid, sig in sig1_rows + sig2_rows + sig3_rows + sig4_rows:
    sig_cache[sig] = sid

for k in ["index", "sig1", "sig2", "sig3", "sig4"]:
    db_files[k].commit()

print("Migrating methods into 2-way sharded DBs (methods_1.db, methods_2.db)...")
all_methods = []
for is_gen, key in [(0, "methodDefinitions"), (1, "constructedGenericMethods")]:
    for m in address_map.get(key, []):
        vaddr = m.get("virtualAddress")
        if vaddr == "0x00000000" or not vaddr:
            continue
        t_id = get_type_id(m.get("group"))
        s_id = sig_cache.get(m.get("signature"))
        dns_id = dotnet_sig_cache.get(m.get("dotNetSignature"))
        all_methods.append((vaddr, m.get("name", ""), s_id, dns_id, t_id, is_gen))

mid_half = len(all_methods) // 2
cur_m1 = db_files["m1"].cursor()
cur_m2 = db_files["m2"].cursor()

db_files["m1"].execute("BEGIN TRANSACTION;")
db_files["m2"].execute("BEGIN TRANSACTION;")

cur_m1.executemany("INSERT INTO methods (virtual_address, name, signature_id, dotnet_signature_id, type_id, is_generic) VALUES (?, ?, ?, ?, ?, ?);", all_methods[:mid_half])
cur_m2.executemany("INSERT INTO methods (virtual_address, name, signature_id, dotnet_signature_id, type_id, is_generic) VALUES (?, ?, ?, ?, ?, ?);", all_methods[mid_half:])

db_files["m1"].commit()
db_files["m2"].commit()
db_files["index"].commit()

print("Migrating pointers.db...")
cur_pointers = db_files["pointers"].cursor()
db_files["pointers"].execute("BEGIN TRANSACTION;")

tip_list = [(t.get("virtualAddress"), t.get("name"), t.get("type"), t.get("dotNetType")) for t in address_map.get("typeInfoPointers", []) if t.get("virtualAddress") != "0x00000000"]
cur_pointers.executemany("INSERT INTO type_info_pointers (virtual_address, name, type, dotnet_type) VALUES (?, ?, ?, ?);", tip_list)

trp_list = [(t.get("virtualAddress"), t.get("name"), t.get("dotNetType")) for t in address_map.get("typeRefPointers", []) if t.get("virtualAddress") != "0x00000000"]
cur_pointers.executemany("INSERT INTO type_ref_pointers (virtual_address, name, dotnet_type) VALUES (?, ?, ?);", trp_list)

mip_list = [(m.get("virtualAddress"), m.get("name"), dotnet_sig_cache.get(m.get("dotNetSignature")), m.get("methodAddress")) for m in address_map.get("methodInfoPointers", []) if m.get("virtualAddress") != "0x00000000"]
cur_pointers.executemany("INSERT INTO method_info_pointers (virtual_address, name, dotnet_signature_id, method_address) VALUES (?, ?, ?, ?);", mip_list)

mi_list = [(m.get("virtualAddress"), m.get("name"), sig_cache.get(m.get("signature"))) for m in address_map.get("methodInvokers", []) if m.get("virtualAddress") != "0x00000000"]
cur_pointers.executemany("INSERT INTO method_invokers (virtual_address, name, signature_id) VALUES (?, ?, ?);", mi_list)

db_files["pointers"].commit()

print("Migrating symbols.db...")
cur_symbols = db_files["symbols"].cursor()
db_files["symbols"].execute("BEGIN TRANSACTION;")

str_list = [(s.get("virtualAddress"), s.get("name"), s.get("string")) for s in address_map.get("stringLiterals", []) if s.get("string")]
cur_symbols.executemany("INSERT INTO string_literals (virtual_address, name, value) VALUES (?, ?, ?);", str_list)

api_list = [(a.get("virtualAddress"), a.get("name"), sig_cache.get(a.get("signature"))) for a in address_map.get("apis", [])]
cur_symbols.executemany("INSERT INTO apis (virtual_address, name, signature_id) VALUES (?, ?, ?);", api_list)

exp_list = [(e.get("virtualAddress"), e.get("name")) for e in address_map.get("exports", [])]
cur_symbols.executemany("INSERT INTO exports (virtual_address, name) VALUES (?, ?);", exp_list)

sym_list = [(s.get("virtualAddress"), s.get("name"), s.get("type")) for s in address_map.get("symbols", []) if s.get("name")]
cur_symbols.executemany("INSERT INTO symbols (virtual_address, name, symbol_type) VALUES (?, ?, ?);", sym_list)

fld_list = [(f.get("virtualAddress"), f.get("name"), f.get("value")) for f in address_map.get("fields", [])]
cur_symbols.executemany("INSERT INTO fields (virtual_address, name, value) VALUES (?, ?, ?);", fld_list)

rva_list = [(f.get("virtualAddress"), f.get("name"), f.get("value")) for f in address_map.get("fieldRvas", [])]
cur_symbols.executemany("INSERT INTO field_rvas (virtual_address, name, value) VALUES (?, ?, ?);", rva_list)

fa_list = [(idx, addr) for idx, addr in enumerate(address_map.get("functionAddresses", [])) if addr != "0x00000000"]
cur_symbols.executemany("INSERT INTO function_addresses (func_index, virtual_address) VALUES (?, ?);", fa_list)

db_files["symbols"].commit()

print("Building indexes...")
cur_index.executescript("""
CREATE INDEX idx_types_asm ON types(assembly_id);
CREATE INDEX idx_types_name ON types(full_name);
""")

for k in ["sig1", "sig2", "sig3", "sig4"]:
    db_files[k].execute("CREATE INDEX idx_sig_val ON signatures(signature);")

for k in ["m1", "m2"]:
    db_files[k].executescript("""
    CREATE INDEX idx_methods_vaddr ON methods(virtual_address);
    CREATE INDEX idx_methods_name ON methods(name);
    CREATE INDEX idx_methods_type ON methods(type_id);
    """)

cur_pointers.executescript("""
CREATE INDEX idx_type_info_name ON type_info_pointers(name);
CREATE INDEX idx_type_ref_name ON type_ref_pointers(name);
CREATE INDEX idx_method_info_vaddr ON method_info_pointers(virtual_address);
CREATE INDEX idx_method_info_maddr ON method_info_pointers(method_address);
""")

cur_symbols.executescript("""
CREATE INDEX idx_strings_vaddr ON string_literals(virtual_address);
CREATE INDEX idx_strings_val ON string_literals(value);
CREATE INDEX idx_symbols_vaddr ON symbols(virtual_address);
CREATE INDEX idx_symbols_name ON symbols(name);
""")

for conn in db_files.values():
    conn.commit()
    conn.close()

print("Executing VACUUM optimization...")
total_size = 0
all_passed = True

print("\n=== [GitHub Release < 100MB Verification Report] ===")
for fname in sorted(os.listdir(DB_DIR)):
    if fname.endswith(".db"):
        path = os.path.join(DB_DIR, fname)
        c = sqlite3.connect(path)
        c.execute("PRAGMA auto_vacuum = FULL;")
        c.execute("VACUUM;")
        c.close()
        
        sz_mb = os.path.getsize(path) / (1024 * 1024)
        total_size += sz_mb
        is_ok = sz_mb < 100
        if not is_ok: all_passed = False
        status = "PASSED (< 100MB)" if is_ok else "FAILED (>= 100MB)"
        print(f"  - database/{fname}: {sz_mb:.2f} MB | Status: {status}")

print(f"\nTotal DB Partition Size: {total_size:.2f} MB")
if all_passed:
    print("\n[SUCCESS] All SQLite DB partitions strictly comply with the GitHub Release 100MB limit.")
else:
    print("\n[FAIL] Some partitions exceeded 100MB limit.")
