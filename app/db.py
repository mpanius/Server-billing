from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS hosting_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    login TEXT DEFAULT '',
    auth_secret TEXT DEFAULT '',
    panel_url TEXT DEFAULT '',
    payment_url TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosting_account_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    ip_address TEXT DEFAULT '',
    service_id TEXT DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'RUB',
    billing_period_days INTEGER NOT NULL DEFAULT 30,
    next_payment_date TEXT NOT NULL,
    payment_url TEXT DEFAULT '',
    panel_url TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_paid_at TEXT DEFAULT '',
    FOREIGN KEY (hosting_account_id) REFERENCES hosting_accounts(id) ON DELETE SET NULL
);

CREATE TRIGGER IF NOT EXISTS hosting_accounts_updated_at
AFTER UPDATE ON hosting_accounts
FOR EACH ROW
BEGIN
    UPDATE hosting_accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS servers_updated_at
AFTER UPDATE ON servers
FOR EACH ROW
BEGIN
    UPDATE servers SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
"""


def ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def database_path() -> Path:
    return Path(settings.database_path).resolve()


def init_db() -> None:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        ensure_column(connection, "servers", "hosting_account_id", "INTEGER DEFAULT NULL")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    init_db()
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
