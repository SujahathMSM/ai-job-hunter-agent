"""Posting-date parsing and the "is this posting still live?" rule shared by every scraper.

A posting is kept only if:
* it has a real posted date no older than the age limit, or
* the source itself only returns postings inside the age window (job-board searches run
  with an hours_old filter), or the source is a company's own careers board, which lists
  only roles that are open right now.

Anything else with no verifiable date ("Recently", "Trending Now") is dropped, and no
date is ever made up for a posting that didn't provide one.
"""
import os
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional

MAX_POSTING_AGE_DAYS = int(os.getenv("MAX_POSTING_AGE_DAYS", "30"))


def parse_posted_date(value: Any) -> Optional[date]:
    """Best-effort parse of a posted date: date/datetime/pandas Timestamp, epoch seconds or
    milliseconds, ISO 8601, or RFC 2822 (RSS). Returns None when there is no real date."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, "to_pydatetime"):  # pandas Timestamp
        try:
            return value.to_pydatetime().date()
        except (ValueError, TypeError):
            return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1e11 else value
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None

    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none", "null"}:
        return None
    if text.isdigit():
        return parse_posted_date(int(text))
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text).date()
    except (TypeError, ValueError, IndexError):
        return None


def days_since(posted: date) -> int:
    return max(0, (datetime.now(timezone.utc).date() - posted).days)


def posted_label(days_ago: Optional[int], fallback: str = "") -> str:
    if days_ago is None:
        return fallback
    if days_ago == 0:
        return "Posted today"
    if days_ago == 1:
        return "Posted yesterday"
    return f"Posted {days_ago}d ago"


def assess(value: Any, max_days: int = MAX_POSTING_AGE_DAYS, undated_label: Optional[str] = None) -> Optional[dict]:
    """Returns {"date_posted", "days_ago", "posted_label"} for a live posting, or None if the
    posting is too old, or undated and undated_label is None (no reason to trust it's live)."""
    posted = parse_posted_date(value)
    if posted is None:
        if undated_label is None:
            return None
        return {"date_posted": "", "days_ago": None, "posted_label": undated_label}
    age = days_since(posted)
    if age > max_days:
        return None
    return {"date_posted": posted.isoformat(), "days_ago": age, "posted_label": posted_label(age)}
