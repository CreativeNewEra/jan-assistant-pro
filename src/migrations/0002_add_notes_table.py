import sqlite3


def upgrade(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_notes (
            key TEXT PRIMARY KEY,
            note TEXT NOT NULL
        )
        """
    )


def downgrade(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS memory_notes")
