import sqlite3


def upgrade(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            last_accessed DATETIME
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON memories(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")


def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS memories")
