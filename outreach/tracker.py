import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DB_PATH

class ApplicationTracker:
    """Tracks applied jobs, draft applications, HR communications, and status updates in SQLite."""

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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            conn.commit()

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
        notes: str = ""
    ) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO applications (
                    job_title, company, location, portal, hr_email,
                    status, applied_date, cv_pdf_path, cover_letter_pdf_path,
                    email_subject, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_title, company, location, portal, hr_email,
                status, now, cv_pdf_path, cover_letter_pdf_path,
                email_subject, notes
            ))
            conn.commit()
            return cursor.lastrowid

    def update_status(self, app_id: int, new_status: str, notes: Optional[str] = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if notes is not None:
                cursor.execute("""
                    UPDATE applications
                    SET status = ?, notes = ?
                    WHERE id = ?
                """, (new_status, notes, app_id))
            else:
                cursor.execute("""
                    UPDATE applications
                    SET status = ?
                    WHERE id = ?
                """, (new_status, app_id))
            conn.commit()

    def list_applications(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM applications
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_metrics(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
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
