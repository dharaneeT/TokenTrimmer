"""SQLite ledger: one row per run, so savings are measured, not guessed."""
import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ledger.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    source TEXT NOT NULL,
    budget INTEGER NOT NULL,
    start_tokens INTEGER NOT NULL,
    end_tokens INTEGER NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    token_source TEXT NOT NULL,
    steps_json TEXT NOT NULL
)
"""


def connect(db_path=None):
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def record_run(result, source, duration_ms, db_path=None):
    """Store one run and return its id."""
    steps = [asdict(step) for step in result.steps]
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO runs (created_at, source, budget, start_tokens, end_tokens, "
            "status, duration_ms, token_source, steps_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (created, source, result.budget, result.start_tokens, result.end_tokens,
             result.status, duration_ms, "estimate", json.dumps(steps)),
        )
        return cursor.lastrowid


def stats(db_path=None, limit=10):
    with closing(connect(db_path)) as conn:
        totals = conn.execute(
            "SELECT COUNT(*) AS runs, COALESCE(SUM(start_tokens), 0) AS start_total, "
            "COALESCE(SUM(end_tokens), 0) AS end_total FROM runs"
        ).fetchone()
        rows = conn.execute(
            "SELECT id, created_at, source, budget, start_tokens, end_tokens, status, "
            "duration_ms, steps_json FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    recent = [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "source": row["source"],
            "budget": row["budget"],
            "start_tokens": row["start_tokens"],
            "end_tokens": row["end_tokens"],
            "saved": row["start_tokens"] - row["end_tokens"],
            "status": row["status"],
            "duration_ms": row["duration_ms"],
            "steps": len(json.loads(row["steps_json"])),
        }
        for row in rows
    ]
    return {
        "runs": totals["runs"],
        "start_total": totals["start_total"],
        "end_total": totals["end_total"],
        "saved_total": totals["start_total"] - totals["end_total"],
        "token_source": "estimate (tiktoken)",
        "recent": recent,
    }