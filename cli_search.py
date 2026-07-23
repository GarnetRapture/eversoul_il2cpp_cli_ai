import sqlite3
import sys
import json
import os
import argparse
import shutil

AUTHOR_URL = "https://github.com/GarnetRapture"
VERSION = "0.0.1"

class Colors:
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

def init_console():
    if os.name == 'nt':
        os.system('')
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

def get_base_dir():
    candidates = []
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(exe_dir)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(script_dir)
    candidates.append(os.getcwd())

    # 1. Check if database/index.db already exists
    for base in candidates:
        db_dir = os.path.join(base, "database")
        if os.path.exists(os.path.join(db_dir, "index.db")):
            return db_dir

    # 2. Hybrid Auto-Relocation: Check if *.db files exist in root/same directory
    for base in candidates:
        root_index = os.path.join(base, "index.db")
        if os.path.exists(root_index):
            db_dir = os.path.join(base, "database")
            os.makedirs(db_dir, exist_ok=True)
            for item in os.listdir(base):
                if item.endswith(".db") and os.path.isfile(os.path.join(base, item)):
                    src = os.path.join(base, item)
                    dst = os.path.join(db_dir, item)
                    try:
                        shutil.move(src, dst)
                    except Exception:
                        pass
            if os.path.exists(os.path.join(db_dir, "index.db")):
                return db_dir

    return os.path.join(candidates[0], "database")

DB_DIR = get_base_dir()

def get_db_connection():
    index_path = os.path.join(DB_DIR, "index.db")
    if not os.path.exists(index_path):
        print(f"{Colors.RED}{Colors.BOLD}[ERROR / 오류] Database directory not found! / 데이터베이스 디렉터리를 찾을 수 없습니다.{Colors.RESET}")
        print(f"{Colors.YELLOW}Expected path / 예상 경로: {index_path}{Colors.RESET}")
        print(f"{Colors.WHITE}Please ensure 'database/*.db' directory is placed in the SAME folder as the executable.{Colors.RESET}")
        print(f"{Colors.WHITE}실행 파일과 동일한 경로에 'database/*.db' 폴더가 존재하는지 확인하십시오.{Colors.RESET}")
        sys.exit(1)

    conn = sqlite3.connect(index_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA journal_mode = OFF;")
    cursor.execute("PRAGMA cache_size = 20000;")
    cursor.execute("PRAGMA temp_store = MEMORY;")

    db_names = [
        ("signatures_1.db", "sig1_db"),
        ("signatures_2.db", "sig2_db"),
        ("signatures_3.db", "sig3_db"),
        ("signatures_4.db", "sig4_db"),
        ("methods_1.db", "m1_db"),
        ("methods_2.db", "m2_db"),
        ("pointers.db", "pointers_db"),
        ("symbols.db", "symbols_db")
    ]

    for filename, alias in db_names:
        p = os.path.join(DB_DIR, filename)
        if not os.path.exists(p):
            print(f"{Colors.RED}[ERROR / 오류] Missing partition database / 분할 데이터베이스 누락: {p}{Colors.RESET}")
            sys.exit(1)
        cursor.execute(f"ATTACH DATABASE '{p}' AS {alias};")

    return conn, cursor


def search_context(query_str, max_results=5):
    conn, cursor = get_db_connection()

    query_clean = query_str.strip()
    is_address = query_clean.startswith("0x") or query_clean.startswith("0X")

    methods_union = """
        SELECT * FROM m1_db.methods
        UNION ALL
        SELECT * FROM m2_db.methods
    """
    signatures_union = """
        SELECT * FROM sig1_db.signatures
        UNION ALL
        SELECT * FROM sig2_db.signatures
        UNION ALL
        SELECT * FROM sig3_db.signatures
        UNION ALL
        SELECT * FROM sig4_db.signatures
    """

    if is_address:
        cursor.execute(f"""
            SELECT m.virtual_address, m.name, sig.signature, dnsig.dotnet_signature, m.is_generic, m.type_id,
                   t.full_name as type_name, a.name as assembly_name
            FROM ({methods_union}) m
            LEFT JOIN ({signatures_union}) sig ON m.signature_id = sig.id
            LEFT JOIN main.dotnet_signatures dnsig ON m.dotnet_signature_id = dnsig.id
            LEFT JOIN main.types t ON m.type_id = t.id
            LEFT JOIN main.assemblies a ON t.assembly_id = a.id
            WHERE m.virtual_address = ?
        """, (query_clean,))
    else:
        cursor.execute(f"""
            SELECT m.virtual_address, m.name, sig.signature, dnsig.dotnet_signature, m.is_generic, m.type_id,
                   t.full_name as type_name, a.name as assembly_name
            FROM ({methods_union}) m
            LEFT JOIN ({signatures_union}) sig ON m.signature_id = sig.id
            LEFT JOIN main.dotnet_signatures dnsig ON m.dotnet_signature_id = dnsig.id
            LEFT JOIN main.types t ON m.type_id = t.id
            LEFT JOIN main.assemblies a ON t.assembly_id = a.id
            WHERE m.name LIKE ? OR dnsig.dotnet_signature LIKE ? OR t.full_name LIKE ?
            LIMIT ?
        """, (f"%{query_clean}%", f"%{query_clean}%", f"%{query_clean}%", max_results))

    methods_matched = cursor.fetchall()
    target_type_ids = set()
    for m in methods_matched:
        if m["type_id"]:
            target_type_ids.add(m["type_id"])

    if not target_type_ids and not is_address:
        cursor.execute("SELECT id FROM main.types WHERE full_name LIKE ? LIMIT ?", (f"%{query_clean}%", max_results))
        for r in cursor.fetchall():
            target_type_ids.add(r["id"])

    type_contexts = []

    for tid in target_type_ids:
        cursor.execute("""
            SELECT t.id, t.full_name, a.name as assembly_name
            FROM main.types t
            JOIN main.assemblies a ON t.assembly_id = a.id
            WHERE t.id = ?
        """, (tid,))
        type_info = cursor.fetchone()
        if not type_info:
            continue

        cursor.execute(f"""
            SELECT m.virtual_address, m.name, sig.signature, dnsig.dotnet_signature, m.is_generic
            FROM ({methods_union}) m
            LEFT JOIN ({signatures_union}) sig ON m.signature_id = sig.id
            LEFT JOIN main.dotnet_signatures dnsig ON m.dotnet_signature_id = dnsig.id
            WHERE m.type_id = ?
            ORDER BY m.virtual_address
        """, (tid,))
        all_type_methods = [dict(r) for r in cursor.fetchall()]

        method_addrs = [m["virtual_address"] for m in all_type_methods if m["virtual_address"]]
        method_info_pointers = []
        if method_addrs:
            placeholders = ",".join(["?"] * len(method_addrs))
            cursor.execute(f"""
                SELECT mip.virtual_address, mip.name, dnsig.dotnet_signature, mip.method_address
                FROM pointers_db.method_info_pointers mip
                LEFT JOIN main.dotnet_signatures dnsig ON mip.dotnet_signature_id = dnsig.id
                WHERE mip.method_address IN ({placeholders})
            """, method_addrs)
            method_info_pointers = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT virtual_address, name, type, dotnet_type FROM pointers_db.type_info_pointers WHERE name LIKE ?", (f"%{type_info['full_name']}%",))
        type_infos = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT virtual_address, name, dotnet_type FROM pointers_db.type_ref_pointers WHERE name LIKE ?", (f"%{type_info['full_name']}%",))
        type_refs = [dict(r) for r in cursor.fetchall()]

        type_contexts.append({
            "type_id": type_info["id"],
            "full_name": type_info["full_name"],
            "assembly": type_info["assembly_name"],
            "method_count": len(all_type_methods),
            "methods": all_type_methods,
            "method_info_pointers": method_info_pointers,
            "type_info_pointers": type_infos,
            "type_ref_pointers": type_refs
        })

    additional_context = {}
    if is_address:
        cursor.execute("SELECT * FROM symbols_db.string_literals WHERE virtual_address = ?", (query_clean,))
        str_lits = [dict(r) for r in cursor.fetchall()]
        if str_lits: additional_context["string_literals"] = str_lits

        cursor.execute("""
            SELECT mip.virtual_address, mip.name, dnsig.dotnet_signature, mip.method_address
            FROM pointers_db.method_info_pointers mip
            LEFT JOIN main.dotnet_signatures dnsig ON mip.dotnet_signature_id = dnsig.id
            WHERE mip.virtual_address = ? OR mip.method_address = ?
        """, (query_clean, query_clean))
        mips = [dict(r) for r in cursor.fetchall()]
        if mips: additional_context["method_info_pointers"] = mips

        cursor.execute(f"""
            SELECT mi.virtual_address, mi.name, sig.signature
            FROM pointers_db.method_invokers mi
            LEFT JOIN ({signatures_union}) sig ON mi.signature_id = sig.id
            WHERE mi.virtual_address = ?
        """, (query_clean,))
        invs = [dict(r) for r in cursor.fetchall()]
        if invs: additional_context["method_invokers"] = invs

        cursor.execute(f"""
            SELECT a.virtual_address, a.name, sig.signature
            FROM symbols_db.apis a
            LEFT JOIN ({signatures_union}) sig ON a.signature_id = sig.id
            WHERE a.virtual_address = ?
        """, (query_clean,))
        apis = [dict(r) for r in cursor.fetchall()]
        if apis: additional_context["apis"] = apis

        cursor.execute("SELECT * FROM symbols_db.exports WHERE virtual_address = ?", (query_clean,))
        exps = [dict(r) for r in cursor.fetchall()]
        if exps: additional_context["exports"] = exps

        cursor.execute("SELECT * FROM symbols_db.symbols WHERE virtual_address = ?", (query_clean,))
        syms = [dict(r) for r in cursor.fetchall()]
        if syms: additional_context["symbols"] = syms

        cursor.execute("SELECT * FROM symbols_db.fields WHERE virtual_address = ?", (query_clean,))
        flds = [dict(r) for r in cursor.fetchall()]
        if flds: additional_context["fields"] = flds
    else:
        cursor.execute("SELECT * FROM symbols_db.string_literals WHERE value LIKE ? LIMIT 5", (f"%{query_clean}%",))
        str_lits = [dict(r) for r in cursor.fetchall()]
        if str_lits: additional_context["matched_string_literals"] = str_lits

        cursor.execute("SELECT * FROM symbols_db.symbols WHERE name LIKE ? LIMIT 5", (f"%{query_clean}%",))
        syms = [dict(r) for r in cursor.fetchall()]
        if syms: additional_context["matched_symbols"] = syms

    conn.close()

    full_ai_context = {
        "author": AUTHOR_URL,
        "version": VERSION,
        "query": query_str,
        "matched_types_count": len(type_contexts),
        "types_context": type_contexts,
        "additional_matched_context": additional_context
    }
    return full_ai_context

def print_banner(lang="en"):
    banner = r"""
  ___ _    ___  ___ ___    ___ ___  _  _ _____ _____  _____ 
 |_ _| |  |_  )/ __| _ \  / __/ _ \| \| |_   _| __\ \/ /_ _|
  | || |__ / /| (__|  _/ | (_| (_) | .` | | | | _| >  < | | 
 |___|____/___|\___|_|    \___\___/|_|\_| |_| |___/_/\_\___|
"""
    print(f"{Colors.MAGENTA}{Colors.BOLD}{banner}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  * IL2CPP AI Context Engine v{VERSION} (Multi-DB Sharded Edition) *{Colors.RESET}")
    print(f"{Colors.WHITE}  Author / 제작자: {Colors.GREEN}{AUTHOR_URL}{Colors.RESET}")
    print(f"{Colors.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")

def print_detailed_help(lang="en"):
    print_banner(lang)

    if lang == "ko":
        print(f"{Colors.YELLOW}{Colors.BOLD}=================== [ IL2CPP CLI 엔진 상세 사용 가이드 ] ==================={Colors.RESET}\n")
        print(f"{Colors.CYAN}{Colors.BOLD}* 기본 사용법 (Usage):{Colors.RESET}")
        print(f"   cli_search <검색어_또는_주소> [옵션...]\n")

        print(f"{Colors.CYAN}{Colors.BOLD}* 명령어 및 인자 옵션 (Arguments & Options):{Colors.RESET}")
        print(f"   {Colors.GREEN}<검색어 / query / -q>{Colors.RESET}   : 클래스명, 메서드명, .NET 시그니처 또는 가상주소(0x...)")
        print(f"   {Colors.GREEN}--lang / -l / --언어 <ko|en>{Colors.RESET}: 출력 언어 설정 (한국어: ko, 영어: en)")
        print(f"   {Colors.GREEN}--json / -j / --제이슨{Colors.RESET}      : AI LLM 주입용 구조화 RAW JSON 객체 출력")
        print(f"   {Colors.GREEN}--help / -h / 도움말{Colors.RESET}        : 본 상세 가이드 화면 출력")
        print(f"   {Colors.GREEN}--version / -v / 버전{Colors.RESET}       : 엔진 버전 정보 출력 (현재: v{VERSION})\n")

        print(f"{Colors.CYAN}{Colors.BOLD}* 명령어 실행 예시 (Examples):{Colors.RESET}")
        print(f"   {Colors.WHITE}1. 클래스명 검색 (한국어 모드):{Colors.RESET}")
        print(f"      cli_search CameraCapturedBlurImage --lang ko")
        print(f"   {Colors.WHITE}2. 가상 주소 검색:{Colors.RESET}")
        print(f"      cli_search 0x0417BE60")
        print(f"   {Colors.WHITE}3. 한국어 커맨드 인자 사용:{Colors.RESET}")
        print(f"      cli_search --검색어 NetworkManager --언어 ko")
        print(f"   {Colors.WHITE}4. AI 주입용 JSON 형식 출력:{Colors.RESET}")
        print(f"      cli_search NetworkManager --json\n")

        print(f"{Colors.CYAN}{Colors.BOLD}* 데이터베이스 파티셔닝 구조 (Database Infra):{Colors.RESET}")
        print(f"   실행 파일과 동일한 경로의 {Colors.YELLOW}database/*.db{Colors.RESET} 폴더를 자동 참조합니다.")
        print(f"   - index.db        : 어셈블리 / 타입 정의 마스터")
        print(f"   - methods_1~2.db  : 메서드 정의 2분할 샤딩 (<100MB)")
        print(f"   - signatures_1~4.db: C++ 시그니처 4분할 샤딩 (<100MB)")
        print(f"   - pointers.db     : TypeInfo / MethodInfo 메타포인터")
        print(f"   - symbols.db      : 문자열, 심볼, API, Export 참조\n")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}=================== [ IL2CPP CLI ENGINE DETAILED GUIDE ] ==================={Colors.RESET}\n")
        print(f"{Colors.CYAN}{Colors.BOLD}* BASIC USAGE:{Colors.RESET}")
        print(f"   cli_search <Query_Keyword_or_Address> [Options...]\n")

        print(f"{Colors.CYAN}{Colors.BOLD}* ARGUMENTS & OPTIONS:{Colors.RESET}")
        print(f"   {Colors.GREEN}<query / -q / --query>{Colors.RESET}     : Class Name, Method Name, DotNet Signature, or VA (0x...)")
        print(f"   {Colors.GREEN}--lang / -l <en|ko>{Colors.RESET}         : Output Language (English: en, Korean: ko)")
        print(f"   {Colors.GREEN}--json / -j{Colors.RESET}                 : Output in structured RAW JSON for AI Prompt Injection")
        print(f"   {Colors.GREEN}--help / -h{Colors.RESET}                 : Show this detailed user guide")
        print(f"   {Colors.GREEN}--version / -v{Colors.RESET}              : Show engine version (Current: v{VERSION})\n")

        print(f"{Colors.CYAN}{Colors.BOLD}* EXAMPLES:{Colors.RESET}")
        print(f"   {Colors.WHITE}1. Search by Class Name:{Colors.RESET}")
        print(f"      cli_search CameraCapturedBlurImage")
        print(f"   {Colors.WHITE}2. Search by Virtual Address (VA):{Colors.RESET}")
        print(f"      cli_search 0x0417BE60")
        print(f"   {Colors.WHITE}3. Output in Korean Mode:{Colors.RESET}")
        print(f"      cli_search NetworkManager --lang ko")
        print(f"   {Colors.WHITE}4. Output in Raw JSON:{Colors.RESET}")
        print(f"      cli_search NetworkManager --json\n")

        print(f"{Colors.CYAN}{Colors.BOLD}* DATABASE INFRASTRUCTURE:{Colors.RESET}")
        print(f"   Auto-detects {Colors.YELLOW}database/*.db{Colors.RESET} directory next to the executable.")
        print(f"   - index.db        : Assemblies & Types Master")
        print(f"   - methods_1~2.db  : Sharded Methods Partition (<100MB)")
        print(f"   - signatures_1~4.db: Sharded C++ Signatures Partition (<100MB)")
        print(f"   - pointers.db     : TypeInfo / MethodInfo Pointers")
        print(f"   - symbols.db      : String Literals, Symbols, APIs, Exports\n")

def parse_custom_args():
    argv = sys.argv[1:]
    
    query = None
    lang = "en"
    json_mode = False
    help_mode = False
    version_mode = False

    idx = 0
    while idx < len(argv):
        arg = argv[idx]
        
        if arg in ["--help", "-h", "help", "도움말", "-도움말"]:
            help_mode = True
        elif arg in ["--version", "-v", "version", "버전", "-버전"]:
            version_mode = True
        elif arg in ["--json", "-j", "--제이슨", "json", "제이슨"]:
            json_mode = True
        elif arg in ["--lang", "-l", "--언어"]:
            if idx + 1 < len(argv):
                lang = argv[idx + 1].lower()
                idx += 1
        elif arg.startswith("--lang="):
            lang = arg.split("=", 1)[1].lower()
        elif arg.startswith("--언어="):
            lang = arg.split("=", 1)[1].lower()
        elif arg in ["--query", "-q", "--검색어"]:
            if idx + 1 < len(argv):
                query = argv[idx + 1]
                idx += 1
        elif arg.startswith("--query="):
            query = arg.split("=", 1)[1]
        elif arg.startswith("--검색어="):
            query = arg.split("=", 1)[1]
        elif not arg.startswith("-") and query is None:
            query = arg
        idx += 1

    return query, lang, json_mode, help_mode, version_mode

def render_result(context, lang="en"):
    labels = {
        "query": "검색 쿼리" if lang == "ko" else "Search Query",
        "matched": "매칭된 타입 수" if lang == "ko" else "Matched Types",
        "type": "타입 정의" if lang == "ko" else "TYPE",
        "assembly": "어셈블리" if lang == "ko" else "Assembly",
        "total_methods": "소속 메서드 총 수" if lang == "ko" else "Total Methods",
        "methods_list": "[ 전체 메서드 리스트 ]" if lang == "ko" else "[ Methods List ]",
        "native_sig": "네이티브 시그니처" if lang == "ko" else "Native Signature",
        "method_info": "[ MethodInfo 포인터 레퍼런스 ]" if lang == "ko" else "[ MethodInfo Pointers ]",
        "type_info": "[ TypeInfo 포인터 레퍼런스 ]" if lang == "ko" else "[ TypeInfo Pointers ]",
        "type_ref": "[ TypeRef 포인터 레퍼런스 ]" if lang == "ko" else "[ TypeRef Pointers ]",
        "additional": "=== 추가 연관 심볼 / 리터럴 맥락 ===" if lang == "ko" else "=== Additional Matched Context ==="
    }

    print_banner(lang)
    print(f"{Colors.WHITE}{Colors.BOLD}> {labels['query']}:{Colors.RESET} {Colors.YELLOW}{context['query']}{Colors.RESET}")
    print(f"{Colors.WHITE}{Colors.BOLD}> {labels['matched']}:{Colors.RESET} {Colors.GREEN}{context['matched_types_count']}{Colors.RESET}\n")

    for idx, t in enumerate(context["types_context"], 1):
        print(f"{Colors.CYAN}+-- {Colors.BOLD}{labels['type']} [{idx}]: {t['full_name']}{Colors.RESET}")
        print(f"{Colors.CYAN}|{Colors.RESET}  {Colors.WHITE}{labels['assembly']}:{Colors.RESET} {Colors.MAGENTA}{t['assembly']}{Colors.RESET}")
        print(f"{Colors.CYAN}|{Colors.RESET}  {Colors.WHITE}{labels['total_methods']}:{Colors.RESET} {Colors.GREEN}{t['method_count']}{Colors.RESET}")
        print(f"{Colors.CYAN}|{Colors.RESET}")
        print(f"{Colors.CYAN}+-- {Colors.BOLD}{labels['methods_list']}{Colors.RESET}")

        for m in t["methods"]:
            generic_str = f" {Colors.YELLOW}(Generic){Colors.RESET}" if m["is_generic"] else ""
            vaddr_str = f"{Colors.GREEN}[{m['virtual_address'] or 'N/A'}]{Colors.RESET}"
            print(f"{Colors.CYAN}|{Colors.RESET}  * {vaddr_str} {Colors.WHITE}{m['dotnet_signature']}{Colors.RESET}{generic_str}")
            print(f"{Colors.CYAN}|{Colors.RESET}    {Colors.DIM}{labels['native_sig']}: {m['signature']}{Colors.RESET}")

        if t["method_info_pointers"]:
            print(f"{Colors.CYAN}|{Colors.RESET}")
            print(f"{Colors.CYAN}+-- {Colors.BOLD}{labels['method_info']}{Colors.RESET}")
            for mip in t["method_info_pointers"]:
                print(f"{Colors.CYAN}|{Colors.RESET}  -> VA: {Colors.GREEN}{mip['virtual_address']}{Colors.RESET} -> Target VA: {Colors.YELLOW}{mip['method_address']}{Colors.RESET} ({mip['dotnet_signature']})")

        if t["type_info_pointers"]:
            print(f"{Colors.CYAN}|{Colors.RESET}")
            print(f"{Colors.CYAN}+-- {Colors.BOLD}{labels['type_info']}{Colors.RESET}")
            for tip in t["type_info_pointers"]:
                print(f"{Colors.CYAN}|{Colors.RESET}  -> VA: {Colors.GREEN}{tip['virtual_address']}{Colors.RESET} | {tip['name']} | DotNet: {tip['dotnet_type']}")

        if t["type_ref_pointers"]:
            print(f"{Colors.CYAN}|{Colors.RESET}")
            print(f"{Colors.CYAN}+-- {Colors.BOLD}{labels['type_ref']}{Colors.RESET}")
            for trp in t["type_ref_pointers"]:
                print(f"{Colors.CYAN}|{Colors.RESET}  -> VA: {Colors.GREEN}{trp['virtual_address']}{Colors.RESET} | {trp['name']} | DotNet: {trp['dotnet_type']}")

        print(f"{Colors.CYAN}+--------------------------------------------------------------------{Colors.RESET}\n")

    if context["additional_matched_context"]:
        print(f"{Colors.MAGENTA}{Colors.BOLD}{labels['additional']}{Colors.RESET}")
        print(json.dumps(context["additional_matched_context"], indent=2, ensure_ascii=False))

def main():
    init_console()

    query, lang, json_mode, help_mode, version_mode = parse_custom_args()

    if version_mode:
        print_banner(lang)
        print(f"{Colors.GREEN}IL2CPP AI Context Engine Version: v{VERSION}{Colors.RESET}")
        sys.exit(0)

    if help_mode or not query:
        print_detailed_help(lang)
        sys.exit(0)

    context = search_context(query)

    if json_mode:
        print(json.dumps(context, indent=2, ensure_ascii=False))
    else:
        render_result(context, lang)

if __name__ == "__main__":
    main()
