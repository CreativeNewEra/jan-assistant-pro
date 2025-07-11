"""
Memory management system for Jan Assistant Pro
"""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .logging_config import get_logger
from .utils import thread_safe


class MemoryManager:
    """Manages persistent memory for the assistant.

    The class uses :class:`threading.RLock`, a reentrant lock, so that
    methods such as ``remember`` or ``recall`` can call ``save_memory``
    while already holding the lock without causing a deadlock.
    """

    def __init__(
        self, memory_file: str, max_entries: int = 1000, auto_save: bool = True
    ):
        self.memory_file = memory_file
        self.max_entries = max_entries
        self.auto_save = auto_save
        self.memory_data = {}
        self._lock = threading.RLock()
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            {"memory_file": self.memory_file},
        )

        # Ensure directory exists
        self._ensure_memory_dir()

        # Load existing memory
        self.load_memory()

    def __enter__(self) -> "MemoryManager":
        """Load memory when entering a context."""
        self.load_memory()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Save memory when exiting a context."""
        self.save_memory()

    def _ensure_memory_dir(self):
        """Ensure the memory directory exists"""
        memory_dir = os.path.dirname(self.memory_file)
        if memory_dir and not os.path.exists(memory_dir):
            os.makedirs(memory_dir, exist_ok=True)

    def load_memory(self) -> bool:
        """
        Load memory from file

        Returns:
            True if loaded successfully, False otherwise
        """
        with thread_safe(self._lock):
            try:
                if os.path.exists(self.memory_file):
                    with open(self.memory_file, "r", encoding="utf-8") as f:
                        self.memory_data = json.load(f)
                    return True
                else:
                    self.memory_data = {}
                    return True
            except Exception as e:
                self.logger.error(
                    "Error loading memory",
                    extra={"extra_fields": {"error": str(e), "file": self.memory_file}},
                )
                self.memory_data = {}
                return False

    def save_memory(self) -> bool:
        """
        Save memory to file

        Returns:
            True if saved successfully, False otherwise
        """
        with thread_safe(self._lock):
            try:
                # Clean up old entries if we exceed max_entries
                if len(self.memory_data) > self.max_entries:
                    self._cleanup_old_entries()

                with open(self.memory_file, "w", encoding="utf-8") as f:
                    json.dump(self.memory_data, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                self.logger.error(
                    "Error saving memory",
                    extra={"extra_fields": {"error": str(e), "file": self.memory_file}},
                )
                return False

    def _cleanup_old_entries(self):
        """Remove oldest entries to stay within max_entries limit"""
        if len(self.memory_data) <= self.max_entries:
            return

        # Sort by timestamp and keep only the most recent entries
        sorted_items = sorted(
            self.memory_data.items(),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True,
        )

        # Keep only the most recent max_entries
        self.memory_data = dict(sorted_items[: self.max_entries])

    def remember(self, key: str, value: str, category: str = "general") -> bool:
        """
        Store a memory entry

        Args:
            key: The key to store the memory under
            value: The value to remember
            category: Optional category for organization

        Returns:
            True if stored successfully
        """
        with thread_safe(self._lock):
            try:
                self.memory_data[key] = {
                    "value": value,
                    "category": category,
                    "timestamp": datetime.now().isoformat(),
                    "access_count": 0,
                }

                if self.auto_save:
                    self.save_memory()

                return True
            except Exception as e:
                self.logger.error(
                    "Error storing memory",
                    extra={"extra_fields": {"error": str(e), "key": key}},
                )
                return False

    def recall(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory entry

        Args:
            key: The key to recall

        Returns:
            Memory entry dictionary or None if not found
        """
        with thread_safe(self._lock):
            if key in self.memory_data:
                # Update access count
                self.memory_data[key]["access_count"] += 1
                self.memory_data[key]["last_accessed"] = datetime.now().isoformat()

                if self.auto_save:
                    self.save_memory()

                return self.memory_data[key].copy()

            return None

    def fuzzy_recall(self, search_term: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Search for memories using fuzzy matching

        Args:
            search_term: Term to search for

        Returns:
            List of (key, memory) tuples that match
        """
        search_term = search_term.lower().strip()
        matches = []

        with thread_safe(self._lock):
            for key, memory in self.memory_data.items():
                key_lower = key.lower()
                value_lower = memory["value"].lower()

                # Exact key match gets highest priority
                if search_term == key_lower:
                    matches.insert(0, (key, memory.copy()))
                # Partial key match
                elif search_term in key_lower or key_lower in search_term:
                    matches.append((key, memory.copy()))
                # Value contains search term
                elif search_term in value_lower:
                    matches.append((key, memory.copy()))

        return matches

    def forget(self, key: str) -> bool:
        """
        Remove a memory entry

        Args:
            key: The key to forget

        Returns:
            True if removed successfully
        """
        with thread_safe(self._lock):
            if key in self.memory_data:
                del self.memory_data[key]

                if self.auto_save:
                    self.save_memory()

                return True
            return False

    def list_memories(
        self, category: str = None, limit: int = None
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        List all memories, optionally filtered by category

        Args:
            category: Optional category filter
            limit: Optional limit on number of results

        Returns:
            List of (key, memory) tuples
        """
        with thread_safe(self._lock):
            memories = []

            for key, memory in self.memory_data.items():
                if category is None or memory.get("category") == category:
                    memories.append((key, memory.copy()))

            # Sort by timestamp (most recent first)
            memories.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)

            if limit:
                memories = memories[:limit]

            return memories

    def get_categories(self) -> List[str]:
        """
        Get all unique categories

        Returns:
            List of category names
        """
        with thread_safe(self._lock):
            categories = set()
            for memory in self.memory_data.values():
                categories.add(memory.get("category", "general"))
            return sorted(list(categories))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics

        Returns:
            Dictionary with memory statistics
        """
        with thread_safe(self._lock):
            if not self.memory_data:
                return {
                    "total_entries": 0,
                    "categories": [],
                    "timestamps": {},
                    "oldest_entry": None,
                    "newest_entry": None,
                    "most_accessed": None,
                }

            timestamps = {
                k: m.get("timestamp", "") for k, m in self.memory_data.items()
            }
            access_counts = {
                k: m.get("access_count", 0) for k, m in self.memory_data.items()
            }

            most_accessed_key = (
                max(access_counts, key=access_counts.get) if access_counts else None
            )

            return {
                "total_entries": len(self.memory_data),
                "categories": self.get_categories(),
                "timestamps": timestamps,
                "oldest_entry": min(timestamps.values()) if timestamps else None,
                "newest_entry": max(timestamps.values()) if timestamps else None,
                "most_accessed": most_accessed_key
                if most_accessed_key and access_counts[most_accessed_key] > 0
                else None,
            }

    def clear_all(self) -> bool:
        """
        Clear all memories

        Returns:
            True if cleared successfully
        """
        with thread_safe(self._lock):
            try:
                self.memory_data = {}
                if self.auto_save:
                    self.save_memory()
                return True
            except Exception as e:
                self.logger.error(
                    "Error clearing memory",
                    extra={"extra_fields": {"error": str(e)}},
                )
                return False

    def export_memories(self, file_path: str) -> bool:
        """
        Export memories to a file

        Args:
            file_path: Path to export to

        Returns:
            True if exported successfully
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.memory_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(
                "Error exporting memories",
                extra={"extra_fields": {"error": str(e), "path": file_path}},
            )
            return False

    def import_memories(self, file_path: str, merge: bool = True) -> bool:
        """
        Import memories from a file

        Args:
            file_path: Path to import from
            merge: If True, merge with existing memories. If False, replace all.

        Returns:
            True if imported successfully
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported_data = json.load(f)

            with thread_safe(self._lock):
                if merge:
                    self.memory_data.update(imported_data)
                else:
                    self.memory_data = imported_data

                if self.auto_save:
                    self.save_memory()

            return True
        except Exception as e:
            self.logger.error(
                "Error importing memories",
                extra={"extra_fields": {"error": str(e), "path": file_path}},
            )
            return False


class EnhancedMemoryManager:
    """SQLite-backed memory manager for better performance and reliability"""

    def __init__(self, db_path: str, max_entries: int = 1000):
        self.db_path = Path(db_path)
        self.max_entries = max_entries
        self._lock = threading.RLock()
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            {"db_path": str(self.db_path)},
        )
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        from .migration_manager import apply_migrations

        apply_migrations(str(self.db_path))

    @contextmanager
    def _get_connection(self):
        """Thread-safe database connection"""
        with thread_safe(self._lock):
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def remember(self, key: str, value: str, category: str = "general") -> bool:
        """Store a memory with automatic cleanup"""
        try:
            with self._get_connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
                if count >= self.max_entries:
                    cleanup_count = max(1, self.max_entries // 10)
                    conn.execute(
                        """
                        DELETE FROM memories
                        WHERE key IN (
                            SELECT key FROM memories
                            ORDER BY timestamp ASC
                            LIMIT ?
                        )
                        """,
                        (cleanup_count,),
                    )

                conn.execute(
                    """
                    INSERT OR REPLACE INTO memories (key, value, category, timestamp, access_count)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 0)
                    """,
                    (key, value, category),
                )

            return True
        except Exception as e:
            self.logger.error(
                "Error storing memory (SQLite)",
                extra={"extra_fields": {"error": str(e), "key": key}},
            )
            return False

    def recall(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve and update access statistics"""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    """SELECT * FROM memories WHERE key = ?""",
                    (key,),
                ).fetchone()

                if row:
                    conn.execute(
                        """
                        UPDATE memories
                        SET access_count = access_count + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        WHERE key = ?
                        """,
                        (key,),
                    )

                    return dict(row)

            return None
        except Exception as e:
            self.logger.error(
                "Error recalling memory (SQLite)",
                extra={"extra_fields": {"error": str(e), "key": key}},
            )
            return None

    def fuzzy_search(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search across keys and values"""
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT * FROM memories
                    WHERE key LIKE ? OR value LIKE ?
                    ORDER BY
                        CASE WHEN key = ? THEN 1
                             WHEN key LIKE ? THEN 2
                             ELSE 3 END,
                        access_count DESC,
                        timestamp DESC
                    LIMIT ?
                    """,
                    (
                        f"%{search_term}%",
                        f"%{search_term}%",
                        search_term,
                        f"{search_term}%",
                        limit,
                    ),
                ).fetchall()

                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(
                "Error searching memories",
                extra={"extra_fields": {"error": str(e), "term": search_term}},
            )
            return []
