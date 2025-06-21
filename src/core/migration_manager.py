from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path
from typing import Callable


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _load_migration(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _ensure_schema_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version("
        "version INTEGER PRIMARY KEY,"
        "applied_at TEXT)"
    )


def _get_current_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def apply_migrations(db_path: str) -> None:
    """Apply all pending migrations to the database."""
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    try:
        _ensure_schema_table(conn)
        current_version = _get_current_version(conn)
        migration_files = [
            p for p in MIGRATIONS_DIR.glob("*.py") if p.stem[0].isdigit()
        ]
        migration_files.sort()
        for path in migration_files:
            version = int(path.stem.split("_", 1)[0])
            if version <= current_version:
                continue
            module = _load_migration(path)
            upgrade: Callable[[sqlite3.Connection], None] = getattr(module, "upgrade")
            with conn:
                upgrade(conn)
                conn.execute(
                    "INSERT INTO schema_version(version, applied_at) VALUES (?, datetime('now'))",
                    (version,),
                )
        conn.commit()
    finally:
        conn.close()


def rollback(db_path: str, target_version: int) -> None:
    """Rollback database to the specified version."""
    conn = sqlite3.connect(db_path)
    try:
        _ensure_schema_table(conn)
        current_version = _get_current_version(conn)
        if target_version >= current_version:
            return
        migration_files = [
            p for p in MIGRATIONS_DIR.glob("*.py") if p.stem[0].isdigit()
        ]
        migration_files.sort(reverse=True)
        for path in migration_files:
            version = int(path.stem.split("_", 1)[0])
            if version > current_version:
                continue
            if version > target_version:
                module = _load_migration(path)
                downgrade: Callable[[sqlite3.Connection], None] = getattr(
                    module, "downgrade"
                )
                with conn:
                    downgrade(conn)
                    conn.execute(
                        "DELETE FROM schema_version WHERE version = ?", (version,)
                    )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage database migrations")
    parser.add_argument("db_path", help="Path to SQLite database")
    parser.add_argument(
        "--rollback", type=int, dest="rollback_to", help="Rollback to version"
    )
    args = parser.parse_args()

    if args.rollback_to is not None:
        rollback(args.db_path, args.rollback_to)
    else:
        apply_migrations(args.db_path)
