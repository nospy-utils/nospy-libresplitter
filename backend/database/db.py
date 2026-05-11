import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../volumes/database/splitwise.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "./schema.sql")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, autocommit=True)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript("".join(f.readlines()))
