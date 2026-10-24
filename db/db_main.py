import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "database.db"


def create_db() -> None:
    """
    Creates initial db
    """

    # Gets db folder from db path, then creates it and also creates any missing folders leading to it, avoids error if alr exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Table for songs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                song_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                file_path TEXT NOT NULL,
                duration_ms INTEGER,
                file_sha256 TEXT UNIQUE,
                is_known BOOLEAN DEFAULT FALSE
            )
        """)

        # Table for fingerprints
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fingerprints (
                hash TEXT,
                song_id INTEGER REFERENCES songs(song_id),
                anchor_frame INTEGER
            )
        """)
        conn.commit()

        return None
