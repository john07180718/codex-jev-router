"""Process-safe local budgets and metadata. No prompts or responses are stored."""
from __future__ import annotations
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .config import PolicyError

class Ledger:
    def __init__(self, home: Path):
        home.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = home / "usage.sqlite3"
        self.db = sqlite3.connect(self.path, timeout=2)
        self.db.execute("PRAGMA busy_timeout=2000")
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, project TEXT NOT NULL, created REAL NOT NULL, closed INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY, task TEXT NOT NULL, project TEXT NOT NULL,
                day TEXT NOT NULL, created REAL NOT NULL, fingerprint TEXT NOT NULL,
                purpose TEXT NOT NULL, status TEXT NOT NULL, model TEXT,
                input_tokens INTEGER, output_tokens INTEGER);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, created REAL NOT NULL, task TEXT NOT NULL,
                project TEXT NOT NULL, purpose TEXT NOT NULL, mode TEXT NOT NULL,
                status TEXT NOT NULL, reason TEXT NOT NULL, attempts INTEGER NOT NULL,
                elapsed_ms INTEGER NOT NULL);
        ''')
        self.db.execute("INSERT OR IGNORE INTO meta VALUES ('hmac_key', ?)", (secrets.token_hex(32),))
        self.db.commit()
        self.salt = bytes.fromhex(self.db.execute("SELECT value FROM meta WHERE key='hmac_key'").fetchone()[0])
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def close(self) -> None:
        self.db.close()

    def digest(self, value: str | bytes) -> str:
        return hmac.new(self.salt, value.encode() if isinstance(value, str) else value, hashlib.sha256).hexdigest()

    def begin(self, project: str) -> str:
        task = str(uuid.uuid4())
        with self.db:
            self.db.execute("INSERT INTO tasks(id,project,created) VALUES (?,?,?)", (task, self.digest(project), time.time()))
        return task

    def check_task(self, task: str, project: str) -> None:
        row = self.db.execute("SELECT project,created,closed FROM tasks WHERE id=?", (task,)).fetchone()
        if row is None or row[0] != self.digest(project):
            raise PolicyError("unknown_or_wrong_project_task")
        if row[2] or time.time() - row[1] > 86400:
            raise PolicyError("closed_or_expired_task")

    def end(self, task: str, project: str) -> None:
        self.check_task(task, project)
        with self.db:
            self.db.execute("UPDATE tasks SET closed=1 WHERE id=?", (task,))

    def reserve(self, task: str, project: str, payload: bytes, purpose: str,
                task_limit: int, daily_limit: int, retry: bool = False) -> int:
        day = datetime.now(timezone.utc).date().isoformat()
        fingerprint = self.digest(payload)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.check_task(task, project)
            if not retry and self.db.execute("SELECT 1 FROM attempts WHERE task=? AND fingerprint=? LIMIT 1", (task, fingerprint)).fetchone():
                raise PolicyError("duplicate_request")
            if self.db.execute("SELECT count(*) FROM attempts WHERE task=?", (task,)).fetchone()[0] >= task_limit:
                raise PolicyError("task_budget_exhausted")
            if self.db.execute("SELECT count(*) FROM attempts WHERE day=?", (day,)).fetchone()[0] >= daily_limit:
                raise PolicyError("daily_budget_exhausted")
            cur = self.db.execute("INSERT INTO attempts(task,project,day,created,fingerprint,purpose,status) VALUES (?,?,?,?,?,?,?)",
                                  (task, self.digest(project), day, time.time(), fingerprint, purpose, "reserved"))
            self.db.commit()
            return int(cur.lastrowid)
        except BaseException:
            self.db.rollback()
            raise

    def finish(self, attempt: int, status: str, response: dict[str, Any] | None = None) -> None:
        usage = response["usage"] if response else {}
        with self.db:
            self.db.execute("UPDATE attempts SET status=?,model=?,input_tokens=?,output_tokens=? WHERE id=?",
                            (status, response.get("model") if response else None,
                             usage.get("input_tokens"), usage.get("output_tokens"), attempt))

    def event(self, task: str, project: str, purpose: str, mode: str,
              status: str, reason: str, attempts: int, elapsed_ms: int) -> None:
        with self.db:
            self.db.execute("INSERT INTO events(created,task,project,purpose,mode,status,reason,attempts,elapsed_ms) VALUES (?,?,?,?,?,?,?,?,?)",
                            (time.time(), task, self.digest(project), purpose, mode, status, reason, attempts, elapsed_ms))

    def stats(self) -> dict[str, Any]:
        total, known, inp, out = self.db.execute("SELECT count(*),count(input_tokens),sum(input_tokens),sum(output_tokens) FROM attempts").fetchone()
        events = {f"{mode}:{status}": n for mode, status, n in self.db.execute("SELECT mode,status,count(*) FROM events GROUP BY mode,status")}
        return {"reserved_live_attempts": total, "attempts_with_reported_usage": known,
                "attempts_with_unknown_usage": total - known,
                "reported_jev_input_tokens": inp or 0, "reported_jev_output_tokens": out or 0,
                "codex_tokens": None, "codex_quota_savings": None, "events": events,
                "note": "Reserved attempts include failures/crashes; unknown usage is not zero. Mock is not inference."}
