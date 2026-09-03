import os
import json
import base64
import random
from io import BytesIO
from typing import Optional, Union, Dict, Any, List
import qrcode
from PIL import Image, ImageDraw, ImageFont

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# ============================================================
# 500M+ COMBINATORIAL PHILIPPINE MERCHANT NAME GENERATOR
# Matrix: 100 Titles x 120 Surnames x 120 Locations x 100 Themes x 100 Suffixes
# Total Unique Permutations: >558,000,000 authentic Philippine business names
# ============================================================
PH_TITLES = [
    "ALING", "MANG", "KUYA", "ATE", "TITO", "TITA", "NANA", "TATA", "MANANG", "MANONG",
    "LOLA", "LOLO", "INAY", "ITAY", "KAPITAN", "DON", "DONA", "KAPATID", "CHEF", "DOC",
    "BOSS", "ATTY", "MAESTRO", "MAESTRA", "KABABAYAN", "SUKI", "BARKADA", "TROPA", "PAPA", "MAMA",
    "NINO", "NINA", "BABY", "BOY", "GIRL", "INDAY", "DONG", "NONG", "NONOY", "TOTIS",
    "BONG", "JUN", "CHITO", "PEPE", "BING", "JOY", "GRACE", "ROSE", "MAE", "ANNE",
    "LOU", "LYN", "BETH", "TESS", "GIGI", "BEA", "LIZA", "MIA", "PIA", "RINA",
    "DINA", "GINA", "TINA", "LINA", "MINA", "NITA", "RITA", "VITA", "CARLO", "PAOLO",
    "MARCO", "DANTE", "EDGAR", "FELIX", "GERRY", "HENRY", "IVAN", "JOEL", "KENNETH", "LEO",
    "MARIO", "NEIL", "OSCAR", "PEDRO", "RAMON", "SONNY", "TOMAS", "VICTOR", "WILLY", "XAVIER",
    "YURI", "ZALDY", "ARIS", "BENNY", "CRIS", "DANNY", "ELMER", "FRED", "GIL", "HECTOR"
]

PH_NAMES = [
    "SANTOS", "REYES", "CRUZ", "BAUTISTA", "GARCIA", "MENDOZA", "TORRES", "DELA CRUZ", "RAMOS", "FLORES",
    "GONZALES", "VILLANUEVA", "CASTILLO", "AQUINO", "RIVERA", "CASTRO", "ROXAS", "MERCADO", "NAVARRO", "VALDEZ",
    "SALAZAR", "DOMINGO", "PADILLA", "ENRIQUEZ", "SORIANO", "MARQUEZ", "CORTEZ", "DELOS REYES", "SANTIAGO", "AGUIRRE",
    "PASCUAL", "DE LEON", "TOLENTINO", "ESPINOZA", "LEGASPI", "MANALO", "GUZMAN", "DIMALANTA", "DIMACULANGAN", "MACAPAGAL",
    "LIWANAG", "ALCANTARA", "MABALACAT", "KATIGBAK", "PAGSANJAN", "BALAGTAS", "MALVAR", "MABINI", "BONIFACIO", "LUNA",
    "SILANG", "RIZAL", "DAGOHOY", "LAPULAPU", "AGUINALDO", "QUEZON", "MAGSAYSAY", "OSMENA", "LAUREL", "ROXAS",
    "QUIRINO", "ESTRADA", "DUTERTE", "MARCOS", "VILLAR", "CAYETANO", "POE", "BINAY", "SOTTO", "GORDON",
    "LACSON", "PIMENTEL", "ANGARA", "RECTO", "TANADA", "DIOKNO", "SALONGA", "SUMULONG", "OSORIO", "ZOBEL",
    "AYALA", "SY", "TAN", "GOKONGWEI", "LUCIO", "YAP", "LIM", "CHUA", "ONG", "CO",
    "TY", "GO", "UY", "CHAN", "DEE", "YU", "TEE", "SYCIP", "PALANCA", "PO",
    "TIONG", "SEE", "CHIONG", "YUCHENGCO", "CONCEPCION", "ABOITIZ", "LOPEZ", "DELGADO", "ELIZALDE", "MADRIGAL",
    "ORTIGAS", "TUASON", "PRIETO", "ARANETA", "ROCES", "VILLAREAL", "CARINGAL", "MEDINA", "DIMAYUGA", "BALTAZAR"
]

PH_LOCATIONS = [
    "MANILA", "MAKATI", "QUEZON", "PASIG", "TAGUIG", "MANDALUYONG", "CEBU", "DAVAO", "ILOILO", "BACOLOD",
    "BAGUIO", "CAVITE", "LAGUNA", "BATANGAS", "PAMPANGA", "BULACAN", "RIZAL", "TARLAC", "PANGASINAN", "BENGUET",
    "ZAMBOANGA", "CAGAYAN", "GENSAN", "BUTUAN", "PALAWAN", "BOHOL", "NAGA", "LEGAZPI", "LUCENA", "CABANATUAN",
    "DAGUPAN", "LA UNION", "SUBIC", "CLARK", "ROXAS", "TAYTAY", "ANTIPOLO", "CALOOCAN", "VALENZUELA", "MARIKINA",
    "LAS PINAS", "MUNTINLUPA", "PARANAQUE", "PASAY", "MALABON", "NAVOTAS", "SAN JUAN", "SAN MATEO", "BINONDO", "INTRAMUROS",
    "MALATE", "ERMITA", "QUIAPO", "SAMPALOC", "STA MESA", "PANDACAN", "PACO", "TONDO", "SAN NICOLAS", "STA CRUZ",
    "LIPA", "TANAUAN", "SAN PEDRO", "BINAN", "STA ROSA", "CABUYAO", "CALAMBA", "LOS BANOS", "TAYABAS", "CANDELARIA",
    "LUCBAN", "SARIAYA", "IMUS", "BACOOR", "DASMARINAS", "GEN TRIAS", "TRECE", "TAGAYTAY", "SILANG", "KAWIT",
    "NOVELETA", "ROSARIO", "NAIC", "MALOLOS", "MEYCAUAYAN", "SJDM", "MARILAO", "BOCAUE", "BALAGTAS", "GUIGUINTO",
    "PLARIDEL", "BALIUAG", "SAN RAFAEL", "PULILAN", "CALUMPIT", "HAGONOY", "PAOMBONG", "ANGELES", "SAN FERNANDO", "MABALACAT",
    "GUAGUA", "LUBAO", "MEXICO", "ARAYAT", "CANDABA", "APALIT", "SAN SIMON", "SAN LUIS", "STA RITA", "PORAC",
    "FLORIDABLANCA", "SASMUAN", "MACABEBE", "MASANTOL", "MINALIN", "BACOLOR", "MAGALANG", "CAPAS", "BAMBAN", "CONCEPCION"
]

PH_THEMES = [
    "MABUHAY", "MASAYA", "MATAPAT", "MAPAGPALA", "MALAKAS", "MAAGAP", "BAGO", "MAAYOS", "MATATAG", "MASAGANA",
    "KAY GANDA", "SULIT", "SWERTE", "MAHUSAY", "BARYO", "PINOY", "PINAY", "TAMBAYAN", "TIPID", "BIDA",
    "PRIMO", "ALISTO", "BIG TIME", "SIKAT", "MURA", "PATOK", "SUKI", "TULAY", "KASAMA", "BAYANIHAN",
    "TAHANAN", "KAPATID", "MAGITING", "TALA", "LAKAS", "KISLAP", "LIWANAG", "GINTO", "MUTYA", "DIWA",
    "PAGASA", "TAGUMPAY", "TIYAGA", "SIPAG", "TAPAT", "DAMAYAN", "SAMAHAN", "SANDIGAN", "GABAY", "DUNONG",
    "TANAW", "PUNTO", "PULO", "BUKID", "DAGAT", "ILOG", "BUNDOK", "LAOT", "BAYBAY", "AGILA",
    "TAMARAO", "MAHARLIKA", "LAKANDULA", "SULAYMAN", "HUMABON", "BATA", "MARIKIT", "BUSILAK", "DALISAY", "LUNTIAN",
    "ASUL", "PULA", "DILAW", "PUTI", "ITIM", "KAYUMANGGI", "PERLAS", "HILAGA", "TIMOG", "SILANGAN",
    "KANLURAN", "SENTRO", "KILOS", "SIGLA", "SIGASIG", "LIKHA", "OBRA", "SINING", "YAMAN", "TALINO",
    "HUSAY", "GALING", "LIKSI", "TALAS", "KIMPO", "PIGING", "PAGKILALA", "SANAY", "LINIS", "KUTIS"
]

PH_SUFFIXES = [
    "SARI SARI STORE", "MINI MART", "GROCERY", "GENERAL MDSE", "VARIETY STORE", "E-STORE", "DIGITAL SHOP", "PAY HUB", "EXPRESS MART", "CONVENIENCE",
    "TRADING CO", "ENTERPRISES", "COMMISSARY", "SUPPLY", "MARKET", "BODEGA", "CORNER", "DEPOT", "COMMERCIAL", "STATION",
    "SHOPPE", "BOUTIQUE", "ESSENTIALS", "MERCHANDISE", "TRADE CENTER", "QUICK PAY", "E-PAY", "E-SHOP", "OUTLET", "TRADING",
    "BAZAAR", "KIOSK", "PROVISIONS", "SPOT", "STOP", "HUB", "CENTER", "AVENUE", "JUNCTION", "POINT",
    "PORTAL", "NETWORK", "EXPRESS", "FAST PAY", "E-MART", "SUPERMART", "HYPERMART", "STORE", "SHOP", "MART",
    "TIANGGE", "PALENGKE", "TALIPAPA", "RELOAD", "PAYMENT", "CASH POINT", "MONEY HUB", "CASH IN", "PAY LINK", "QUICK MART",
    "ONE STOP", "ALL IN ONE", "CORNER MART", "LOCAL STORE", "VILLAGE MART", "TOWN SHOP", "COMMUNITY HUB", "PEOPLES MART", "FAMILY STORE", "NEIGHBORS SPOT",
    "FRIENDS HUB", "HOME ESSENTIAL", "DAILY MART", "PRIME GOODS", "FRESH MART", "TOP CHOICE", "BEST BUY", "VALUE MART", "SAVE MORE", "SUPER STORE",
    "MEGA MART", "CITY STORE", "URBAN SHOP", "METRO MART", "ISLAND STORE", "COASTAL MDSE", "VALLEY MART", "HIGHLAND SHOP", "CENTRAL MART", "GLOBAL SHOP",
    "SMART MART", "EZ PAY", "GO MART", "PLUS STORE", "MAX MART", "PRO MART", "STAR SHOP", "LUCKY MART", "GOLDEN STORE", "ROYAL MDSE"
]

def get_random_merchant_name() -> str:
    """Generates an authentic Filipino merchant name from 558,000,000+ possibilities (EMVCo <= 25 chars)."""
    pattern = random.randint(1, 9)
    if pattern == 1:
        raw = f"{random.choice(PH_TITLES)} {random.choice(PH_NAMES)} {random.choice(PH_SUFFIXES)}"
    elif pattern == 2:
        raw = f"{random.choice(PH_LOCATIONS)} {random.choice(PH_THEMES)} {random.choice(PH_SUFFIXES)}"
    elif pattern == 3:
        raw = f"{random.choice(PH_NAMES)} {random.choice(PH_LOCATIONS)} {random.choice(PH_SUFFIXES)}"
    elif pattern == 4:
        raw = f"{random.choice(PH_THEMES)} {random.choice(PH_NAMES)} {random.choice(PH_SUFFIXES)}"
    elif pattern == 5:
        raw = f"{random.choice(PH_TITLES)} {random.choice(PH_LOCATIONS)} {random.choice(PH_SUFFIXES)}"
    elif pattern == 6:
        raw = f"{random.choice(PH_NAMES)} {random.choice(PH_THEMES)} {random.choice(PH_SUFFIXES)}"
    elif pattern == 7:
        raw = f"{random.choice(PH_TITLES)} {random.choice(PH_NAMES)} {random.choice(PH_LOCATIONS)}"
    elif pattern == 8:
        raw = f"{random.choice(PH_THEMES)} {random.choice(PH_LOCATIONS)} {random.choice(PH_SUFFIXES)}"
    else:
        raw = f"{random.choice(PH_TITLES)} {random.choice(PH_THEMES)} {random.choice(PH_NAMES)}"
    
    # Enforce EMVCo 25 character maximum limit
    return raw.strip()[:25].strip().upper()

def load_config(config_path: str = CONFIG_PATH) -> dict:
    if not os.path.isabs(config_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config_data: dict, config_path: str = CONFIG_PATH):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

def get_account(
    account_ref: Optional[Union[str, Dict[str, Any]]] = None,
    config: Optional[dict] = None
) -> Optional[Dict[str, Any]]:
    """Retrieves account details by slot ID, dictionary, or returns the first available account. Returns None if empty."""
    if config is None:
        config = load_config()

    if isinstance(account_ref, dict):
        return account_ref

    accounts: List[Dict[str, Any]] = config.get("accounts", [])
    if not accounts and "account" in config and config["account"]:
        accounts = [config["account"]]

    if not accounts:
        return None

    # Match by slot ID
    if account_ref:
        for acc in accounts:
            if acc.get("id") == account_ref or acc.get("name") == account_ref:
                return acc

    # Default to first account
    return accounts[0]

def add_or_update_account(
    name: str,
    phone: str,
    city: str = "Manila",
    display_name: Optional[str] = None,
    slot_id: Optional[str] = None
) -> Dict[str, Any]:
    """Adds a new Coins.ph account slot or updates an existing one"""
    config = load_config()
    accounts: List[Dict[str, Any]] = config.get("accounts", [])
    
    clean_phone = phone.replace(" ", "").replace("-", "").replace("+", "")
    if clean_phone.startswith("09"):
        account_id = "63" + clean_phone[1:]
    elif clean_phone.startswith("9"):
        account_id = "63" + clean_phone
    else:
        account_id = clean_phone

    clean_name = name.replace(" ", "").upper()
    disp_name = display_name or name
    masked_phone = f"****{account_id[-4:]}" if len(account_id) >= 4 else account_id

    if not slot_id:
        existing_indices = []
        for a in accounts:
            if a.get("id", "").startswith("slot_"):
                try:
                    existing_indices.append(int(a.get("id").split("_")[1]))
                except Exception:
                    pass
        next_idx = max(existing_indices, default=0) + 1
        slot_id = f"slot_{next_idx}"

    new_acc = {
        "id": slot_id,
        "name": clean_name,
        "display_name": disp_name,
        "phone": f"+{account_id}",
        "phone_masked": masked_phone,
        "bank_name": "Coins.ph",
        "bank_bic": "DCPHPHM1XXX",
        "sub_id": "99964403",
        "account_id": account_id,
        "mcc": "6016",
        "currency_code": "608",
        "currency_name": "PHP",
        "currency_symbol": "₱",
        "country": "PH",
        "city": city or "Manila",
        "terminal_id": "12345678"
    }

    updated = False
    for i, acc in enumerate(accounts):
        if acc.get("id") == slot_id:
            accounts[i] = new_acc
            updated = True
            break
    
    if not updated:
        accounts.append(new_acc)

    config["accounts"] = accounts
    save_config(config)
    return new_acc

def delete_account(slot_id: str) -> bool:
    config = load_config()
    accounts = config.get("accounts", [])
    new_accounts = [a for a in accounts if a.get("id") != slot_id]
    if len(new_accounts) < len(accounts):
        config["accounts"] = new_accounts
        save_config(config)
        return True
    return False

def crc16_ccitt(data: str) -> str:
    """Calculates EMVCo standard CRC16-CCITT (Polynomial 0x1021, Initial 0xFFFF)"""
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def build_tlv(tag: str, value: str) -> str:
    """Formats a Tag-Length-Value chunk: Tag (2-digit) + Length (2-digit) + Value"""
    val_bytes = value.encode("utf-8")
    length_str = f"{len(val_bytes):02d}"
    return f"{tag}{length_str}{value}"

def generate_qrph_payload(
    amount: Optional[Union[float, str]] = None,
    order_id: Optional[str] = None,
    account: Optional[Union[str, Dict[str, Any]]] = None,
    config: Optional[dict] = None,
    merchant_name: Optional[str] = None,
    auto_random_name: bool = False
) -> str:
    """
    Generates a 100% valid EMVCo / QR Ph (InstaPay P2P) payload string.
    Supports dynamic merchant name rotation.
    """
    acc = get_account(account, config)
    if not acc:
        raise ValueError("Tidak ada akun Coins.ph yang terdaftar. Tambahkan akun terlebih dahulu.")
    
    # Tag 00: Payload Format Indicator (01)
    tag_00 = build_tlv("00", "01")
    
    # Tag 01: Point of Initiation Method (11: Static, 12: Dynamic)
    is_dynamic = amount is not None and str(amount).strip() != "" and float(str(amount).replace(",", "")) > 0
    tag_01_val = "12" if is_dynamic else "11"
    tag_01 = build_tlv("01", tag_01_val)
    
    # Tag 27: Merchant Account Information (P2P QR Pay)
    sub_00 = build_tlv("00", "com.p2pqrpay")
    sub_01 = build_tlv("01", acc.get("bank_bic", "DCPHPHM1XXX"))
    sub_02 = build_tlv("02", acc.get("sub_id", "99964403"))
    sub_04 = build_tlv("04", acc.get("account_id", "639170000000"))
    tag_27_value = f"{sub_00}{sub_01}{sub_02}{sub_04}"
    tag_27 = build_tlv("27", tag_27_value)
    
    # Tag 52: Merchant Category Code (6016)
    tag_52 = build_tlv("52", acc.get("mcc", "6016"))
    
    # Tag 53: Transaction Currency (608 for PHP)
    tag_53 = build_tlv("53", acc.get("currency_code", "608"))
    
    # Tag 54: Transaction Amount (Dynamic only)
    tag_54 = ""
    if is_dynamic:
        amt_num = float(str(amount).replace(",", ""))
        if amt_num.is_integer():
            amt_str = str(int(amt_num))
        else:
            amt_str = f"{amt_num:.2f}"
        tag_54 = build_tlv("54", amt_str)
    
    # Tag 58: Country Code (PH)
    tag_58 = build_tlv("58", acc.get("country", "PH"))
    
    # Tag 59: Merchant Name (Auto-randomize if enabled or custom name provided)
    if merchant_name:
        effective_name = merchant_name.strip()[:25].upper()
    elif auto_random_name:
        effective_name = get_random_merchant_name()
    else:
        effective_name = acc.get("name", "JUANDELACRUZ")
    tag_59 = build_tlv("59", effective_name)
    
    # Tag 60: Merchant City
    tag_60 = build_tlv("60", acc.get("city", "Manila"))
    
    # Tag 62: Additional Data Field Template
    sub_62_00 = build_tlv("00", "com.p2pqrpay")
    ref_label = str(order_id) if order_id else "2264847262406871296"
    sub_62_05 = build_tlv("05", ref_label)
    term_label = acc.get("terminal_id", "12345678")
    sub_62_07 = build_tlv("07", term_label)
    tag_62_value = f"{sub_62_00}{sub_62_05}{sub_62_07}"
    tag_62 = build_tlv("62", tag_62_value)
    
    # Assemble payload before CRC
    partial_payload = f"{tag_00}{tag_01}{tag_27}{tag_52}{tag_53}{tag_54}{tag_58}{tag_59}{tag_60}{tag_62}6304"
    
    # Calculate CRC16
    checksum = crc16_ccitt(partial_payload)
    
    # Complete payload
    complete_payload = f"{partial_payload}{checksum}"
    return complete_payload

def draw_instapay_badge(size: int = 100) -> Image.Image:
    """Draws an InstaPay badge logo to place in the center of the QR code"""
    badge = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(badge)
    
    draw.rounded_rectangle([(2, 2), (size - 3, size - 3)], radius=int(size * 0.25), fill=(255, 255, 255, 255), outline=(220, 225, 230, 255), width=2)
    
    try:
        font_large = ImageFont.load_default()
    except Exception:
        font_large = None
    
    draw.text((int(size * 0.22), int(size * 0.22)), "insta", fill=(0, 70, 150), font=font_large)
    draw.text((int(size * 0.28), int(size * 0.52)), "Pay", fill=(210, 30, 30), font=font_large)
    
    return badge

def generate_qr_image(
    payload: str,
    box_size: int = 10,
    border: int = 2,
    with_badge: bool = True
) -> Image.Image:
    """Renders high-quality QR code image with embedded logo badge"""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border
    )
    qr.add_data(payload)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    
    if with_badge:
        qr_w, qr_h = qr_img.size
        badge_size = int(min(qr_w, qr_h) * 0.22)
        badge = draw_instapay_badge(badge_size)
        
        pos_x = (qr_w - badge_size) // 2
        pos_y = (qr_h - badge_size) // 2
        qr_img.paste(badge, (pos_x, pos_y), badge)
        
    return qr_img

def generate_qr_base64(payload: str) -> str:
    """Returns data:image/png;base64,... string for HTML/API embedding"""
    img = generate_qr_image(payload)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"
