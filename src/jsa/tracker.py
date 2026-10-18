"""SQLite storage for applications and runs.

applications: one row per analyzed posting. Every row starts as a 'draft'; only an
explicit approve moves it on (draft -> approved -> applied/rejected).
llm_calls: one row per model call, so cost and latency can be totalled per run.
"""

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from jsa.schemas import FitReport, Posting

STATUSES = ("draft", "approved", "applied", "rejected")

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    run_id      TEXT NOT NULL,
    company     TEXT,
    title       TEXT,
    fit_score   INTEGER,
    verdict     TEXT,
    status      TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'approved', 'applied', 'rejected')),
    report_json TEXT NOT NULL,
    notes       TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS llm_calls (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL,
    ts            TEXT NOT NULL,
    step          TEXT NOT NULL,
    model         TEXT NOT NULL,
    input_tokens  INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd      REAL NOT NULL,
    latency_ms    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS llm_calls_run_id ON llm_calls (run_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def _db():
    path = Path(os.environ.get("JSA_DB_PATH", "data/db/jsa.sqlite"))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        with conn:  # commits on success, rolls back on error
            yield conn
    finally:
        conn.close()


def new_run_id() -> str:
    return uuid.uuid4().hex


def log_call(run_id, step, model, input_tokens, output_tokens, cost_usd, latency_ms) -> None:
    with _db() as conn:
        conn.execute(
            "INSERT INTO llm_calls (run_id, ts, step, model, input_tokens, output_tokens,"
            " cost_usd, latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, _now(), step, model, input_tokens, output_tokens, cost_usd, latency_ms),
        )


def run_cost(run_id: str) -> float:
    with _db() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_calls WHERE run_id = ?", (run_id,)
        ).fetchone()
    return row[0]


def save_draft(
    run_id: str, posting: Posting, report: FitReport, warnings: list[str], dropped_bullets: int
) -> int:
    report_json = json.dumps(
        {
            "posting": posting.model_dump(),
            "report": report.model_dump(),
            "warnings": warnings,
            "dropped_bullets": dropped_bullets,
        }
    )
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO applications (created_at, run_id, company, title, fit_score, verdict,"
            " report_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (_now(), run_id, posting.company, posting.title, report.fit_score, report.verdict,
             report_json),
        )
    return cur.lastrowid


def approve(application_id: int, notes: str = "") -> str:
    with _db() as conn:
        row = conn.execute(
            "SELECT status, company, title FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if row is None:
            return f"No application with id {application_id}."
        if row["status"] != "draft":
            return f"Application {application_id} is already {row['status']}; only drafts can be approved."
        conn.execute(
            "UPDATE applications SET status = 'approved', notes = ? WHERE id = ?",
            (notes, application_id),
        )
    return f"Approved application {application_id}: {row['company']} - {row['title']}."


def list_text(status: str = "all", limit: int = 20) -> str:
    if status != "all" and status not in STATUSES:
        return f"Unknown status {status!r}. Use one of: all, {', '.join(STATUSES)}."
    query = "SELECT id, created_at, company, title, fit_score, verdict, status FROM applications"
    params: tuple = ()
    if status != "all":
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY id DESC LIMIT ?"
    with _db() as conn:
        rows = conn.execute(query, (*params, limit)).fetchall()
    if not rows:
        return "No applications yet." if status == "all" else f"No {status} applications."
    return "\n".join(
        f"#{r['id']:<3} {r['status']:<8} {r['fit_score']:>3}  {r['verdict']:<7} "
        f"{r['company']} - {r['title']}  ({r['created_at'][:10]})"
        for r in rows
    )
