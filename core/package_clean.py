import os
import zipfile
import json
from datetime import datetime

def make_clean_package():
    # Root dir is parent of core/
    core_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(core_dir)
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"COINS_PAYMENT_GATEWAY_KOSONGAN_{date_str}.zip"
    zip_path = os.path.join(root_dir, zip_name)

    EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", ".idea", ".vscode", "scratch", "COINS PAYMENT GATEWAY", "NGROK SAFA"}
    EXCLUDE_FILES = {"payments.db", "ngrok.exe", "START_NGROK.bat", "START_ALL.bat", "BUAT_PAKET_KOSONGAN.bat", ".bot.pid", "users.json", "access_codes.json", zip_name}
    EXCLUDE_EXTENSIONS = {".pyc", ".log", ".zip", ".tmp"}

    CLEAN_CONFIG = {
        "telegram": {
            "bot_token": "ISI_BOT_TOKEN_DISINI",
            "admin_ids": []
        },
        "security": {
            "user_sessions": {},
            "access_codes": {}
        },
        "bot_settings": {
            "default_base_php": 100,
            "auto_check_interval_seconds": 5,
            "invoice_timeout_minutes": 15,
            "auto_random_name": True
        },
        "accounts": [],
        "rates": {
            "base_rate": 60.55,
            "buffer": 0.20
        },
        "server": {
            "host": "0.0.0.0",
            "port": 5000,
            "api_key": "coins_secret_key_123",
            "invoice_timeout_minutes": 15
        }
    }

    print("=" * 66)
    print("      MEMBUAT PAKET KOSONGAN (MURNI BERSIH SIAP PAKAI)")
    print("=" * 66)
    print(f"[*] Folder Root  : {root_dir}")
    print(f"[*] Target ZIP   : {zip_name}")
    print()

    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if file in EXCLUDE_FILES or ext in EXCLUDE_EXTENSIONS or file.endswith(".zip"):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, root_dir)
                
                if file == "config.json":
                    zipf.writestr(arcname, json.dumps(CLEAN_CONFIG, indent=2, ensure_ascii=False))
                    print(f"  [CLEAN] {arcname} (Akun & data pribadi dikosongkan)")
                elif file == "wallet_manager.py":
                    with open(file_path, "r", encoding="utf-8") as wf:
                        wcode = wf.read()
                    import re
                    wcode_clean = re.sub(r'DEFAULT_DEV_SEED_PHRASE\s*=\s*["\'].*?["\']', 'DEFAULT_DEV_SEED_PHRASE = ""', wcode)
                    zipf.writestr(arcname, wcode_clean)
                    print(f"  [CLEAN] {arcname} (Seed phrase / private keys dikosongkan)")
                elif file == "pos.html":
                    with open(file_path, "r", encoding="utf-8") as pf:
                        pcode = pf.read()
                    import re
                    pcode_clean = re.sub(r'const devPhrase\s*=\s*["\'].*?["\'];', 'const devPhrase = "";', pcode)
                    zipf.writestr(arcname, pcode_clean)
                    print(f"  [CLEAN] {arcname} (Dev phrase & kredensial dikosongkan)")
                else:
                    zipf.write(file_path, arcname)
                    print(f"  [OK]    {arcname}")
                count += 1

    size_kb = os.path.getsize(zip_path) / 1024
    print()
    print("=" * 66)
    print(f"  [SUKSES] {count} file berhasil dikemas!")
    print(f"  [FILE]   {zip_name}")
    print(f"  [UKURAN] {size_kb:.1f} KB")
    print("=" * 66)

if __name__ == "__main__":
    make_clean_package()
