# database/base_database.py

import sqlite3
from typing import Any, List, Optional, Tuple

class BaseDatabase:
    """
    A simple SQLite-backed base class providing:
      - Table creation (with a {table_name} placeholder)
      - Insertion
      - Single-row and multi-row queries
      - Convenience methods for common patterns
    """

    def __init__(self, db_path: str, table_name: str):
        self.db_path = db_path
        self.table_name = table_name

    def _connect(self) -> sqlite3.Connection:
        """Open a new connection with foreign keys enabled and dict-like row access."""
        conn = sqlite3.connect(self.db_path)
        # enforce foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON;")
        # return rows as sqlite3.Row for column access by name
        conn.row_factory = sqlite3.Row
        return conn

    def create_table(self, create_sql: str) -> None:
        """
        Runs a CREATE TABLE IF NOT EXISTS.  `create_sql` may contain
        "{table_name}" which will be replaced.
        """
        sql = create_sql.format(table_name=self.table_name)
        with self._connect() as conn:
            conn.execute(sql)
            conn.commit()

    def insert(self, data: dict) -> int:
        """
        Insert a row given by a dict of column:value pairs.
        Returns the new row’s ID.
        """
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        sql = f"INSERT INTO {self.table_name} ({cols}) VALUES ({placeholders})"
        values = tuple(data.values())

        with self._connect() as conn:
            cursor = conn.execute(sql, values)
            conn.commit()
            return cursor.lastrowid

    def get_row(self, column: str, value: Any) -> Optional[Tuple]:
        """
        Fetch exactly one row where `column = value`, or None if not found.
        """
        sql = f"SELECT * FROM {self.table_name} WHERE {column} = ?"
        with self._connect() as conn:
            cursor = conn.execute(sql, (value,))
            return cursor.fetchone()

    def get_all(self) -> List[Tuple]:
        """
        Fetch every row in the table.
        """
        sql = f"SELECT * FROM {self.table_name}"
        with self._connect() as conn:
            cursor = conn.execute(sql)
            return cursor.fetchall()

    def get_columns(self, column: str) -> List[Tuple]:
        """
        Fetch a single column for all rows (useful for listing names, etc).
        """
        sql = f"SELECT {column} FROM {self.table_name}"
        with self._connect() as conn:
            cursor = conn.execute(sql)
            return cursor.fetchall()