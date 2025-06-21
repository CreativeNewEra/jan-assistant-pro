from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class StorageInterface(ABC):
    """Abstract storage backend."""

    @abstractmethod
    def save(self, key: str, value: Any) -> None:
        """Persist ``value`` under ``key``."""
        raise NotImplementedError

    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Retrieve ``value`` for ``key`` or ``None`` if missing."""
        raise NotImplementedError


class JSONStorage(StorageInterface):
    """Simple JSON file storage."""

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding="utf-8")

    def _load_data(self) -> dict:
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_data(self, data: dict) -> None:
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save(self, key: str, value: Any) -> None:
        data = self._load_data()
        data[key] = value
        self._write_data(data)

    def load(self, key: str) -> Optional[Any]:
        data = self._load_data()
        return data.get(key)


class SQLiteStorage(StorageInterface):
    """SQLite-based storage backend."""

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value BLOB)"
            )

    def save(self, key: str, value: Any) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
            conn.commit()

    def load(self, key: str) -> Optional[Any]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT value FROM kv WHERE key = ?", (key,))
            row = cur.fetchone()
        if row is None:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON for key '{key}': {row[0]}") from e
