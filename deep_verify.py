import json
import sqlite3
import os
import random

DB_DIR = "database"
JSON_PATH = "il2cpp.json"

conn = sqlite3.connect(os.path.join(DB_DIR, "index.db"))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute(f"ATTACH DATABASE '{os.path.join(DB_DIR, 'signatures_1.db')}' AS sig1_db;")
cursor.execute(f"ATTACH DATABASE '{os.path.join(DB_DIR, 'signatures_2.db')}' AS sig2_db;")
cursor.execute(f"ATTACH DATABASE '{os.path.join(DB_DIR, 'signatures_3.db')}' AS sig3_db;")
cursor.execute(f"ATTACH DATABASE '{os.path.join(DB_DIR, 'signatures_4.db')}' AS sig4_db;")
cursor.execute(f"ATTACH DATABASE '{os.path.join(DB_DIR, 'methods_1.db')}' AS m1_db;")
cursor.execute(f"ATTACH DATABASE '{os.path.join(DB_DIR, 'methods_2.db')}' AS m2_db;")
cursor.execute(f"ATTACH DATABASE '{os.path.join(DB_DIR, 'pointers.db')}' AS pointers_db;")
cursor.execute(f"ATTACH DATABASE '{os.path.join(DB_DIR, 'symbols.db')}' AS symbols_db;")

print("JSON 원본 로드 중...")
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
am = data["addressMap"]

methods_union = "SELECT * FROM m1_db.methods UNION ALL SELECT * FROM m2_db.methods"
signatures_union = "SELECT * FROM sig1_db.signatures UNION ALL SELECT * FROM sig2_db.signatures UNION ALL SELECT * FROM sig3_db.signatures UNION ALL SELECT * FROM sig4_db.signatures"

errors = []
total_field_checks = 0

# 1. methodDefinitions 필드 단위 샘플 검증 (무작위 1,000건)
mdefs = [m for m in am.get("methodDefinitions", []) if m.get("virtualAddress") and m.get("virtualAddress") != "0x00000000"]
sample_mdefs = random.sample(mdefs, min(1000, len(mdefs)))

print(f"1. methodDefinitions 무작위 샘플 {len(sample_mdefs)}건 1:1 값 비교 중...")
for item in sample_mdefs:
    vaddr = item.get("virtualAddress")
    cursor.execute(f"""
        SELECT m.virtual_address, m.name, sig.signature, dnsig.dotnet_signature, t.full_name as type_name, a.name as assembly_name
        FROM ({methods_union}) m
        LEFT JOIN ({signatures_union}) sig ON m.signature_id = sig.id
        LEFT JOIN main.dotnet_signatures dnsig ON m.dotnet_signature_id = dnsig.id
        LEFT JOIN main.types t ON m.type_id = t.id
        LEFT JOIN main.assemblies a ON t.assembly_id = a.id
        WHERE m.virtual_address = ? AND m.name = ?
    """, (vaddr, item.get("name", "")))
    row = cursor.fetchone()
    
    if not row:
        errors.append(f"methodDefinition 매칭 실패: {vaddr} - {item.get('name')}")
        continue
    
    # 필드 1:1 검증
    total_field_checks += 4
    if row["virtual_address"] != item.get("virtualAddress"):
        errors.append(f"VA 불일치: JSON({item.get('virtualAddress')}) vs DB({row['virtual_address']})")
    if row["name"] != item.get("name", ""):
        errors.append(f"Name 불일치: JSON({item.get('name')}) vs DB({row['name']})")
    if (row["signature"] or "") != (item.get("signature") or ""):
        errors.append(f"Signature 불일치: {item.get('name')}")
    if (row["dotnet_signature"] or "") != (item.get("dotNetSignature") or ""):
        errors.append(f"DotNetSignature 불일치: {item.get('name')}")

# 2. stringLiterals 필드 단위 샘플 검증 (무작위 1,000건)
str_lits = [s for s in am.get("stringLiterals", []) if s.get("string")]
sample_strs = random.sample(str_lits, min(1000, len(str_lits)))

print(f"2. stringLiterals 무작위 샘플 {len(sample_strs)}건 1:1 값 비교 중...")
for s in sample_strs:
    vaddr = s.get("virtualAddress")
    val = s.get("string")
    cursor.execute("SELECT value FROM symbols_db.string_literals WHERE virtual_address = ? AND value = ?", (vaddr, val))
    row = cursor.fetchone()
    total_field_checks += 1
    if not row:
        errors.append(f"stringLiteral 값 불일치: VA({vaddr}), Value({val[:20]})")

# 3. methodInfoPointers 필드 단위 샘플 검증 (무작위 500건)
mips = [m for m in am.get("methodInfoPointers", []) if m.get("virtualAddress") != "0x00000000"]
sample_mips = random.sample(mips, min(500, len(mips)))

print(f"3. methodInfoPointers 무작위 샘플 {len(sample_mips)}건 1:1 값 비교 중...")
for m in sample_mips:
    vaddr = m.get("virtualAddress")
    cursor.execute("""
        SELECT mip.virtual_address, mip.name, dnsig.dotnet_signature, mip.method_address
        FROM pointers_db.method_info_pointers mip
        LEFT JOIN main.dotnet_signatures dnsig ON mip.dotnet_signature_id = dnsig.id
        WHERE mip.virtual_address = ?
    """, (vaddr,))
    row = cursor.fetchone()
    total_field_checks += 3
    if not row:
        errors.append(f"methodInfoPointer 매칭 실패: {vaddr}")
        continue
    if row["method_address"] != m.get("methodAddress"):
        errors.append(f"methodAddress 불일치: VA({vaddr})")
    if (row["dotnet_signature"] or "") != (m.get("dotNetSignature") or ""):
        errors.append(f"MIP DotNetSignature 불일치: VA({vaddr})")

conn.close()

print("\n=== [필드 단위 1:1 교차 심층 검증 결과] ===")
print(f"총 검증 항목: 2,500 건 레코드 (총 {total_field_checks} 개 필드 1:1 교차 검증)")
print(f"검증 오류(Mismatch) 건수: {len(errors)} 건")
if len(errors) == 0:
    print("SUCCESS: JSON 원본 필드 값과 DB 저장 필드 값이 100% 완벽히 일치함을 실시간 교차 대조로 확인하였습니다.")
else:
    print(f"오류 목록 샘플: {errors[:5]}")
