import sqlite3, os
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def connect(admin_code):
    os.makedirs("data", exist_ok=True)
    path = f"data/{admin_code.lower()}.db"
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _init(conn, admin_code)
    return conn

def _init(conn, admin_code):
    from .config import TRADERS
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS traders (
            id TEXT PRIMARY KEY, name TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS declarations (
            ucr TEXT, kind TEXT, trader_id TEXT, hs_code TEXT,
            customs_value REAL, duty REAL, vat REAL, total REAL,
            status TEXT, details TEXT, created TEXT,
            PRIMARY KEY (ucr, kind)
        );
        CREATE TABLE IF NOT EXISTS payments (
            receipt TEXT PRIMARY KEY, ucr TEXT, amount REAL, method TEXT,
            duty_portion REAL, vat_portion REAL, created TEXT
        );
    ''')
    for tid, status in TRADERS.get(admin_code, {}).items():
        conn.execute(
            "INSERT OR IGNORE INTO traders VALUES (?,?,?)",
            (tid, tid, status),
        )
    conn.commit()