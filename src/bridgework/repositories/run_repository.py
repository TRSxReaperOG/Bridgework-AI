import json
import sqlite3
import uuid
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bridgework.schemas import Run

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS runs (
    run_id     TEXT PRIMARY KEY,
    stage      TEXT NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


class RunNotFoundError(Exception):
    """Raised when updating a run that does not exist."""


class RunRepository:
    """Saves and loads runs in a SQLite file, so a run survives restarts and can be resumed."""

    def __init__(self, db_path: str | Path):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def create_run(self, stage: str, state: dict[str, Any] | None = None) -> str:
        run_id = uuid.uuid4().hex
        now = _now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO runs (run_id, stage, state_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (run_id, stage, json.dumps(state or {}), now, now),
            )
        return run_id

    def update_run(
        self,
        run_id: str,
        stage: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> None:
        if stage is None and state is None:
            raise ValueError("update_run needs a new stage, a new state, or both")

        assignments = ["updated_at = ?"]
        values: list[Any] = [_now()]
        if stage is not None:
            assignments.append("stage = ?")
            values.append(stage)
        if state is not None:
            assignments.append("state_json = ?")
            values.append(json.dumps(state))
        values.append(run_id)

        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE runs SET {', '.join(assignments)} WHERE run_id = ?", values
            )
        if cursor.rowcount == 0:
            raise RunNotFoundError(run_id)

    def get_run(self, run_id: str) -> Run | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return Run(
            run_id=row["run_id"],
            stage=row["stage"],
            state=json.loads(row["state_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return _Connection(conn)


class _Connection:
    """Commits on success, rolls back on error, and always closes the database file."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def __enter__(self) -> sqlite3.Connection:
        return self._conn

    def __exit__(self, exc_type, exc, tb) -> None:
        with closing(self._conn):
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()


def _now() -> str:
    return datetime.now(UTC).isoformat()
