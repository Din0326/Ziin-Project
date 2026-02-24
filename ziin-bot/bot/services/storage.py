from __future__ import annotations

import logging
import os
import sqlite3
import time
from pathlib import Path
from threading import RLock
from typing import Any, Iterable, Optional

_conn: Optional[sqlite3.Connection] = None
_lock = RLock()
logger = logging.getLogger("__main__")
_DEBUG_SQL = os.getenv("DEBUG_SQL", "0") == "1"


def _debug_sql(message: str) -> None:
    if _DEBUG_SQL:
        logger.info("[storage] %s", message)


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _is_locked_error(exc: sqlite3.OperationalError) -> bool:
    return "database is locked" in str(exc).lower()


def _run_with_lock_retry(
    action,
    *,
    operation_name: str,
    max_attempts: int = 8,
    base_delay_seconds: float = 0.5,
):
    for attempt in range(1, max_attempts + 1):
        try:
            return action()
        except sqlite3.OperationalError as exc:
            if not _is_locked_error(exc) or attempt == max_attempts:
                raise
            delay = base_delay_seconds * attempt
            logger.warning(
                "SQLite locked during %s; retrying in %.1fs (%d/%d)",
                operation_name,
                delay,
                attempt,
                max_attempts,
            )
            time.sleep(delay)


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          name TEXT PRIMARY KEY,
          applied_at INTEGER NOT NULL
        )
        """
    )


def _is_sql_migration_already_satisfied(conn: sqlite3.Connection, migration_name: str) -> bool:
    if not migration_name.startswith("addcol__") or not migration_name.endswith(".sql"):
        return False
    parts = migration_name[:-4].split("__")
    if len(parts) != 3:
        return False
    _, table, column = parts
    return _column_exists(conn, table, column)


def _apply_sql_migrations(conn: sqlite3.Connection, migrations_dir: Path) -> None:
    _ensure_migrations_table(conn)
    if not migrations_dir.exists():
        _debug_sql(f"migrations dir not found: {migrations_dir}")
        return

    for migration_path in sorted(migrations_dir.glob("*.sql")):
        migration_name = migration_path.name
        _debug_sql(f"checking migration: {migration_name}")
        already_applied = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE name = ? LIMIT 1",
            (migration_name,),
        ).fetchone()
        if already_applied:
            _debug_sql(f"skip already applied: {migration_name}")
            continue

        if _is_sql_migration_already_satisfied(conn, migration_name):
            _debug_sql(f"mark satisfied by existing schema: {migration_name}")
            conn.execute(
                "INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)",
                (migration_name, now_ts()),
            )
            continue

        _debug_sql(f"apply migration: {migration_name}")
        conn.executescript(migration_path.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)",
            (migration_name, now_ts()),
        )


def init_storage(local_db_path: Optional[Path]) -> sqlite3.Connection:
    """Initialize shared SQLite connection once."""
    global _conn

    if _conn is not None:
        _debug_sql("reuse existing sqlite connection")
        return _conn

    base_dir = Path(__file__).resolve().parents[2]
    sqlite_path = local_db_path or Path(os.getenv("LOCAL_DB_PATH") or (base_dir / "data" / "local.db"))
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    _debug_sql(f"open sqlite path: {sqlite_path}")

    conn = sqlite3.connect(str(sqlite_path), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")

    schema_path = base_dir / "data" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    need_bootstrap_schema = not _table_exists(conn, "guild_settings")
    _debug_sql(f"schema bootstrap required={need_bootstrap_schema} path={schema_path}")

    def _bootstrap_schema() -> None:
        if need_bootstrap_schema:
            conn.executescript(schema_sql)
        _apply_sql_migrations(conn, base_dir / "data" / "migrations")
        conn.commit()

    _run_with_lock_retry(_bootstrap_schema, operation_name="storage bootstrap")
    _debug_sql("storage initialized and committed")

    _conn = conn
    return _conn


def get_db() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("Storage is not initialized. Call init_storage() first.")
    return _conn


def is_storage_ready() -> bool:
    return _conn is not None


def now_ts() -> int:
    return int(time.time())


def fetchone(sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
    conn = get_db()
    with _lock:
        cur = conn.execute(sql, tuple(params))
        return cur.fetchone()


def fetchall(sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    conn = get_db()
    with _lock:
        cur = conn.execute(sql, tuple(params))
        return cur.fetchall()


def execute(sql: str, params: Iterable[Any] = ()) -> None:
    conn = get_db()
    with _lock:
        conn.execute(sql, tuple(params))
        conn.commit()

