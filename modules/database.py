#!/usr/bin/env python3
"""
database.py - Database connection pool, CRUD operations, session/token management.
Supports PostgreSQL with connection pooling.
"""

import os
import time
import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)


@dataclass
class AccountResult:
    email: str
    password: str
    success: bool
    status: str           # pending, verified, registered, verification_failed,
                          # verification_timeout, verification_token_failed,
                          # failed, duplicate, cancelled, login_verified
    error: Optional[str] = None
    proxy_used: Optional[str] = None
    session_token: Optional[str] = None
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()


class DatabaseManager:
    """Manages PostgreSQL connection pool and account operations."""

    def __init__(self, database_url: str, max_workers: int = 5):
        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self._db_url = database_url
        self._max_workers = max_workers

    def init_pool(self) -> bool:
        """Initialize the connection pool."""
        try:
            self._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self._max_workers + 2,
                dsn=self._db_url
            )
            # Test connection
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            logger.info(f"✅ Database pool initialized (maxconn={self._max_workers + 2})")
            return True
        except Exception as e:
            logger.error(f"❌ Database pool init failed: {e}")
            return False

    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            logger.info("🔒 Database pool closed")

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool (context manager)."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    # ==================== ACCOUNT CRUD ====================

    def save_account(self, email: str, password: str, status: str = "pending",
                     proxy_used: str = "", session_token: str = "") -> bool:
        """Save a new account to the database."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO stok_akun (kategori, data_akun, status, session_data)
                           VALUES (%s, %s, %s, %s)""",
                        ("runway", f"{email}|{password}", status, session_token if session_token else None)
                    )
                    conn.commit()
                logger.info(f"✅ Account saved: {email} (status: {status})")
                return True
        except Exception as e:
            logger.error(f"Database error saving account {email}: {e}")
            return False

    def update_status(self, email: str, status: str) -> bool:
        """Update the status of an existing account."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE stok_akun SET status = %s WHERE data_akun LIKE %s",
                        (status, f"{email}|%")
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update account {email} status: {e}")
            return False

    def save_session_token(self, email: str, session_token: str) -> bool:
        """Save session token/cookie for an account (feature #23)."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE stok_akun SET session_data = %s, status = 'verified'
                           WHERE data_akun LIKE %s""",
                        (session_token, f"{email}|%")
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to save session for {email}: {e}")
            return False

    def get_session_token(self, email: str) -> Optional[str]:
        """Retrieve saved session token for an account."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT session_data FROM stok_akun WHERE data_akun LIKE %s LIMIT 1",
                                (f"{email}|%",))
                    row = cur.fetchone()
                    return row[0] if row and row[0] else None
        except Exception:
            return None

    def check_exists(self, email: str) -> bool:
        """Check if account already exists in the database."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM stok_akun WHERE data_akun LIKE %s LIMIT 1",
                                (f"{email}|%",))
                    return cur.fetchone() is not None
        except Exception:
            return False

    def get_pending_accounts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get accounts with pending/verification_timeout status for recovery (feature #27)."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT data_akun, status FROM stok_akun
                           WHERE status IN ('pending', 'verification_timeout', 'verification_token_failed',
                                            'verification_failed', 'pending_verification')
                           ORDER BY created_at ASC LIMIT %s""",
                        (limit,)
                    )
                    rows = cur.fetchall()
                    return [
                        {"email": r[0].split("|")[0], "password": r[0].split("|")[1] if "|" in r[0] else "",
                         "status": r[1]}
                        for r in rows
                    ]
        except Exception as e:
            logger.error(f"Failed to get pending accounts: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get account statistics."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Total count
                    cur.execute("SELECT COUNT(*) FROM stok_akun")
                    total = cur.fetchone()[0]

                    # Count by status
                    cur.execute("""SELECT status, COUNT(*) FROM stok_akun GROUP BY status ORDER BY COUNT(*) DESC""")
                    by_status = {r[0]: r[1] for r in cur.fetchall()}

                    # Today count
                    cur.execute("SELECT COUNT(*) FROM stok_akun WHERE created_at > NOW() - INTERVAL '24 hours'")
                    today_count = cur.fetchone()[0]

                    # Success rate
                    cur.execute("""SELECT COUNT(*) FROM stok_akun
                                   WHERE status IN ('verified', 'verified', 'login_verified', 'registered')""")
                    success_count = cur.fetchone()[0]

                    return {
                        "total": total,
                        "by_status": by_status,
                        "today_count": today_count,
                        "success_count": success_count,
                        "success_rate": round(success_count / total * 100, 1) if total > 0 else 0,
                        "ban_rate": round(
                            (by_status.get("failed", 0) + by_status.get("duplicate", 0)) / total * 100, 1
                        ) if total > 0 else 0,
                    }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total": 0, "by_status": {}, "today_count": 0, "success_rate": 0, "ban_rate": 0}

    def get_incremental_start(self) -> int:
        """Get how many accounts already exist (for incremental farming, feature #28)."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM stok_akun")
                    return cur.fetchone()[0]
        except Exception:
            return 0
