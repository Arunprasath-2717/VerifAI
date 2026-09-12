import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent.parent / "verifai.db"

_db_initialized = False

def get_db_connection():
    global _db_initialized
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if not _db_initialized:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verifications'")
        table_exists = cursor.fetchone()
        if not table_exists:
            init_db_with_conn(conn)
            from app.db.seed import seed_database
            seed_database()
        _db_initialized = True

    return conn

def init_db_with_conn(conn):
    cursor = conn.cursor()
    schema_path = Path(__file__).parent / "schema.sql"
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
    conn.commit()

def init_db():
    conn = get_db_connection()
    conn.close()
