# database/users_database.py

import sqlite3
from typing import Optional, Tuple, List
from database.base_database import BaseDatabase

class UsersDatabase(BaseDatabase):
    def __init__(self, db_path: str):
        super().__init__(db_path, 'users')
        self.create_table("""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                username       TEXT    UNIQUE NOT NULL,
                password_hash  TEXT    NOT NULL
            )
        """)

    def get_user_by_username(self, username: str) -> Optional[sqlite3.Row]:
        """
        Fetch a single user row by username.
        Returns Row with fields (id, username, password_hash) or None.
        """
        return self.get_row('username', username)

    def get_user_by_id(self, user_id: int) -> Optional[sqlite3.Row]:
        """Fetch by numeric ID."""
        return self.get_row('id', user_id)

    def add_user(self, username: str, password_hash: str) -> int:
        """
        Insert a new user with a server‑salted password_hash.
        Returns the new user's id.
        """
        return self.insert({'username': username, 'password_hash': password_hash})

    def list_usernames(self) -> List[str]:
        """Return all usernames."""
        rows = self.get_columns('username')
        return [r[0] for r in rows]
