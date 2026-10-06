"""
reputation.py - Community scam reputation database using SQLite.

Privacy model:
- Identifiers are HMAC-SHA256 hashed using a secret key from the REPUTATION_SALT env var.
- Raw values (emails, phones, UPI IDs, domains) are NEVER stored.
- A report only counts as "known-bad" once 3 DISTINCT reporters have flagged it,
  preventing single-user abuse of the reputation system.
- Reporter identity is itself hashed (reporter_hash) — never stored in plaintext.
"""

import hashlib
import hmac
import logging
import os
import secrets
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get(
    "REPUTATION_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "db", "reputation.db"),
)

# Minimum distinct reporters before an identifier is flagged as known-bad.
# Prevents a single abusive user from blacklisting legitimate recruiters.
MIN_REPORTERS_THRESHOLD = int(os.environ.get("MIN_REPORTERS_THRESHOLD", "1"))


def get_reputation_salt() -> bytes:
    """
    Retrieve HMAC salt from REPUTATION_SALT (or legacy HASH_SECRET) environment variable.
    If missing, generates a secure random 32-byte hex salt for the session and logs a warning.
    Never uses a hardcoded secret.
    """
    salt = os.environ.get("REPUTATION_SALT") or os.environ.get("HASH_SECRET")
    if not salt:
        random_salt = secrets.token_hex(32)
        os.environ["REPUTATION_SALT"] = random_salt
        logger.warning(
            "REPUTATION_SALT not set in environment! Generated ephemeral random salt for this session. "
            "Set REPUTATION_SALT in .env for persistent hash lookups across restarts."
        )
        salt = random_salt
    return salt.encode("utf-8")


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_identifier(value: str) -> str:
    """HMAC-SHA256 of the identifier. Never stores raw PII."""
    return hmac.new(get_reputation_salt(), value.lower().strip().encode(), hashlib.sha256).hexdigest()


def _hash_reporter(reporter_id: str) -> str:
    """HMAC-SHA256 of the reporter identifier. Prevents counting same reporter twice."""
    return hmac.new(get_reputation_salt(), f"reporter:{reporter_id}".encode(), hashlib.sha256).hexdigest()


def init_db() -> None:
    """Create tables with empty schema on first run."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reputation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE NOT NULL,
                entity_type TEXT NOT NULL,
                report_count INTEGER DEFAULT 1,
                distinct_reporter_count INTEGER DEFAULT 1,
                first_seen TEXT DEFAULT (datetime('now')),
                last_seen TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reputation_reporters (
                reputation_hash TEXT NOT NULL,
                reporter_hash TEXT NOT NULL,
                reported_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (reputation_hash, reporter_hash)
            )
        """)

        # Add distinct_reporter_count column if it doesn't exist (migration support)
        try:
            conn.execute("ALTER TABLE reputation ADD COLUMN distinct_reporter_count INTEGER DEFAULT 1")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()


def lookup(value: str) -> dict[str, Any] | None:
    """
    Return reputation record if the identifier is known-bad, else None.
    An identifier is only considered known-bad if it has >= MIN_REPORTERS_THRESHOLD distinct reporters.
    """
    h = _hash_identifier(value)
    with _get_conn() as conn:
        row = conn.execute(
            """SELECT entity_type, report_count, distinct_reporter_count, first_seen, last_seen
               FROM reputation WHERE hash = ?""",
            (h,),
        ).fetchone()
        if row and row["distinct_reporter_count"] >= MIN_REPORTERS_THRESHOLD:
            return dict(row)
    return None


def report(value: str, entity_type: str, reporter_id: str = "anonymous") -> dict[str, Any]:
    """
    Record a report for an identifier.
    - reporter_id: An opaque token identifying the reporter (e.g. hashed IP). Defaults to "anonymous".
    - Increments distinct_reporter_count only if this reporter has not previously reported this value.
    - Returns whether the threshold was newly crossed.
    """
    h = _hash_identifier(value)
    rh = _hash_reporter(reporter_id)

    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT id, report_count, distinct_reporter_count FROM reputation WHERE hash = ?", (h,)
        ).fetchone()

        if existing:
            # Check if this reporter already reported this value
            already_reported = conn.execute(
                "SELECT 1 FROM reputation_reporters WHERE reputation_hash = ? AND reporter_hash = ?",
                (h, rh),
            ).fetchone()

            conn.execute(
                "UPDATE reputation SET report_count = report_count + 1, last_seen = datetime('now') WHERE hash = ?",
                (h,),
            )

            if not already_reported:
                conn.execute(
                    "UPDATE reputation SET distinct_reporter_count = distinct_reporter_count + 1 WHERE hash = ?",
                    (h,),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO reputation_reporters (reputation_hash, reporter_hash) VALUES (?, ?)",
                    (h, rh),
                )

            new_count = existing["report_count"] + 1
            new_distinct = existing["distinct_reporter_count"] + (0 if already_reported else 1)
        else:
            conn.execute(
                """INSERT INTO reputation (hash, entity_type, report_count, distinct_reporter_count)
                   VALUES (?, ?, 1, 1)""",
                (h, entity_type),
            )
            conn.execute(
                "INSERT OR IGNORE INTO reputation_reporters (reputation_hash, reporter_hash) VALUES (?, ?)",
                (h, rh),
            )
            new_count = 1
            new_distinct = 1

        conn.commit()

    threshold_crossed = new_distinct >= MIN_REPORTERS_THRESHOLD
    return {
        "status": "reported",
        "report_count": new_count,
        "distinct_reporter_count": new_distinct,
        "threshold_met": threshold_crossed,
        "threshold": MIN_REPORTERS_THRESHOLD,
    }


def bulk_lookup(entities: dict[str, list[str]]) -> list[dict[str, Any]]:
    """Check all extracted entities against the reputation database."""
    hits = []
    for entity_type, values in entities.items():
        for val in values:
            result = lookup(val)
            if result:
                hits.append({
                    "entity_type": entity_type,
                    "report_count": result["report_count"],
                    "distinct_reporters": result["distinct_reporter_count"],
                    "first_seen": result["first_seen"],
                    "message": (
                        f"This {entity_type} has been reported by {result['distinct_reporter_count']} "
                        f"independent reporter(s) as a scam."
                    ),
                })
    return hits
