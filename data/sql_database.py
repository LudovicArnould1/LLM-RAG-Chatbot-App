"""Module to provide functions for initializing and interacting with the database."""

import sqlite3


def init_db() -> None:
    """Initialize the database."""
    conn = sqlite3.connect("data/queries.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            answer TEXT NOT NULL,
            documents TEXT NOT NULL,
            feedback TEXT
        )
    """)
    conn.commit()
    conn.close()
