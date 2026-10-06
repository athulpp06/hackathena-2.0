"""
analytics.py - Persistent storage for anonymized usage statistics and user feedback.
Stores aggregate counts and feedback in SQLite with zero PII retention.
"""

import os
import sqlite3
from typing import Any

DB_PATH = os.environ.get("REPUTATION_DB_PATH", os.path.join(os.path.dirname(__file__), "reputation.db"))


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_analytics_db() -> None:
    """Initialize tables for feedback and aggregate scan stats."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT,
                verdict TEXT NOT NULL,
                has_user_text INTEGER DEFAULT 0,
                raw_text_preview TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rule_stats (
                category TEXT PRIMARY KEY,
                hit_count INTEGER DEFAULT 1
            )
        """)
        conn.commit()


def record_scan_event(endpoint: str, risk_level: str, language: str = "en", rule_categories: list[str] | None = None) -> None:
    """Record an anonymized scan event and update rule category frequencies."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO scan_events (endpoint, risk_level, language) VALUES (?, ?, ?)",
                (endpoint, risk_level, language or "en"),
            )
            if rule_categories:
                for cat in set(rule_categories):
                    conn.execute("""
                        INSERT INTO rule_stats (category, hit_count) VALUES (?, 1)
                        ON CONFLICT(category) DO UPDATE SET hit_count = hit_count + 1
                    """, (cat,))
            conn.commit()
    except Exception:
        # Non-critical telemetry failure must never break core user analysis
        pass


def record_feedback_entry(verdict: str, analysis_id: str = "", opt_in_text: bool = False, raw_text: str = "") -> dict[str, Any]:
    """Record user feedback into persistent SQLite storage."""
    preview = None
    if opt_in_text and raw_text:
        preview = raw_text[:200]

    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO feedback (analysis_id, verdict, has_user_text, raw_text_preview) VALUES (?, ?, ?, ?)",
            (analysis_id or None, verdict, 1 if opt_in_text else 0, preview),
        )
        conn.commit()
        entry_id = cur.lastrowid

    return {
        "status": "received",
        "feedback_id": entry_id,
        "text_stored": bool(opt_in_text and preview),
    }


def get_aggregate_stats() -> dict[str, Any]:
    """Return aggregated metrics with zero personally identifiable data."""
    with _get_conn() as conn:
        total_scans = conn.execute("SELECT COUNT(*) FROM scan_events").fetchone()[0]

        endpoint_rows = conn.execute("SELECT endpoint, COUNT(*) as count FROM scan_events GROUP BY endpoint").fetchall()
        scans_by_endpoint = {r["endpoint"]: r["count"] for r in endpoint_rows}

        risk_rows = conn.execute("SELECT risk_level, COUNT(*) as count FROM scan_events GROUP BY risk_level").fetchall()
        risk_distribution = {r["risk_level"]: r["count"] for r in risk_rows}

        rule_rows = conn.execute("SELECT category, hit_count FROM rule_stats ORDER BY hit_count DESC LIMIT 10").fetchall()
        top_rules = [{"category": r["category"], "count": r["hit_count"]} for r in rule_rows]

        feedback_rows = conn.execute("SELECT verdict, COUNT(*) as count FROM feedback GROUP BY verdict").fetchall()
        feedback_distribution = {r["verdict"]: r["count"] for r in feedback_rows}

    return {
        "total_scans": total_scans,
        "scans_by_endpoint": scans_by_endpoint,
        "risk_distribution": risk_distribution,
        "top_rule_categories": top_rules,
        "feedback_distribution": feedback_distribution,
        "privacy_guarantee": "Zero raw message text or user identifiers are included in statistics.",
    }
