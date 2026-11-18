"""Job-search APIs that need a free key. Currently: Jooble.

A source runs only when its key is set in .env, and only adds results: if the key is
missing, rejected or rate-limited, the source is skipped and the reason logged.

    JOOBLE_API_KEY   https://jooble.org/api/about  (free on request)

Jooble aggregates listings from many boards worldwide, the Gulf included, and is searched
for every location.
"""
import os
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests

from hunter.freshness import assess

TIMEOUT = (4.0, 15.0)

def jooble_enabled() -> bool:
    return bool(os.getenv("JOOBLE_API_KEY", "").strip())


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _posting(title: str, company: str, location: str, url: str, fresh: Dict[str, Any], site: str,
             description: str = "", salary: str = "") -> Dict[str, Any]:
    from hunter.hr_finder import HRFinder
    emails = HRFinder.extract_emails_from_text(description)
    return {
        "job_title": title.strip(),
        "company": company.strip(),
        "location": location.strip(),
        "site": site,
        "portal": url, "job_url": url, "apply_url": url,
        "salary": salary, "salary_range": salary,
        "hr_email": emails[0] if emails else "", "has_hr_email": bool(emails),
        "description": description[:300] + ("..." if len(description) > 300 else ""),
        "full_description": description,
        **fresh,
    }


def search_jooble(keyword: str, location: str, max_days: int, results: int = 20) -> List[Dict[str, Any]]:
    key = os.getenv("JOOBLE_API_KEY", "").strip()
    if not key:
        return []
    body = {
        "keywords": keyword,
        "location": location,
        "page": 1,
        "ResultOnPage": min(results, 50),
        "datecreatedfrom": (date.today() - timedelta(days=max_days)).isoformat(),
    }
    try:
        r = requests.post(f"https://jooble.org/api/{key}", json=body, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"[Jooble] request failed for {location}: {type(e).__name__}")
        return []
    if r.status_code != 200:
        print(f"[Jooble] HTTP {r.status_code} for {location}: {r.text[:150]}")
        return []

    out = []
    for item in (r.json() or {}).get("jobs", []) or []:
        # Jooble aggregates many sources; only keep listings with a real recent date
        fresh = assess(item.get("updated"), max_days)
        url = item.get("link") or ""
        title = _strip_html(item.get("title") or "")
        if not fresh or not url or not title:
            continue
        source = (item.get("source") or "").strip()
        out.append(_posting(
            title, item.get("company") or "", item.get("location") or location, url, fresh,
            f"Jooble ({source})" if source else "Jooble",
            _strip_html(item.get("snippet") or ""), (item.get("salary") or "").strip(),
        ))
    return out


def search_keyed_sources(keyword: str, city: str, country: str, display: Optional[str],
                         max_days: int, results: int) -> List[Dict[str, Any]]:
    """Results from every keyed API that is configured, for one location."""
    jobs = []
    if jooble_enabled():
        jobs += search_jooble(keyword, display or city, max_days, results)
    return jobs
