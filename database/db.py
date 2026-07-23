import sqlite3
import json
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection
from typing import Any, Dict, List, Optional
from utils.config import Config
from utils.exceptions import AppError
from utils.helpers import ensure_directory

CREATE_DATASET_TABLE = '''
CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    path TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    metadata TEXT
);
'''

class Database:
    def __init__(self, db_path: Path = Config.DB_PATH):
        self.db_path = ensure_directory(db_path.parent) / db_path.name
        self.connection: Optional[Connection] = None
        self.initialize()

    def connect(self) -> Connection:
        if self.connection is None:
            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def initialize(self) -> None:
        conn = self.connect()
        conn.execute(CREATE_DATASET_TABLE)
        conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        try:
            cursor = self.connect().cursor()
            cursor.execute(query, params)
            self.connect().commit()
            return cursor
        except Exception as exc:
            raise AppError(f'Database operation failed: {exc}') from exc

    def register_dataset(
        self,
        dataset_id: str,
        filename: str,
        path: str,
        metadata: Dict[str, Any] = None,
    ) -> None:
        metadata_json = json.dumps(metadata or {})
        self.execute(
            'INSERT OR REPLACE INTO datasets (id, filename, path, uploaded_at, metadata) VALUES (?, ?, ?, ?, ?)',
            (dataset_id, filename, path, datetime.utcnow().isoformat(), metadata_json),
        )

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.execute('SELECT * FROM datasets WHERE id = ?', (dataset_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_datasets(self) -> List[Dict[str, Any]]:
        cursor = self.execute('SELECT * FROM datasets ORDER BY uploaded_at DESC')
        return [dict(row) for row in cursor.fetchall()]
