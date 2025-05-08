# database/song_database.py

import sqlite3
from typing import Optional, List, Dict
from database.base_database import BaseDatabase

class SongDatabase(BaseDatabase):
    def __init__(self, db_path: str):
        super().__init__(db_path, 'songs')
        self.create_table("""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id                   INTEGER PRIMARY KEY,
                song_name            TEXT    NOT NULL UNIQUE,
                artist_name          TEXT    NOT NULL,
                album_name           TEXT,
                album_cover_image    TEXT,
                album_type           TEXT    NOT NULL,
                release_date         TEXT,
                spotify_url          TEXT,
                spectrograms         TEXT    NOT NULL
            )
        """)
        self.history = BaseDatabase(db_path, 'song_history')
        self.history.create_table("""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT NOT NULL,
                song_id     INTEGER NOT NULL,
                played_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def add_song(self, song_data: Dict) -> int:
        """Insert full metadata dict; returns song_id."""
        return self.insert(song_data)

    def get_song_by_name(self, song_name: str) -> Optional[sqlite3.Row]:
        """Fetch by unique name."""
        return self.get_row('song_name', song_name)

    def get_song_by_id(self, song_id: int) -> Optional[sqlite3.Row]:
        """Fetch by numeric ID."""
        return self.get_row('id', song_id)

    def update_song_history(self, username: str, song_name: str) -> None:
        """Append play, then trim to the 20 most recent."""
        row = self.get_song_by_name(song_name)
        if not row:
            return
        song_id = row['id']
        self.history.insert({'username': username, 'song_id': song_id})
        with self.history._connect() as conn:
            conn.execute("""
                DELETE FROM song_history
                 WHERE id IN (
                   SELECT id FROM song_history
                    WHERE username = ?
                    ORDER BY played_at DESC
                    LIMIT -1 OFFSET 20
                 )
            """, (username,))
            conn.commit()

    def get_user_history(self, username: str) -> List[Dict]:
        """
        Returns newest→oldest list of {'song_name','played_at'} for this user.
        """
        with self.history._connect() as conn:
            cur = conn.execute("""
                SELECT s.song_name, h.played_at
                  FROM song_history h
                  JOIN songs s ON s.id = h.song_id
                 WHERE h.username = ?
                 ORDER BY h.played_at DESC
            """, (username,))
            rows = cur.fetchall()
        return [{'song_name': r['song_name'], 'played_at': r['played_at']} for r in rows]

    def list_all_songs(self) -> List[sqlite3.Row]:
        """Fetch every metadata row."""
        return self.get_all()
