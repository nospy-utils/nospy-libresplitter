import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "splitwise.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, autocommit=True)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT    NOT NULL,
                email     TEXT    NOT NULL UNIQUE,
                password  TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
