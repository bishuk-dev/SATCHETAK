from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with closing(self._connect()) as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS objects (
                    kind TEXT NOT NULL,
                    id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (kind, id)
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def put(self, kind: str, object_id: str, body: dict[str, Any]) -> None:
        with closing(self._connect()) as db:
            db.execute(
                "INSERT OR REPLACE INTO objects(kind, id, body) VALUES (?, ?, ?)",
                (kind, object_id, json.dumps(body, separators=(",", ":"))),
            )
            db.commit()

    def get(self, kind: str, object_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as db:
            row = db.execute(
                "SELECT body FROM objects WHERE kind = ? AND id = ?", (kind, object_id)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, kind: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT body FROM objects WHERE kind = ? ORDER BY created_at DESC", (kind,)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
