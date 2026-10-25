import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DB_PATH

class ApplicationTracker:
    """Multi-tenant tracking engine for applied jobs, draft applications,
    candidate personas, and per-user SMTP outreach credentials in SQLite."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Users Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    created_at TEXT
                )
            """)

            # 2. Profiles Table (Multi-tenant candidate persona store)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # 3. User Settings Table (Per-user private SMTP configuration)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id TEXT PRIMARY KEY,
                    smtp_host TEXT,
                    smtp_port INTEGER DEFAULT 587,
                    smtp_user TEXT,
                    smtp_password TEXT,
                    sender_name TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # 4. Applications Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT DEFAULT 'default',
                    job_title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    portal TEXT,
                    hr_email TEXT,
                    status TEXT DEFAULT 'Drafted',
                    applied_date TEXT,
                    cv_pdf_path TEXT,
                    cover_letter_pdf_path TEXT,
                    email_subject TEXT,
                    notes TEXT
                )
            """)

            # Safe migration: ensure user_id column exists
            try:
                cursor.execute("ALTER TABLE applications ADD COLUMN user_id TEXT DEFAULT 'default'")
            except sqlite3.OperationalError:
                pass  # already present

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_apps_user ON applications(user_id)")

            # Seed default user for backward compatibility
            cursor.execute("SELECT id FROM users WHERE id = 'default'")
            if not cursor.fetchone():
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO users (id, email, full_name, created_at)
                    VALUES ('default', 'sujahathmhmd@gmail.com', 'M.S. Mohamed Sujahath', ?)
                """, (now,))

            conn.commit()

    # --- MULTI-TENANT PROFILE CRUD ---
    def get_profile(self, user_id: str = "default") -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT profile_json FROM profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except Exception:
                    pass
        return None

    def save_profile(self, user_id: str, profile: Dict[str, Any]):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        profile_str = json.dumps(profile, ensure_ascii=False)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO profiles (user_id, profile_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    profile_json = excluded.profile_json,
                    updated_at = excluded.updated_at
            """, (user_id, profile_str, now))
            conn.commit()

    # --- MULTI-TENANT SETTINGS CRUD ---
    def get_user_settings(self, user_id: str = "default") -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT smtp_host, smtp_port, smtp_user, smtp_password, sender_name 
                FROM user_settings WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "smtp_host": row[0] or "smtp.gmail.com",
                    "smtp_port": row[1] or 587,
                    "smtp_user": row[2] or "",
                    "smtp_password": row[3] or "",
                    "sender_name": row[4] or ""
                }
        return {}

    def save_user_settings(self, user_id: str, settings: Dict[str, Any]):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_settings (user_id, smtp_host, smtp_port, smtp_user, smtp_password, sender_name, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    smtp_host = excluded.smtp_host,
                    smtp_port = excluded.smtp_port,
                    smtp_user = excluded.smtp_user,
                    smtp_password = excluded.smtp_password,
                    sender_name = excluded.sender_name,
                    updated_at = excluded.updated_at
            """, (
                user_id,
                settings.get("smtp_host", "smtp.gmail.com"),
                int(settings.get("smtp_port", 587)),
                settings.get("smtp_user", "").strip(),
                settings.get("smtp_password", "").strip(),
                settings.get("sender_name", "").strip(),
                now
            ))
            conn.commit()

    # --- MULTI-TENANT APPLICATION TRACKING ---
    def add_application(
        self,
        job_title: str,
        company: str,
        location: str,
        portal: str = "",
        hr_email: str = "",
        status: str = "Drafted",
        cv_pdf_path: str = "",
        cover_letter_pdf_path: str = "",
        email_subject: str = "",
        notes: str = "",
        user_id: str = "default"
    ) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO applications (
                    user_id, job_title, company, location, portal, hr_email,
                    status, applied_date, cv_pdf_path, cover_letter_pdf_path,
                    email_subject, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, job_title, company, location, portal, hr_email,
                status, now, cv_pdf_path, cover_letter_pdf_path,
                email_subject, notes
            ))
            conn.commit()
            return cursor.lastrowid

    def update_status(self, app_id: int, new_status: str, notes: Optional[str] = None, user_id: str = "default"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if notes is not None:
                cursor.execute("""
                    UPDATE applications
                    SET status = ?, notes = ?
                    WHERE id = ? AND user_id = ?
                """, (new_status, notes, app_id, user_id))
            else:
                cursor.execute("""
                    UPDATE applications
                    SET status = ?
                    WHERE id = ? AND user_id = ?
                """, (new_status, app_id, user_id))
            conn.commit()

    def list_applications(self, limit: int = 100, user_id: str = "default") -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM applications
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_metrics(self, user_id: str = "default") -> Dict[str, int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) FROM applications WHERE user_id = ? GROUP BY status", (user_id,))
            rows = cursor.fetchall()
            counts = {status: count for status, count in rows}

            total = sum(counts.values())
            applied = counts.get("Sent", 0) + counts.get("Applied", 0)
            drafted = counts.get("Drafted", 0)
            interviews = counts.get("Interview", 0)

            return {
                "total": total,
                "applied": applied,
                "drafted": drafted,
                "interviews": interviews
            }
