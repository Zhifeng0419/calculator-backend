"""SQLite database layer for calculation history persistence."""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

DB_PATH = os.environ.get("CALCULATOR_DB_PATH", os.path.join(os.path.dirname(__file__), "history.db"))

_schema = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expression TEXT NOT NULL,
    result TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'calculate',
    time TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_time ON history(time DESC);
"""

# Thread-local connection with a lock around schema init / writes.
_local = threading.local()
_init_lock = threading.Lock()
_initialized = False


def _connect() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _local.conn = conn
    return conn


def init_db() -> None:
    """Create the history table if it does not exist."""
    global _initialized
    with _init_lock:
        if _initialized:
            return
        conn = _connect()
        conn.executescript(_schema)
        conn.commit()
        _initialized = True


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a database connection, ensuring the schema is initialized."""
    if not _initialized:
        init_db()
    conn = _connect()
    try:
        yield conn
    finally:
        pass  # keep the connection open for the thread


def add_record(expression: str, result: str, record_type: str = "calculate") -> int:
    """Insert a new history record and return its id."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO history (expression, result, type, time) VALUES (?, ?, ?, ?)",
            (expression, result, record_type, now),
        )
        conn.commit()
        return cur.lastrowid


def get_records(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    record_type: str | None = None,
) -> dict:
    """Return a paginated list of history records (newest first)."""
    page = max(page, 1)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    clauses = []
    params: list = []
    if search:
        clauses.append("(expression LIKE ? OR result LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if record_type:
        clauses.append("type = ?")
        params.append(record_type)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""

    with get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM history{where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT id, expression, result, type, time FROM history{where} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()

    items = [
        {
            "id": row["id"],
            "expression": row["expression"],
            "result": row["result"],
            "type": row["type"],
            "time": row["time"],
        }
        for row in rows
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


def delete_record(record_id: int) -> bool:
    """Delete a single history record by id. Returns True if a row was deleted."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
        conn.commit()
        return cur.rowcount > 0


def clear_all_records() -> int:
    """Delete all history records. Returns the number of deleted rows."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM history")
        conn.commit()
        return cur.rowcount


def get_stats() -> dict:
    """Return simple statistics over the history table."""
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        row = conn.execute(
            "SELECT COUNT(DISTINCT type) FROM history"
        ).fetchone()
        type_count = row[0]
    return {"total_records": total, "distinct_types": type_count}
