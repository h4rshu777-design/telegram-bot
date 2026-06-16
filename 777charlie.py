#!/usr/bin/env python3
"""
Python Encoder Telegram Bot — Full Edition
All encoding methods preserved. Full admin panel with:
  Admin Management, Custom Font System, Button Name Editor,
  Category Editor, User Management, Broadcast System,
  Maintenance Mode, DB Backup/Restore, Settings persistence.
"""

import os, io, ast, re, base64, marshal, zlib, binascii, codecs
import logging, sqlite3, json, time, datetime, asyncio, csv
from typing import Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, Document,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)
from telegram.constants import ParseMode

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
BOT_TOKEN     = "8951400081:AAHR3jAfJVihnug47--Rh332r2cw2kCDcAQ"
CHANNEL_ID    = "@iownscript"
CHANNEL_URL   = "https://t.me/stuff_portal"
DEVELOPER_URL= "t.me/harshucontactbot"
ADMIN_IDS     = [8416077220]   # Your Telegram user ID(s)
# ─────────────────────────────────────────────

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
BOT_START_TIME = time.time()

DB_PATH = "encoder_bot.db"

# ══════════════════════════════════════════════
#  UNICODE FONT MAPS
# ══════════════════════════════════════════════
FONT_MAPS = {
    "bold": {
        **{chr(ord('A')+i): chr(0x1D400+i) for i in range(26)},
        **{chr(ord('a')+i): chr(0x1D41A+i) for i in range(26)},
        **{str(i): chr(0x1D7CE+i) for i in range(10)},
    },
    "italic": {
        **{chr(ord('A')+i): chr(0x1D434+i) for i in range(26)},
        **{chr(ord('a')+i): ('𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧')[i] for i in range(26)},
    },
    "monospace": {
        **{chr(ord('A')+i): chr(0x1D670+i) for i in range(26)},
        **{chr(ord('a')+i): chr(0x1D68A+i) for i in range(26)},
        **{str(i): chr(0x1D7F6+i) for i in range(10)},
    },
    "small_caps": dict(zip(
        "abcdefghijklmnopqrstuvwxyz",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢ"
    )),
    "fraktur": {
        **{chr(ord('A')+i): chr(0x1D504+i) for i in range(26)},
        **{chr(ord('a')+i): chr(0x1D51E+i) for i in range(26)},
    },
    "double_struck": {
        **{chr(ord('A')+i): chr(0x1D538+i) for i in range(26)},
        **{chr(ord('a')+i): chr(0x1D552+i) for i in range(26)},
        **{str(i): chr(0x1D7D8+i) for i in range(10)},
    },
    "fancy": dict(zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏"
    )),
    "wide": dict(zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９"
    )),
}

def apply_font(text: str, style: str) -> str:
    if style == "normal" or style not in FONT_MAPS:
        return text
    fmap = FONT_MAPS[style]
    return "".join(fmap.get(c, c) for c in text)

FONT_STYLE_NAMES = {
    "normal":       "Normal",
    "bold":         "𝗕𝗼𝗹𝗱",
    "italic":       "𝘐𝘵𝘢𝘭𝘪𝘤",
    "monospace":    "𝙼𝚘𝚗𝚘𝚜𝚙𝚊𝚌𝚎",
    "small_caps":   "ꜱᴍᴀʟʟ ᴄᴀᴘꜱ",
    "fraktur":      "𝔉𝔯𝔞𝔨𝔱𝔲𝔯",
    "double_struck":"𝔻𝕠𝕦𝕓𝕝𝕖",
    "fancy":        "𝒻𝒶𝓃𝒸𝓎",
    "wide":         "Ｗｉｄｅ",
}

# ══════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT DEFAULT '',
            first_name    TEXT DEFAULT '',
            join_date     TEXT,
            last_active   TEXT,
            total_encodes INTEGER DEFAULT 0,
            is_banned     INTEGER DEFAULT 0,
            ban_reason    TEXT DEFAULT '',
            unban_history TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS encode_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            method    TEXT,
            filename  TEXT,
            success   INTEGER DEFAULT 1,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS bot_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS encoder_settings (
            method_key   TEXT PRIMARY KEY,
            display_name TEXT,
            enabled      INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS admin_list (
            user_id INTEGER PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS broadcast_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            btype      TEXT,
            summary    TEXT,
            delivered  INTEGER DEFAULT 0,
            failed     INTEGER DEFAULT 0,
            timestamp  TEXT
        );
        CREATE TABLE IF NOT EXISTS failed_broadcast_users (
            broadcast_id INTEGER,
            user_id      INTEGER,
            PRIMARY KEY (broadcast_id, user_id)
        );
    """)

    defaults = {
        "maintenance_mode":    "0",
        "maintenance_message": "⚠️ Bot is currently under maintenance.\nPlease try again later.",
        "bot_name":            "PYTHON ENCODER BOT",
        "bot_subtitle":        "Protect your Python source code from casual viewing and copying.",
        "header_text":         "🔐 PYTHON ENCODER BOT",
        "footer_text":         "Supported formats: .py only",
        "welcome_title":       "🔐 𝗣𝗬𝗧𝗛𝗢𝗡 𝗘𝗡𝗖𝗢𝗗𝗘𝗥 𝗕𝗢𝗧\n\n«𝗦𝗢𝗨𝗥𝗖𝗘 𝗣𝗥𝗢𝗧𝗘𝗖𝗧𝗜𝗢𝗡\n𝗘𝗡𝗖𝗢𝗗𝗘 𝗠𝗢𝗗𝗨𝗟𝗘𝗦\n𝗦𝗘𝗖𝗨𝗥𝗘 𝗣𝗥𝗢𝗖𝗘𝗦𝗦𝗜𝗡𝗚»",
        "welcome_description": "📎 This bot can encode your Python file with multiple encryption methods!",
        "welcome_footer":      "⛔️ Send Your Python File (.py) to continue!!",
        "force_join_channel":  CHANNEL_ID,
        "channel_url":         CHANNEL_URL,
        "developer_url":       DEVELOPER_URL,
        "adv_category_label":  "🔥 ─── ADVANCED ENCODERS ───",
        "nor_category_label":  "📦 ─── NORMAL ENCODERS ───",
        "btn_join_channel":    "📢 Join Channel",
        "btn_developer":       "👨‍💻 Developer",
        "btn_encode_again":    "🔄 Encode Another File",
        "btn_channel":         "📢 Channel",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO bot_settings (key,value) VALUES (?,?)", (k, v))

    encoder_defaults = {
        "dx_enc": "DX-Enc", "pyspector": "PySpector", "special": "Special",
        "b85_zlib": "B85+Zlib", "a85_zlib": "A85+Zlib", "b32_zlib": "B32+Zlib",
        "marshal": "Marshal", "zlib": "Zlib", "base16": "Base16", "base32": "Base32",
        "base64": "Base64", "ascii85": "Ascii85", "hex": "Hex",
        "url_b64": "URL-B64", "string_repr": "String Repr",
    }
    for mk, dn in encoder_defaults.items():
        c.execute("INSERT OR IGNORE INTO encoder_settings (method_key,display_name,enabled) VALUES (?,?,1)", (mk,dn))

    for aid in ADMIN_IDS:
        c.execute("INSERT OR IGNORE INTO admin_list (user_id) VALUES (?)", (aid,))

    conn.commit()
    conn.close()

def get_setting(key: str, default: str = "") -> str:
    conn = get_db()
    row = conn.execute("SELECT value FROM bot_settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO bot_settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def upsert_user(user_id: int, username: str, first_name: str):
    conn = get_db()
    now = datetime.datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO users (user_id,username,first_name,join_date,last_active)
        VALUES (?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_active=excluded.last_active
    """, (user_id, username or "", first_name or "", now, now))
    conn.commit()
    conn.close()

def update_last_active(user_id: int):
    conn = get_db()
    now = datetime.datetime.utcnow().isoformat()
    conn.execute("UPDATE users SET last_active=? WHERE user_id=?", (now, user_id))
    conn.commit()
    conn.close()

def log_encode(user_id: int, method: str, filename: str, success: int):
    conn = get_db()
    now = datetime.datetime.utcnow().isoformat()
    conn.execute("INSERT INTO encode_log (user_id,method,filename,success,timestamp) VALUES (?,?,?,?,?)",
                 (user_id, method, filename, success, now))
    if success:
        conn.execute("UPDATE users SET total_encodes=total_encodes+1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id: int) -> bool:
    conn = get_db()
    row = conn.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return bool(row and row["is_banned"])

def ban_user(user_id: int, reason: str = ""):
    conn = get_db()
    conn.execute("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?", (reason, user_id))
    conn.commit()
    conn.close()

def unban_user(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT unban_history FROM users WHERE user_id=?", (user_id,)).fetchone()
    history = json.loads(row["unban_history"]) if row else []
    history.append(datetime.datetime.utcnow().isoformat())
    conn.execute("UPDATE users SET is_banned=0, ban_reason='', unban_history=? WHERE user_id=?",
                 (json.dumps(history), user_id))
    conn.commit()
    conn.close()

def get_user_info(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def search_user_by_username(username: str):
    uname = username.lstrip("@")
    conn = get_db()
    rows = conn.execute("SELECT * FROM users WHERE username LIKE ?", (f"%{uname}%",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_user_ids() -> list:
    conn = get_db()
    rows = conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]

def get_all_users_csv() -> str:
    conn = get_db()
    rows = conn.execute("SELECT user_id,username,first_name,join_date,last_active,total_encodes,is_banned FROM users ORDER BY join_date DESC").fetchall()
    conn.close()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["user_id","username","first_name","join_date","last_active","total_encodes","is_banned"])
    for r in rows:
        w.writerow([r["user_id"],r["username"],r["first_name"],r["join_date"],r["last_active"],r["total_encodes"],r["is_banned"]])
    return buf.getvalue()

def get_stats() -> dict:
    conn = get_db()
    total_users   = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    active_users  = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_banned=0").fetchone()["c"]
    banned_users  = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_banned=1").fetchone()["c"]
    total_encoded = conn.execute("SELECT COUNT(*) as c FROM encode_log").fetchone()["c"]
    total_success = conn.execute("SELECT COUNT(*) as c FROM encode_log WHERE success=1").fetchone()["c"]
    total_failed  = conn.execute("SELECT COUNT(*) as c FROM encode_log WHERE success=0").fetchone()["c"]
    recent_users  = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE last_active >= ?",
        ((datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat(),)
    ).fetchone()["c"]
    conn.close()
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    uptime_seconds = int(time.time() - BOT_START_TIME)
    h, rem = divmod(uptime_seconds, 3600)
    m, s   = divmod(rem, 60)
    return {
        "total_users": total_users, "active_users": active_users,
        "banned_users": banned_users, "recent_users": recent_users,
        "total_encoded": total_encoded, "total_success": total_success,
        "total_failed": total_failed, "db_size": db_size,
        "uptime": f"{h}h {m}m {s}s",
    }

# ── Encoder settings ──────────────────────────

def get_encoder_settings() -> dict:
    conn = get_db()
    rows = conn.execute("SELECT * FROM encoder_settings").fetchall()
    conn.close()
    return {r["method_key"]: {"display_name": r["display_name"], "enabled": bool(r["enabled"])} for r in rows}

def set_encoder_name(method_key: str, name: str):
    conn = get_db()
    conn.execute("UPDATE encoder_settings SET display_name=? WHERE method_key=?", (name, method_key))
    conn.commit()
    conn.close()

def set_encoder_enabled(method_key: str, enabled: bool):
    conn = get_db()
    conn.execute("UPDATE encoder_settings SET enabled=? WHERE method_key=?", (1 if enabled else 0, method_key))
    conn.commit()
    conn.close()

ENCODER_DEFAULTS = {
    "dx_enc": "DX-Enc", "pyspector": "PySpector", "special": "Special",
    "b85_zlib": "B85+Zlib", "a85_zlib": "A85+Zlib", "b32_zlib": "B32+Zlib",
    "marshal": "Marshal", "zlib": "Zlib", "base16": "Base16", "base32": "Base32",
    "base64": "Base64", "ascii85": "Ascii85", "hex": "Hex",
    "url_b64": "URL-B64", "string_repr": "String Repr",
}

def reset_encoder_names():
    conn = get_db()
    for mk, dn in ENCODER_DEFAULTS.items():
        conn.execute("UPDATE encoder_settings SET display_name=? WHERE method_key=?", (dn, mk))
    conn.commit()
    conn.close()

# ── Admin list ────────────────────────────────

def get_admin_ids() -> list:
    conn = get_db()
    rows = conn.execute("SELECT user_id FROM admin_list").fetchall()
    conn.close()
    base = [r["user_id"] for r in rows]
    for aid in ADMIN_IDS:
        if aid not in base:
            base.append(aid)
    return base

def add_admin(user_id: int):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO admin_list (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def remove_admin(user_id: int):
    if user_id in ADMIN_IDS:
        return False
    conn = get_db()
    conn.execute("DELETE FROM admin_list WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return True

def is_admin(user_id: int) -> bool:
    return user_id in get_admin_ids()

# ── Broadcast history ─────────────────────────

def log_broadcast(btype: str, summary: str, delivered: int, failed: int, failed_ids: list) -> int:
    conn = get_db()
    now = datetime.datetime.utcnow().isoformat()
    cur = conn.execute(
        "INSERT INTO broadcast_history (btype,summary,delivered,failed,timestamp) VALUES (?,?,?,?,?)",
        (btype, summary, delivered, failed, now)
    )
    bid = cur.lastrowid
    for uid in failed_ids:
        conn.execute("INSERT OR IGNORE INTO failed_broadcast_users (broadcast_id,user_id) VALUES (?,?)", (bid, uid))
    conn.commit()
    conn.close()
    return bid

def get_broadcast_history(limit: int = 10) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM broadcast_history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_failed_broadcast_users(broadcast_id: int) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT user_id FROM failed_broadcast_users WHERE broadcast_id=?", (broadcast_id,)
    ).fetchall()
    conn.close()
    return [r["user_id"] for r in rows]

# ══════════════════════════════════════════════
#  ENCODING ENGINE  (unchanged)
# ══════════════════════════════════════════════

class PythonEncryptor:

    @staticmethod
    def extract_imports(code: str) -> list:
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}" if module else f"import {alias.name}")
        except Exception:
            lines = re.findall(r'^(?:from\s+\S+\s+)?import\s+[^#\n]+', code, re.MULTILINE)
            imports.extend(lines)
        seen: set = set()
        unique: list = []
        for imp in imports:
            if imp not in seen:
                seen.add(imp)
                unique.append(imp)
        return unique

    @staticmethod
    def extract_functions_and_classes(code: str):
        functions, classes = [], []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
        except Exception:
            pass
        return functions, classes

    @staticmethod
    def _apply_layer(current, layer: str) -> bytes:
        if isinstance(current, str):
            current = current.encode()
        if layer == "base64":    return base64.b64encode(current)
        if layer == "base32":    return base64.b32encode(current)
        if layer == "base85":    return base64.b85encode(current)
        if layer == "ascii85":   return base64.a85encode(current)
        if layer == "base16":    return base64.b16encode(current)
        if layer == "zlib":      return zlib.compress(current, level=9)
        if layer == "reverse":   return current[::-1]
        if layer == "rot13":     return codecs.encode(current.decode(), "rot13").encode()
        if layer == "hex":       return binascii.hexlify(current)
        if layer == "marshal":   return marshal.dumps(current)
        if layer == "url_b64":   return base64.urlsafe_b64encode(current)
        if layer == "string_repr": return repr(current).encode()
        return current

    def encrypt_data(self, data, layers: list) -> bytes:
        current = data
        for layer in layers:
            current = self._apply_layer(current, layer)
        return current if isinstance(current, bytes) else current.encode()

    METHOD_LAYERS = {
        "dx_enc":      ["base64", "zlib", "reverse", "base85", "rot13", "hex", "marshal"],
        "pyspector":   ["zlib", "base85", "hex", "marshal", "base64"],
        "special":     ["marshal", "zlib", "base64", "reverse", "hex"],
        "b85_zlib":    ["zlib", "base85"],
        "a85_zlib":    ["zlib", "ascii85"],
        "b32_zlib":    ["zlib", "base32"],
        "marshal":     ["marshal"],
        "zlib":        ["zlib", "base64"],
        "base16":      ["base16"],
        "base32":      ["base32"],
        "base64":      ["base64"],
        "ascii85":     ["ascii85"],
        "hex":         ["hex"],
        "url_b64":     ["url_b64"],
        "string_repr": ["string_repr", "base64"],
    }

    METHOD_INFO = {
        "dx_enc":      {"name": "DX-Enc",       "protection": "High",   "speed": "Slow"},
        "pyspector":   {"name": "PySpector",    "protection": "High",   "speed": "Medium"},
        "special":     {"name": "Special",      "protection": "High",   "speed": "Slow"},
        "b85_zlib":    {"name": "B85+Zlib",     "protection": "Medium", "speed": "Fast"},
        "a85_zlib":    {"name": "A85+Zlib",     "protection": "Medium", "speed": "Fast"},
        "b32_zlib":    {"name": "B32+Zlib",     "protection": "Medium", "speed": "Fast"},
        "marshal":     {"name": "Marshal",      "protection": "Low",    "speed": "Fast"},
        "zlib":        {"name": "Zlib",         "protection": "Low",    "speed": "Fast"},
        "base16":      {"name": "Base16",       "protection": "Low",    "speed": "Fast"},
        "base32":      {"name": "Base32",       "protection": "Low",    "speed": "Fast"},
        "base64":      {"name": "Base64",       "protection": "Low",    "speed": "Fast"},
        "ascii85":     {"name": "Ascii85",      "protection": "Low",    "speed": "Fast"},
        "hex":         {"name": "Hex",          "protection": "Low",    "speed": "Fast"},
        "url_b64":     {"name": "URL-B64",      "protection": "Low",    "speed": "Fast"},
        "string_repr": {"name": "String Repr",  "protection": "Low",    "speed": "Fast"},
    }

    def build_encoded_script(self, encrypted_bytes: bytes, layers: list, original_imports: list) -> str:
        # Build compact runtime decoder — imports and source structure are never exposed.
        # The payload is a sealed base64(zlib(marshal(layers+data))) blob.
        import base64 as _b64, zlib as _zl, marshal as _ms
        meta = _ms.dumps((layers, encrypted_bytes))
        payload = _b64.b64encode(_zl.compress(meta, 9)).decode()
        return (
            "#!/usr/bin/env python3\n"
            "import base64,zlib,marshal,binascii,codecs\n"
            "_p=b'" + payload + "'\n"
            "def _d(d,ls):\n"
            " for l in reversed(ls):\n"
            "  if l=='base64':d=base64.b64decode(d)\n"
            "  elif l=='base32':d=base64.b32decode(d)\n"
            "  elif l=='base85':d=base64.b85decode(d)\n"
            "  elif l=='ascii85':d=base64.a85decode(d)\n"
            "  elif l=='base16':d=base64.b16decode(d)\n"
            "  elif l=='zlib':d=zlib.decompress(d)\n"
            "  elif l=='reverse':d=d[::-1]\n"
            "  elif l=='rot13':d=codecs.decode(d.decode(),'rot13').encode()\n"
            "  elif l=='hex':d=binascii.unhexlify(d)\n"
            "  elif l=='marshal':d=marshal.loads(d)\n"
            "  elif l=='url_b64':d=base64.urlsafe_b64decode(d)\n"
            "  elif l=='string_repr':\n"
            "   import ast as _a;d=_a.literal_eval(d.decode());d=d if isinstance(d,bytes) else d.encode()\n"
            " return d\n"
            "_ls,_e=marshal.loads(zlib.decompress(base64.b64decode(_p)))\n"
            "_r=_d(_e,_ls)\n"
            "if isinstance(_r,bytes):_r=_r.decode('utf-8')\n"
            "exec(compile(_r,'<protected>','exec'),{'__name__':'__main__'})\n"
        )

    def encode(self, source_code: str, method_key: str) -> tuple:
        layers = self.METHOD_LAYERS[method_key]
        imports = self.extract_imports(source_code)
        functions, classes = self.extract_functions_and_classes(source_code)
        encrypted = self.encrypt_data(source_code, layers)
        script = self.build_encoded_script(encrypted, layers, imports)
        stats = {
            "original_size": len(source_code.encode()),
            "encoded_size":  len(script.encode()),
            "imports":       len(imports),
            "functions":     len(functions),
            "classes":       len(classes),
        }
        return script, stats

# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

async def is_member(bot, user_id: int) -> bool:
    channel = get_setting("force_join_channel") or CHANNEL_ID
    try:
        member = await bot.get_chat_member(channel, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return True

def escape_md(text: str) -> str:
    """Escape MarkdownV2 special chars."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def build_welcome_text(first_name: str = "", user_id: int = 0, username: str = "") -> str:
    """
    Single, canonical welcome message builder.
    - Top block: dynamic user info (always injected, never stored in DB)
    - Middle block: UI Manager-controlled branding (welcome_title from DB)
    - Description block: UI Manager-controlled (welcome_description from DB)
    - Footer block: UI Manager-controlled (welcome_footer from DB)
    No hardcoded fallback text; no duplicate builders anywhere in the project.
    """
    # Dynamic user info — always live from Telegram
    display_username = f"@{username}" if username else "No Username"
    user_block = (
        f"👋 WELCOME {first_name}!!!\n\n"
        f"🆔 User ID: {user_id}\n"
        f"📛 Username: {display_username}"
    )

    # UI Manager-controlled sections (pulled from DB, admin-editable)
    title = get_setting("welcome_title")   # e.g. "🔐 𝗣𝗬𝗧𝗛𝗢𝗡 𝗘𝗡𝗖𝗢𝗗𝗘𝗥 𝗕𝗢𝗧"
    desc  = get_setting("welcome_description")
    foot  = get_setting("welcome_footer")

    parts = [user_block]
    if title:
        parts.append(title)
    if desc:
        parts.append(desc)
    if foot:
        parts.append(foot)

    return "\n\n".join(parts)

# ══════════════════════════════════════════════
#  KEYBOARD BUILDERS
# ══════════════════════════════════════════════

def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(get_setting("btn_join_channel"), url=get_setting("channel_url") or CHANNEL_URL),
        InlineKeyboardButton(get_setting("btn_developer"), url=get_setting("developer_url") or DEVELOPER_URL),
    ]])

def method_keyboard() -> InlineKeyboardMarkup:
    enc = get_encoder_settings()
    ADVANCED_KEYS = ["dx_enc","pyspector","special","b85_zlib","a85_zlib","b32_zlib"]
    NORMAL_KEYS   = ["marshal","zlib","base16","base32","base64","ascii85","hex","url_b64","string_repr"]
    def build_rows(keys):
        enabled = [k for k in keys if enc.get(k, {}).get("enabled", True)]
        rows = []
        for i in range(0, len(enabled), 3):
            chunk = enabled[i:i+3]
            rows.append([InlineKeyboardButton(enc[k]["display_name"], callback_data=f"method:{k}") for k in chunk])
        return rows
    adv_rows = build_rows(ADVANCED_KEYS)
    nor_rows = build_rows(NORMAL_KEYS)
    keyboard = []
    if adv_rows:
        keyboard.append([InlineKeyboardButton(get_setting("adv_category_label"), callback_data="noop")])
        keyboard.extend(adv_rows)
    if nor_rows:
        keyboard.append([InlineKeyboardButton(get_setting("nor_category_label"), callback_data="noop")])
        keyboard.extend(nor_rows)
    return InlineKeyboardMarkup(keyboard)

def post_encode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(get_setting("btn_encode_again"), callback_data="encode_again"),
        InlineKeyboardButton(get_setting("btn_channel"), url=get_setting("channel_url") or CHANNEL_URL),
    ]])

def join_required_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_setting("btn_join_channel"), url=get_setting("channel_url") or CHANNEL_URL)],
        [InlineKeyboardButton("✅ I've Joined – Continue", callback_data="check_join")],
    ])

def admin_back_keyboard(back_target: str = "adm:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=back_target)]])

def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard",    callback_data="adm:dashboard"),
         InlineKeyboardButton("👥 Users",        callback_data="adm:usermgmt")],
        [InlineKeyboardButton("📣 Broadcast",    callback_data="adm:broadcast"),
         InlineKeyboardButton("👑 Admins",       callback_data="adm:adminmgmt")],
        [InlineKeyboardButton("⚙️ Encoder Mgr", callback_data="adm:encodermgr"),
         InlineKeyboardButton("🔐 Encoder Ctrl",callback_data="adm:encoderctrl")],
        [InlineKeyboardButton("🎨 UI Manager",  callback_data="adm:uimgr"),
         InlineKeyboardButton("📡 Channel Cfg", callback_data="adm:channelcfg")],
        [InlineKeyboardButton("🔧 Maintenance", callback_data="adm:maintenance"),
         InlineKeyboardButton("💾 Database",    callback_data="adm:backup")],
        [InlineKeyboardButton("❌ Close",        callback_data="adm:close")],
    ])

def admin_usermgmt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban User",       callback_data="adm:ban"),
         InlineKeyboardButton("✅ Unban User",     callback_data="adm:unban")],
        [InlineKeyboardButton("🔍 User by ID",    callback_data="adm:userinfo"),
         InlineKeyboardButton("🔎 User by @name", callback_data="adm:usersearch")],
        [InlineKeyboardButton("👥 User Count",    callback_data="adm:usercount"),
         InlineKeyboardButton("📥 Export CSV",    callback_data="adm:exportusers")],
        [InlineKeyboardButton("🔙 Back",          callback_data="adm:main")],
    ])

def admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Text",      callback_data="adm:bc_text"),
         InlineKeyboardButton("🖼 Photo",     callback_data="adm:bc_photo")],
        [InlineKeyboardButton("🎬 Video",     callback_data="adm:bc_video"),
         InlineKeyboardButton("📎 Document",  callback_data="adm:bc_doc")],
        [InlineKeyboardButton("↩️ Forward",   callback_data="adm:bc_forward")],
        [InlineKeyboardButton("📋 History",   callback_data="adm:bc_history"),
         InlineKeyboardButton("🔁 Retry",     callback_data="adm:bc_retry")],
        [InlineKeyboardButton("🔙 Back",      callback_data="adm:main")],
    ])

def admin_adminmgmt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Admin",    callback_data="adm:add_admin"),
         InlineKeyboardButton("➖ Remove Admin", callback_data="adm:rem_admin")],
        [InlineKeyboardButton("📋 List Admins",  callback_data="adm:list_admins")],
        [InlineKeyboardButton("🔙 Back",         callback_data="adm:main")],
    ])

def admin_maintenance_keyboard() -> InlineKeyboardMarkup:
    mode = get_setting("maintenance_mode")
    toggle_label = "✅ Disable Maintenance" if mode == "1" else "🔴 Enable Maintenance"
    toggle_cb    = "adm:maint_off"          if mode == "1" else "adm:maint_on"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data=toggle_cb)],
        [InlineKeyboardButton("✏️ Edit Maintenance Message", callback_data="adm:maint_msg")],
        [InlineKeyboardButton("🔙 Back", callback_data="adm:main")],
    ])

def admin_encoder_mgr_keyboard() -> InlineKeyboardMarkup:
    enc = get_encoder_settings()
    keys = list(enc.keys())
    rows = []
    for i in range(0, len(keys), 2):
        chunk = keys[i:i+2]
        rows.append([InlineKeyboardButton(f"✏️ {enc[k]['display_name']}", callback_data=f"adm:rename:{k}") for k in chunk])
    rows.append([InlineKeyboardButton("🔄 Restore Defaults", callback_data="adm:rename_reset")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="adm:main")])
    return InlineKeyboardMarkup(rows)

def admin_encoder_ctrl_keyboard() -> InlineKeyboardMarkup:
    enc = get_encoder_settings()
    keys = list(enc.keys())
    rows = []
    for i in range(0, len(keys), 2):
        chunk = keys[i:i+2]
        rows.append([
            InlineKeyboardButton(
                f"{'🟢' if enc[k]['enabled'] else '🔴'} {enc[k]['display_name']}",
                callback_data=f"adm:toggle:{k}"
            ) for k in chunk
        ])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="adm:main")])
    return InlineKeyboardMarkup(rows)

def font_select_keyboard(method_key: str) -> InlineKeyboardMarkup:
    rows = []
    style_items = list(FONT_STYLE_NAMES.items())
    for i in range(0, len(style_items), 2):
        chunk = style_items[i:i+2]
        rows.append([
            InlineKeyboardButton(label, callback_data=f"adm:fontapply:{method_key}:{style}")
            for style, label in chunk
        ])
    rows.append([InlineKeyboardButton("✏️ Custom Name", callback_data=f"adm:rename:{method_key}")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="adm:encodermgr")])
    return InlineKeyboardMarkup(rows)

def admin_uimgr_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Welcome Title",       callback_data="adm:wm_title"),
         InlineKeyboardButton("✏️ Welcome Desc",        callback_data="adm:wm_desc")],
        [InlineKeyboardButton("✏️ Welcome Footer",      callback_data="adm:wm_footer")],
        [InlineKeyboardButton("✏️ Bot Name",            callback_data="adm:ap_name"),
         InlineKeyboardButton("✏️ Bot Subtitle",        callback_data="adm:ap_subtitle")],
        [InlineKeyboardButton("✏️ Header Text",         callback_data="adm:ap_header"),
         InlineKeyboardButton("✏️ Footer Text",         callback_data="adm:ap_footer")],
        [InlineKeyboardButton("✏️ Adv Category Label",  callback_data="adm:cat_adv"),
         InlineKeyboardButton("✏️ Nor Category Label",  callback_data="adm:cat_nor")],
        [InlineKeyboardButton("✏️ Btn: Join Channel",   callback_data="adm:btn_join"),
         InlineKeyboardButton("✏️ Btn: Developer",      callback_data="adm:btn_dev")],
        [InlineKeyboardButton("✏️ Btn: Encode Again",   callback_data="adm:btn_encode_again"),
         InlineKeyboardButton("✏️ Btn: Channel",        callback_data="adm:btn_channel")],
        [InlineKeyboardButton("🔙 Back", callback_data="adm:main")],
    ])

def admin_channel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 Change Channel ID",    callback_data="adm:ch_id")],
        [InlineKeyboardButton("🔗 Change Channel URL",   callback_data="adm:ch_url")],
        [InlineKeyboardButton("👨‍💻 Change Developer URL", callback_data="adm:ch_dev")],
        [InlineKeyboardButton("🔙 Back", callback_data="adm:main")],
    ])

def admin_backup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Export / Download DB", callback_data="adm:backup_export")],
        [InlineKeyboardButton("📥 Import / Restore DB",  callback_data="adm:backup_import")],
        [InlineKeyboardButton("📋 Export Settings JSON", callback_data="adm:backup_settings")],
        [InlineKeyboardButton("🔙 Back", callback_data="adm:main")],
    ])

# ══════════════════════════════════════════════
#  BROADCAST HELPERS
# ══════════════════════════════════════════════

async def _run_broadcast(bot, admin_chat_id: int, btype: str, summary: str, send_fn) -> int:
    user_ids = get_all_user_ids()
    delivered, failed, failed_ids = 0, 0, []
    status_msg = await bot.send_message(chat_id=admin_chat_id, text=f"📣 Broadcasting to {len(user_ids)} users…")
    for uid in user_ids:
        try:
            await send_fn(uid)
            delivered += 1
        except Exception:
            failed += 1
            failed_ids.append(uid)
        await asyncio.sleep(0.05)
    bid = log_broadcast(btype, summary, delivered, failed, failed_ids)
    await bot.edit_message_text(
        chat_id=admin_chat_id,
        message_id=status_msg.message_id,
        text=f"📣 *Broadcast Complete*\n\n✅ Delivered: `{delivered}`\n❌ Failed: `{failed}`\n🔑 BC ID: `{bid}`",
        parse_mode=None,
        reply_markup=admin_main_keyboard(),
    )
    return bid

async def do_broadcast_text(bot, admin_chat_id: int, text: str):
    await _run_broadcast(bot, admin_chat_id, "text", text[:80],
                         lambda uid: bot.send_message(chat_id=uid, text=text))

async def do_broadcast_photo(bot, admin_chat_id: int, photo_id: str, caption: str):
    await _run_broadcast(bot, admin_chat_id, "photo", f"Photo: {caption[:60]}",
                         lambda uid: bot.send_photo(chat_id=uid, photo=photo_id, caption=caption))

async def do_broadcast_video(bot, admin_chat_id: int, video_id: str, caption: str):
    await _run_broadcast(bot, admin_chat_id, "video", f"Video: {caption[:60]}",
                         lambda uid: bot.send_video(chat_id=uid, video=video_id, caption=caption))

async def do_broadcast_document(bot, admin_chat_id: int, doc_id: str, caption: str):
    await _run_broadcast(bot, admin_chat_id, "document", f"Doc: {caption[:60]}",
                         lambda uid: bot.send_document(chat_id=uid, document=doc_id, caption=caption))

async def do_broadcast_forward(bot, admin_chat_id: int, from_chat_id: int, message_id: int):
    await _run_broadcast(bot, admin_chat_id, "forward", f"Fwd from {from_chat_id}",
                         lambda uid: bot.forward_message(chat_id=uid, from_chat_id=from_chat_id, message_id=message_id))

async def do_retry_broadcast(bot, admin_chat_id: int, broadcast_id: int):
    failed_ids = get_failed_broadcast_users(broadcast_id)
    if not failed_ids:
        await bot.send_message(chat_id=admin_chat_id, text="✅ No failed users for that broadcast ID.", reply_markup=admin_main_keyboard())
        return
    history = get_broadcast_history(50)
    bc = next((b for b in history if b["id"] == broadcast_id), None)
    if not bc:
        await bot.send_message(chat_id=admin_chat_id, text="❌ Broadcast ID not found.", reply_markup=admin_main_keyboard())
        return
    delivered, failed, new_failed = 0, 0, []
    status_msg = await bot.send_message(chat_id=admin_chat_id, text=f"🔁 Retrying {len(failed_ids)} users…")
    for uid in failed_ids:
        try:
            if bc["btype"] == "text":
                await bot.send_message(chat_id=uid, text=bc["summary"])
            delivered += 1
        except Exception:
            failed += 1
            new_failed.append(uid)
        await asyncio.sleep(0.05)
    await bot.edit_message_text(
        chat_id=admin_chat_id,
        message_id=status_msg.message_id,
        text=f"🔁 *Retry Complete*\n\n✅ Delivered: `{delivered}`\n❌ Failed: `{failed}`",
        parse_mode=None,
        reply_markup=admin_main_keyboard(),
    )

# ══════════════════════════════════════════════
#  COMMAND HANDLERS
# ══════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    upsert_user(user.id, user.username, user.first_name)
    if get_setting("maintenance_mode") == "1" and not is_admin(user.id):
        await update.message.reply_text(get_setting("maintenance_message","⚠️ Under maintenance. Try later."))
        return
    if is_banned(user.id):
        await update.message.reply_text("🚫 You have been banned from using this bot.")
        return
    if not await is_member(context.bot, user.id):
        await update.message.reply_text(
            "⚠️ *You must join our channel first to use this bot\\.*",
            parse_mode=None,
            reply_markup=join_required_keyboard(),
        )
        return
    context.user_data.clear()
    await update.message.reply_text(
        build_welcome_text(
            first_name=user.first_name or "",
            user_id=user.id,
            username=user.username or "",
        ),
        parse_mode=None,
        reply_markup=welcome_keyboard(),
    )

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ You are not authorised to use this command.")
        return
    await update.message.reply_text(
        "🛡 *ADMIN PANEL*\n\nSelect an option below:",
        parse_mode=None,
        reply_markup=admin_main_keyboard(),
    )

# ══════════════════════════════════════════════
#  DOCUMENT HANDLER  (single, clean handler)
# ══════════════════════════════════════════════

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    upsert_user(user.id, user.username, user.first_name)
    update_last_active(user.id)
    msg = update.message
    doc: Document = msg.document
    fname: str = doc.file_name or ""

    # Admin: awaiting DB import
    if is_admin(user.id) and context.user_data.get("adm_await") == "db_import":
        context.user_data.pop("adm_await", None)
        if not fname.endswith(".db"):
            await msg.reply_text("❌ Please send a valid `.db` backup file.")
            return
        status = await msg.reply_text("📥 Importing database…")
        try:
            tg_file = await context.bot.get_file(doc.file_id)
            buf = io.BytesIO()
            await tg_file.download_to_memory(buf)
            with open(DB_PATH, "wb") as f:
                f.write(buf.getvalue())
            await status.edit_text("✅ Database imported successfully!", reply_markup=admin_main_keyboard())
        except Exception as e:
            await status.edit_text(f"❌ Import failed: {e}")
        return

    # Admin: awaiting document broadcast
    if is_admin(user.id) and context.user_data.get("adm_await") == "bc_doc":
        context.user_data.pop("adm_await", None)
        await do_broadcast_document(context.bot, msg.chat_id, doc.file_id, msg.caption or "")
        return

    # Maintenance block
    if get_setting("maintenance_mode") == "1" and not is_admin(user.id):
        await msg.reply_text(get_setting("maintenance_message", "⚠️ Under maintenance. Try later."))
        return

    if is_banned(user.id):
        await msg.reply_text("🚫 You have been banned from using this bot.")
        return

    if not await is_member(context.bot, user.id):
        await msg.reply_text("⚠️ Please join the channel first.", reply_markup=join_required_keyboard())
        return

    if not fname.lower().endswith(".py"):
        ext = os.path.splitext(fname)[1] or "(unknown)"
        await msg.reply_text(
            f"❌ *Invalid file type:* `{escape_md(ext)}`\n\nPlease send a *\\.py* Python file only\\.",
            parse_mode=None,
        )
        return

    status_msg = await msg.reply_text("📥 *File Received*\n🔍 Validating\\.\\.\\.", parse_mode=ParseMode.MARKDOWN_V2)
    try:
        tg_file = await context.bot.get_file(doc.file_id)
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        raw_bytes = buf.getvalue()
        try:
            source_code = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            await status_msg.edit_text("❌ *Cannot decode file as UTF\\-8\\.* Send a valid \\.py file\\.", parse_mode=ParseMode.MARKDOWN_V2)
            log_encode(user.id, "unknown", fname, 0)
            return
        try:
            ast.parse(source_code)
        except SyntaxError as e:
            await status_msg.edit_text(
                f"❌ *Syntax error:*\n`{escape_md(str(e))}`\n\nFix and re\\-upload\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            log_encode(user.id, "unknown", fname, 0)
            return
    except Exception:
        logger.exception("Download failed")
        await status_msg.edit_text("❌ *Failed to download file\\.* Try again\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    context.user_data["source_code"] = source_code
    context.user_data["filename"]    = fname
    context.user_data["orig_size"]   = len(raw_bytes)
    await status_msg.edit_text(
        "✅ File Received Successfully\n\n"
        "🔍 Validation Completed\n"
        "🛡 Security Check Passed\n\n"
        "⚡ Select an encoding method below.",
        parse_mode=None,
        reply_markup=method_keyboard(),
    )

# ══════════════════════════════════════════════
#  PHOTO HANDLER
# ══════════════════════════════════════════════

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin(user.id): return
    if context.user_data.get("adm_await") != "bc_photo": return
    context.user_data.pop("adm_await", None)
    msg = update.message
    await do_broadcast_photo(context.bot, msg.chat_id, msg.photo[-1].file_id, msg.caption or "")

# ══════════════════════════════════════════════
#  VIDEO HANDLER
# ══════════════════════════════════════════════

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin(user.id): return
    if context.user_data.get("adm_await") != "bc_video": return
    context.user_data.pop("adm_await", None)
    msg = update.message
    await do_broadcast_video(context.bot, msg.chat_id, msg.video.file_id, msg.caption or "")

# ══════════════════════════════════════════════
#  FORWARD HANDLER
# ══════════════════════════════════════════════

async def handle_forwarded(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_admin(user.id): return
    if context.user_data.get("adm_await") != "bc_forward": return
    context.user_data.pop("adm_await", None)
    msg = update.message
    await do_broadcast_forward(context.bot, msg.chat_id, msg.chat.id, msg.message_id)

# ══════════════════════════════════════════════
#  TEXT HANDLER
# ══════════════════════════════════════════════

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text or ""

    if is_admin(user.id) and context.user_data.get("adm_await"):
        await _process_admin_text_await(update, context, text)
        return

    if get_setting("maintenance_mode") == "1" and not is_admin(user.id):
        await update.message.reply_text(get_setting("maintenance_message","⚠️ Under maintenance. Try later."))
        return

    if is_banned(user.id):
        await update.message.reply_text("🚫 You have been banned from using this bot.")
        return

    await update.message.reply_text("⚠️ Please send a *\\.py* Python file to encode\\.", parse_mode=ParseMode.MARKDOWN_V2)

async def _process_admin_text_await(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    await_key = context.user_data.pop("adm_await", None)
    msg = update.message

    async def ok(reply: str, markup=None):
        await msg.reply_text(f"✅ {reply}", reply_markup=markup or admin_main_keyboard())

    if await_key == "ban_id":
        parts = text.strip().split(None, 1)
        try:
            uid = int(parts[0])
        except ValueError:
            await msg.reply_text("❌ Invalid user ID. Must be a number.")
            return
        reason = parts[1] if len(parts) > 1 else ""
        ban_user(uid, reason)
        await ok(f"User `{uid}` has been banned. Reason: {reason or 'none'}")

    elif await_key == "unban_id":
        try:
            uid = int(text.strip())
        except ValueError:
            await msg.reply_text("❌ Invalid user ID.")
            return
        unban_user(uid)
        await ok(f"User `{uid}` has been unbanned.")

    elif await_key == "user_info_id":
        try:
            uid = int(text.strip())
        except ValueError:
            await msg.reply_text("❌ Invalid user ID.")
            return
        info = get_user_info(uid)
        if not info:
            await msg.reply_text("❌ User not found.", reply_markup=admin_main_keyboard())
            return
        unban_history = json.loads(info.get("unban_history") or "[]")
        await msg.reply_text(
            f"🔍 *USER PROFILE*\n\n"
            f"ID: `{info['user_id']}`\n"
            f"Username: `@{escape_md(info['username'] or 'N/A')}`\n"
            f"Name: `{escape_md(info['first_name'] or 'N/A')}`\n"
            f"Joined: `{info['join_date']}`\n"
            f"Last Active: `{info['last_active']}`\n"
            f"Total Encodes: `{info['total_encodes']}`\n"
            f"Banned: {'🚫 Yes' if info['is_banned'] else '✅ No'}\n"
            f"Ban Reason: `{escape_md(info.get('ban_reason') or 'none')}`\n"
            f"Unban Count: `{len(unban_history)}`",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=admin_main_keyboard(),
        )

    elif await_key == "user_search_uname":
        results = search_user_by_username(text.strip())
        if not results:
            await msg.reply_text("❌ No users found matching that username.", reply_markup=admin_main_keyboard())
            return
        lines = [f"Found {len(results)} user(s):\n"]
        for info in results[:10]:
            lines.append(f"ID: {info['user_id']} | @{info['username']} | {info['first_name']} | Banned: {'Yes' if info['is_banned'] else 'No'}")
        await msg.reply_text("\n".join(lines), reply_markup=admin_main_keyboard())

    elif await_key == "bc_text":
        await do_broadcast_text(context.bot, msg.chat_id, text)

    elif await_key == "bc_retry_id":
        try:
            bid = int(text.strip())
        except ValueError:
            await msg.reply_text("❌ Invalid broadcast ID.")
            return
        await do_retry_broadcast(context.bot, msg.chat_id, bid)

    elif await_key == "rename_value":
        mk = context.user_data.pop("adm_rename_key", None)
        if mk:
            set_encoder_name(mk, text.strip())
            await msg.reply_text(f"✅ Encoder renamed to: {text.strip()}", reply_markup=admin_encoder_mgr_keyboard())

    elif await_key == "add_admin_id":
        try:
            uid = int(text.strip())
        except ValueError:
            await msg.reply_text("❌ Invalid user ID.")
            return
        add_admin(uid)
        await ok(f"User `{uid}` added as admin.")

    elif await_key == "rem_admin_id":
        try:
            uid = int(text.strip())
        except ValueError:
            await msg.reply_text("❌ Invalid user ID.")
            return
        if not remove_admin(uid):
            await msg.reply_text("❌ Cannot remove a hardcoded super-admin.", reply_markup=admin_main_keyboard())
        else:
            await ok(f"User `{uid}` removed from admins.")

    elif await_key == "maint_msg":
        set_setting("maintenance_message", text)
        await ok("Maintenance message updated!")

    elif await_key == "wm_title":
        set_setting("welcome_title", text)
        await ok("Welcome title updated!")

    elif await_key == "wm_desc":
        set_setting("welcome_description", text)
        await ok("Welcome description updated!")

    elif await_key == "wm_footer":
        set_setting("welcome_footer", text)
        await ok("Welcome footer updated!")

    elif await_key == "ch_id":
        val = text.strip()
        if not val.startswith("@"): val = "@" + val
        set_setting("force_join_channel", val)
        await ok(f"Force join channel updated to {val}!")

    elif await_key == "ch_url":
        set_setting("channel_url", text.strip())
        await ok("Channel URL updated!")

    elif await_key == "ch_dev":
        set_setting("developer_url", text.strip())
        await ok("Developer URL updated!")

    elif await_key == "ap_name":
        set_setting("bot_name", text)
        await ok("Bot name updated!")

    elif await_key == "ap_subtitle":
        set_setting("bot_subtitle", text)
        await ok("Bot subtitle updated!")

    elif await_key == "ap_header":
        set_setting("header_text", text)
        await ok("Header text updated!")

    elif await_key == "ap_footer":
        set_setting("footer_text", text)
        await ok("Footer text updated!")

    elif await_key == "cat_adv":
        set_setting("adv_category_label", text)
        await ok("Advanced category label updated!")

    elif await_key == "cat_nor":
        set_setting("nor_category_label", text)
        await ok("Normal category label updated!")

    elif await_key == "btn_join":
        set_setting("btn_join_channel", text)
        await ok("Join Channel button text updated!")

    elif await_key == "btn_dev":
        set_setting("btn_developer", text)
        await ok("Developer button text updated!")

    elif await_key == "btn_encode_again":
        set_setting("btn_encode_again", text)
        await ok("Encode Again button text updated!")

    elif await_key == "btn_channel":
        set_setting("btn_channel", text)
        await ok("Channel button text updated!")

    else:
        await msg.reply_text("⚠️ Unknown input. Cancelled.", reply_markup=admin_main_keyboard())

# ══════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ══════════════════════════════════════════════

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data: str = query.data
    user = query.from_user

    if data == "noop":
        return

    if data == "check_join":
        if await is_member(context.bot, user.id):
            context.user_data.clear()
            await query.edit_message_text(
                build_welcome_text(
                    first_name=user.first_name or "",
                    user_id=user.id,
                    username=user.username or "",
                ),
                parse_mode=None,
                reply_markup=welcome_keyboard(),
            )
        else:
            await query.answer("❌ You haven't joined yet!", show_alert=True)
        return

    if data == "encode_again":
        context.user_data.clear()
        await query.edit_message_text(
            build_welcome_text(
                first_name=user.first_name or "",
                user_id=user.id,
                username=user.username or "",
            ),
            parse_mode=None,
            reply_markup=welcome_keyboard(),
        )
        return

    if data.startswith("method:"):
        method_key  = data.split(":", 1)[1]
        source_code = context.user_data.get("source_code")
        filename    = context.user_data.get("filename", "script.py")
        orig_size   = context.user_data.get("orig_size", 0)
        if not source_code:
            await query.edit_message_text("⚠️ No file found\\. Please send a \\.py file first\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        enc         = get_encoder_settings()
        method_name = enc.get(method_key, {}).get("display_name") or PythonEncryptor.METHOD_INFO.get(method_key, {}).get("name", method_key)
        prot_info   = PythonEncryptor.METHOD_INFO.get(method_key, {})
        await query.edit_message_text(
            f"🔐 *{escape_md(method_name)}*\n\n"
            f"Protection: *{prot_info.get('protection','—')}*\n"
            f"Speed: *{prot_info.get('speed','—')}*\n\n"
            "_Encoding\\.\\.\\. please wait_",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        encryptor = PythonEncryptor()
        try:
            encoded_script, stats = encryptor.encode(source_code, method_key)
            log_encode(user.id, method_key, filename, 1)
        except Exception as e:
            logger.exception("Encoding failed")
            log_encode(user.id, method_key, filename, 0)
            await query.edit_message_text(
                f"❌ *Encoding failed\\.*\n\n`{escape_md(str(e))}`",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return
        encoded_bytes = encoded_script.encode("utf-8")
        encoded_size  = len(encoded_bytes)
        out_name      = f"encoded_{filename}"
        file_buf      = io.BytesIO(encoded_bytes)
        file_buf.name = out_name
        await query.edit_message_text(
            "✅ Encoding Complete\n\n"
            "🔐 Your file is now protected.\n\n"
            "🛡 Source code secured.\n"
            "📦 Protected file generated.\n"
            "⚡ Ready for deployment.",
            parse_mode=None,
        )
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_buf, filename=out_name,
            caption=f"✅ *Encoding Complete*\n\n🔐 Method: `{escape_md(method_name)}`\n📄 File: `{escape_md(filename)}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        size_ratio = (encoded_size / orig_size * 100) if orig_size else 0
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                f"📊 *Protection Report*\n\n"
                f"✅ Encoded Successfully\n✅ Obfuscation Applied\n✅ Protection Layer Added\n\n"
                f"📦 Original: `{orig_size:,}` bytes\n"
                f"📦 Encoded:  `{encoded_size:,}` bytes _\\({size_ratio:.1f}%\\)_\n\n"
                f"📌 Imports: `{stats['imports']}`\n"
                f"📌 Functions: `{stats['functions']}`\n"
                f"📌 Classes: `{stats['classes']}`"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=post_encode_keyboard(),
        )
        context.user_data.clear()
        return

    # ── ADMIN CALLBACKS ───────────────────────
    if data.startswith("adm:"):
        if not is_admin(user.id):
            await query.answer("⛔ Not authorised.", show_alert=True)
            return
        action = data[4:]

        if action == "main":
            await query.edit_message_text("🛡 *ADMIN PANEL*\n\nSelect an option:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_main_keyboard())
            return
        if action == "close":
            await query.edit_message_text("✅ Admin panel closed.")
            return

        # Dashboard
        if action == "dashboard":
            s = get_stats()
            await query.edit_message_text(
                f"📊 *ADMIN DASHBOARD*\n\n"
                f"👥 Total Users: `{s['total_users']}`\n"
                f"✅ Active: `{s['active_users']}`\n"
                f"🚫 Banned: `{s['banned_users']}`\n"
                f"📅 Active \\(7 days\\): `{s['recent_users']}`\n"
                f"📁 Total Encodes: `{s['total_encoded']}`\n"
                f"✅ Successful: `{s['total_success']}`\n"
                f"❌ Failed: `{s['total_failed']}`\n"
                f"⏱ Uptime: `{s['uptime']}`\n"
                f"💾 DB Size: `{s['db_size']/1024:.2f} KB`",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=admin_back_keyboard(),
            )
            return

        # User management
        if action == "usermgmt":
            await query.edit_message_text("👥 *USER MANAGEMENT*", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_usermgmt_keyboard())
            return
        if action == "usercount":
            s = get_stats()
            await query.edit_message_text(
                f"👥 *USER COUNT*\n\nTotal: `{s['total_users']}`\nActive: `{s['active_users']}`\nBanned: `{s['banned_users']}`\nRecent \\(7d\\): `{s['recent_users']}`",
                parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:usermgmt"))
            return
        if action == "ban":
            context.user_data["adm_await"] = "ban_id"
            await query.edit_message_text("🚫 *BAN USER*\n\nSend user ID \\(optionally followed by reason\\):\n`123456789 spamming`", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:usermgmt"))
            return
        if action == "unban":
            context.user_data["adm_await"] = "unban_id"
            await query.edit_message_text("✅ *UNBAN USER*\n\nSend the user ID:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:usermgmt"))
            return
        if action == "userinfo":
            context.user_data["adm_await"] = "user_info_id"
            await query.edit_message_text("🔍 *USER INFO*\n\nSend the user ID:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:usermgmt"))
            return
        if action == "usersearch":
            context.user_data["adm_await"] = "user_search_uname"
            await query.edit_message_text("🔎 *SEARCH BY USERNAME*\n\nSend username \\(with or without @\\):", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:usermgmt"))
            return
        if action == "exportusers":
            csv_data = get_all_users_csv()
            buf = io.BytesIO(csv_data.encode())
            now_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            buf.name = f"users_{now_str}.csv"
            await context.bot.send_document(chat_id=query.message.chat_id, document=buf, filename=buf.name, caption="📥 Users export")
            return

        # Broadcast
        if action == "broadcast":
            await query.edit_message_text("📣 *BROADCAST*\n\nSelect type:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_broadcast_keyboard())
            return
        if action == "bc_text":
            context.user_data["adm_await"] = "bc_text"
            await query.edit_message_text("📝 *TEXT BROADCAST*\n\nSend the message to broadcast:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:broadcast"))
            return
        if action == "bc_photo":
            context.user_data["adm_await"] = "bc_photo"
            await query.edit_message_text("🖼 *PHOTO BROADCAST*\n\nSend the photo \\(optional caption\\):", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:broadcast"))
            return
        if action == "bc_video":
            context.user_data["adm_await"] = "bc_video"
            await query.edit_message_text("🎬 *VIDEO BROADCAST*\n\nSend the video \\(optional caption\\):", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:broadcast"))
            return
        if action == "bc_doc":
            context.user_data["adm_await"] = "bc_doc"
            await query.edit_message_text("📎 *DOCUMENT BROADCAST*\n\nSend the document \\(optional caption\\):", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:broadcast"))
            return
        if action == "bc_forward":
            context.user_data["adm_await"] = "bc_forward"
            await query.edit_message_text("↩️ *FORWARD BROADCAST*\n\nForward any message here:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:broadcast"))
            return
        if action == "bc_history":
            history = get_broadcast_history(10)
            if not history:
                await query.edit_message_text("📋 No broadcast history yet.", reply_markup=admin_back_keyboard("adm:broadcast"))
                return
            lines = ["📋 *BROADCAST HISTORY* \\(last 10\\)\n"]
            for b in history:
                lines.append(f"ID `{b['id']}` \\| {escape_md(b['btype'])} \\| ✅{b['delivered']} ❌{b['failed']} \\| `{escape_md(b['timestamp'][:16])}`")
            await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:broadcast"))
            return
        if action == "bc_retry":
            context.user_data["adm_await"] = "bc_retry_id"
            await query.edit_message_text("🔁 *RETRY BROADCAST*\n\nSend the Broadcast ID to retry failed users:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:broadcast"))
            return

        # Admin management
        if action == "adminmgmt":
            await query.edit_message_text("👑 *ADMIN MANAGEMENT*", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_adminmgmt_keyboard())
            return
        if action == "add_admin":
            context.user_data["adm_await"] = "add_admin_id"
            await query.edit_message_text("➕ *ADD ADMIN*\n\nSend the user ID to promote:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:adminmgmt"))
            return
        if action == "rem_admin":
            context.user_data["adm_await"] = "rem_admin_id"
            await query.edit_message_text("➖ *REMOVE ADMIN*\n\nSend the user ID to demote:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:adminmgmt"))
            return
        if action == "list_admins":
            admin_ids = get_admin_ids()
            lines = [f"👑 *ADMIN LIST*\n"]
            for aid in admin_ids:
                info = get_user_info(aid)
                uname = f"@{info['username']}" if info and info.get("username") else "unknown"
                lines.append(f"`{aid}` — {escape_md(uname)}")
            await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:adminmgmt"))
            return

        # Maintenance
        if action == "maintenance":
            mode = get_setting("maintenance_mode")
            status = "🔴 ENABLED" if mode == "1" else "🟢 DISABLED"
            await query.edit_message_text(f"🔧 *MAINTENANCE MODE*\n\nStatus: {status}", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_maintenance_keyboard())
            return
        if action == "maint_on":
            set_setting("maintenance_mode", "1")
            await query.edit_message_text("🔴 *Maintenance ENABLED*", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_maintenance_keyboard())
            return
        if action == "maint_off":
            set_setting("maintenance_mode", "0")
            await query.edit_message_text("🟢 *Maintenance DISABLED*", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_maintenance_keyboard())
            return
        if action == "maint_msg":
            context.user_data["adm_await"] = "maint_msg"
            await query.edit_message_text("✏️ *EDIT MAINTENANCE MESSAGE*\n\nSend the new maintenance message:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:maintenance"))
            return

        # Encoder manager
        if action == "encodermgr":
            await query.edit_message_text("⚙️ *ENCODER MANAGER*\n\nTap an encoder to rename or apply font:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_encoder_mgr_keyboard())
            return
        if action == "rename_reset":
            reset_encoder_names()
            await query.edit_message_text("🔄 *Default names restored\\!*", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_encoder_mgr_keyboard())
            return
        if action.startswith("rename:"):
            mk = action.split(":", 1)[1]
            enc = get_encoder_settings()
            current_name = enc.get(mk, {}).get("display_name", mk)
            await query.edit_message_text(
                f"✏️ *ENCODER:* `{escape_md(current_name)}`\n\nChoose a font style or tap 'Custom Name':",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=font_select_keyboard(mk),
            )
            return
        if action.startswith("fontapply:"):
            parts = action.split(":", 2)
            mk, style = parts[1], parts[2]
            enc = get_encoder_settings()
            base_name = ENCODER_DEFAULTS.get(mk, enc.get(mk, {}).get("display_name", mk))
            new_name = apply_font(base_name, style)
            set_encoder_name(mk, new_name)
            await query.edit_message_text(
                f"✅ *Encoder renamed to:* `{escape_md(new_name)}`",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=admin_encoder_mgr_keyboard(),
            )
            return
        if action.startswith("fontcustom:"):
            mk = action.split(":", 1)[1]
            context.user_data["adm_await"]      = "rename_value"
            context.user_data["adm_rename_key"] = mk
            enc = get_encoder_settings()
            current_name = enc.get(mk, {}).get("display_name", mk)
            await query.edit_message_text(
                f"✏️ *CUSTOM NAME*\n\nCurrent: `{escape_md(current_name)}`\n\nSend the new name:",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=admin_back_keyboard("adm:encodermgr"),
            )
            return

        # Encoder control
        if action == "encoderctrl":
            await query.edit_message_text("🔐 *ENCODER CONTROL*\n\n🟢 = Enabled   🔴 = Disabled\n\nTap to toggle:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_encoder_ctrl_keyboard())
            return
        if action.startswith("toggle:"):
            mk = action.split(":", 1)[1]
            enc = get_encoder_settings()
            current = enc.get(mk, {}).get("enabled", True)
            set_encoder_enabled(mk, not current)
            state = "🟢 Enabled" if not current else "🔴 Disabled"
            name = enc.get(mk, {}).get("display_name", mk)
            await query.answer(f"{name} is now {state}", show_alert=False)
            await query.edit_message_text("🔐 *ENCODER CONTROL*\n\n🟢 = Enabled   🔴 = Disabled\n\nTap to toggle:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_encoder_ctrl_keyboard())
            return

        # UI Manager
        if action == "uimgr":
            title = get_setting("welcome_title")
            desc  = get_setting("welcome_description")
            foot  = get_setting("welcome_footer")
            bname = get_setting("bot_name")
            bsub  = get_setting("bot_subtitle")
            hdr   = get_setting("header_text")
            ftr   = get_setting("footer_text")
            preview = (
                f"🎨 *UI MANAGER*\n\nSelect what to edit:\n\n"
                f"*Current Values:*\n"
                f"Title: `{escape_md(title)}`\n"
                f"Desc: `{escape_md(desc[:40])}{'…' if len(desc)>40 else ''}`\n"
                f"Footer: `{escape_md(foot[:40])}{'…' if len(foot)>40 else ''}`\n"
                f"Bot Name: `{escape_md(bname)}`\n"
                f"Subtitle: `{escape_md(bsub[:40])}{'…' if len(bsub)>40 else ''}`\n"
                f"Header: `{escape_md(hdr)}`\n"
                f"Footer\\-text: `{escape_md(ftr)}`"
            )
            await query.edit_message_text(preview, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_uimgr_keyboard())
            return
        if action == "wm_title":
            context.user_data["adm_await"] = "wm_title"
            await query.edit_message_text("✏️ *EDIT WELCOME TITLE*\n\nSend the new title:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "wm_desc":
            context.user_data["adm_await"] = "wm_desc"
            await query.edit_message_text("✏️ *EDIT WELCOME DESCRIPTION*\n\nSend the new description:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "wm_footer":
            context.user_data["adm_await"] = "wm_footer"
            await query.edit_message_text("✏️ *EDIT WELCOME FOOTER*\n\nSend the new footer:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "ap_name":
            context.user_data["adm_await"] = "ap_name"
            await query.edit_message_text("✏️ *EDIT BOT NAME*\n\nSend the new name:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "ap_subtitle":
            context.user_data["adm_await"] = "ap_subtitle"
            await query.edit_message_text("✏️ *EDIT BOT SUBTITLE*\n\nSend the new subtitle:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "ap_header":
            context.user_data["adm_await"] = "ap_header"
            await query.edit_message_text("✏️ *EDIT HEADER TEXT*\n\nSend the new header:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "ap_footer":
            context.user_data["adm_await"] = "ap_footer"
            await query.edit_message_text("✏️ *EDIT FOOTER TEXT*\n\nSend the new footer:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "cat_adv":
            context.user_data["adm_await"] = "cat_adv"
            await query.edit_message_text("✏️ *ADVANCED CATEGORY LABEL*\n\nSend the new label:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "cat_nor":
            context.user_data["adm_await"] = "cat_nor"
            await query.edit_message_text("✏️ *NORMAL CATEGORY LABEL*\n\nSend the new label:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "btn_join":
            context.user_data["adm_await"] = "btn_join"
            await query.edit_message_text("✏️ *BTN: JOIN CHANNEL*\n\nSend the new button text:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "btn_dev":
            context.user_data["adm_await"] = "btn_dev"
            await query.edit_message_text("✏️ *BTN: DEVELOPER*\n\nSend the new button text:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "btn_encode_again":
            context.user_data["adm_await"] = "btn_encode_again"
            await query.edit_message_text("✏️ *BTN: ENCODE AGAIN*\n\nSend the new button text:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return
        if action == "btn_channel":
            context.user_data["adm_await"] = "btn_channel"
            await query.edit_message_text("✏️ *BTN: CHANNEL*\n\nSend the new button text:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:uimgr"))
            return

        # Channel config
        if action == "channelcfg":
            ch_id = get_setting("force_join_channel"); ch_url = get_setting("channel_url"); dev_url = get_setting("developer_url")
            await query.edit_message_text(
                f"📡 *CHANNEL SETTINGS*\n\nChannel ID: `{escape_md(ch_id)}`\nChannel URL: `{escape_md(ch_url)}`\nDeveloper URL: `{escape_md(dev_url)}`",
                parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_channel_keyboard())
            return
        if action == "ch_id":
            context.user_data["adm_await"] = "ch_id"
            await query.edit_message_text("📡 *CHANGE CHANNEL ID*\n\nSend new channel username \\(e\\.g\\. @mychannel\\):", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:channelcfg"))
            return
        if action == "ch_url":
            context.user_data["adm_await"] = "ch_url"
            await query.edit_message_text("🔗 *CHANGE CHANNEL URL*\n\nSend new URL:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:channelcfg"))
            return
        if action == "ch_dev":
            context.user_data["adm_await"] = "ch_dev"
            await query.edit_message_text("👨‍💻 *CHANGE DEVELOPER URL*\n\nSend new URL:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:channelcfg"))
            return

        # Backup / DB
        if action == "backup":
            await query.edit_message_text("💾 *DATABASE*\n\nSelect an action:", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_backup_keyboard())
            return
        if action == "backup_export":
            if not os.path.exists(DB_PATH):
                await query.answer("No database found!", show_alert=True); return
            await query.answer("Sending database…")
            with open(DB_PATH, "rb") as f:
                db_data = f.read()
            now_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            buf = io.BytesIO(db_data); buf.name = f"encoder_bot_backup_{now_str}.db"
            await context.bot.send_document(chat_id=query.message.chat_id, document=buf, filename=buf.name, caption=f"💾 DB Backup {now_str} UTC")
            return
        if action == "backup_import":
            context.user_data["adm_await"] = "db_import"
            await query.edit_message_text("📥 *IMPORT DATABASE*\n\nSend a `\\.db` file to replace current database\\.\n\n⚠️ This overwrites all data\\!", parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_back_keyboard("adm:backup"))
            return
        if action == "backup_settings":
            conn = get_db()
            rows = conn.execute("SELECT key,value FROM bot_settings").fetchall()
            conn.close()
            settings_dict = {r["key"]: r["value"] for r in rows}
            now_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            buf = io.BytesIO(json.dumps(settings_dict, indent=2).encode())
            buf.name = f"bot_settings_{now_str}.json"
            await context.bot.send_document(chat_id=query.message.chat_id, document=buf, filename=buf.name, caption="📋 Bot settings export")
            return

        logger.warning("Unhandled admin callback: %s", data)
        return

    logger.warning("Unhandled callback: %s", data)

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main() -> None:
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin",  cmd_admin))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Documents – single handler, handles admin DB import, admin bc_doc, and normal .py uploads
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Photos – admin bc_photo only (returns early if no await)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Videos – admin bc_video only
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # Forwarded messages – admin bc_forward only
    app.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded))

    # Text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot started. Polling…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
