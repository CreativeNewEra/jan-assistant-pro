import sqlite3
from pathlib import Path

import pytest

from src.core.migration_manager import apply_migrations, rollback
from src.core.memory import EnhancedMemoryManager


def _schema_version(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0
    finally:
        conn.close()


LATEST_VERSION = 2


def test_new_database_initialized(tmp_path):
    db = tmp_path / "mem.sqlite"
    apply_migrations(str(db))
    assert _schema_version(db) == LATEST_VERSION


def test_upgrade_preserves_data(tmp_path):
    db = tmp_path / "upgrade.sqlite"
    apply_migrations(str(db))
    rollback(str(db), 1)

    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO memories (key, value) VALUES (?, ?)",
        ("foo", "bar"),
    )
    conn.commit()
    conn.close()

    apply_migrations(str(db))

    manager = EnhancedMemoryManager(str(db))
    recalled = manager.recall("foo")
    assert recalled is not None and recalled["value"] == "bar"
    assert _schema_version(db) == LATEST_VERSION


def test_failed_migration_rolls_back(tmp_path, monkeypatch):
    db = tmp_path / "fail.sqlite"
    apply_migrations(str(db))
    rollback(str(db), 1)

    import types
    from src.core import migration_manager as mm

    orig = mm._load_migration

    def patched(path: Path):
        mod = orig(path)
        if "0002_add_notes_table" in path.name:
            mod.upgrade = lambda conn: (_ for _ in ()).throw(RuntimeError("boom"))
        return mod

    monkeypatch.setattr(mm, "_load_migration", patched)

    with pytest.raises(RuntimeError):
        apply_migrations(str(db))

    assert _schema_version(db) == 1
    conn = sqlite3.connect(db)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_notes'"
    )
    assert cur.fetchone() is None
    conn.close()
