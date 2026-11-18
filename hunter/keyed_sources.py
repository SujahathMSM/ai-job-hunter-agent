"""Job-search APIs that need a free key: Adzuna and Jooble.

Each runs only when its key is set in .env, and only adds results: if a key is missing,
rejected or rate-limited, the source is skipped and the reason logged.

    ADZUNA_APP_ID / ADZUNA_APP_KEY   https://developer.adzuna.com  (free developer plan)
    JOOBLE_API_KEY                   https://jooble.org/api/about  (free on request)

Adzuna covers the countries in ADZUNA_COUNTRIES (no Gulf coverage). Jooble aggregates
listings from many boards worldwide and is searched for every location.
"""
import os
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests

from hunter.freshness import assess

TIMEOUT = (4.0, 15.0)

# Our country names -> Adzuna country codes
ADZUNA_COUNTRIES = {
    "uk": "gb", "usa": "us", "austria": "at", "australia": "au", "belgium": "be", "brazil": "br",
    "canada": "ca", "switzerland": "ch", "germany": "de", "spain": "es", "france": "fr", "india": "in",
    "italy": "it", "mexico": "mx", "netherlands": "nl", "new zealand": "nz", "poland": "pl",
    "singapore": "sg", "south africa": "za",
}


def adzuna_enabled() -> bool:
    return bool(os.getenv("ADZUNA_APP_ID", "").strip() and os.getenv("ADZUNA_APP_KEY", "").strip())


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


def search_adzuna(keyword: str, city: str, country: str, max_days: int, results: int = 20) -> List[Dict[str, Any]]:
    code = ADZUNA_COUNTRIES.get((country or "").lower())
    if not code or not adzuna_enabled():
        return []
    params = {
        "app_id": os.getenv("ADZUNA_APP_ID", "").strip(),
        "app_key": os.getenv("ADZUNA_APP_KEY", "").strip(),
        "what": keyword,
        "where": city,
        "max_days_old": max_days,
        "results_per_page": min(results, 50),
        "sort_by": "date",
        "content-type": "application/json",
    }
    try:
        r = requests.get(f"https://api.adzuna.com/v1/api/jobs/{code}/search/1", params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"[Adzuna] request failed for {city}: {type(e).__name__}")
        return []
    if r.status_code != 200:
        print(f"[Adzuna] HTTP {r.status_code} for {city}: {r.text[:150]}")
        return []

    out = []
    for item in (r.json() or {}).get("results", []) or []:
        # Adzuna was asked for max_days_old, so an undated result is inside that window
        fresh = assess(item.get("created"), max_days, undated_label=f"Posted within {max_days}d")
        url = item.get("redirect_url") or ""
        title = _strip_html(item.get("title") or "")
        if not fresh or not url or not title:
            continue
        lo, hi = item.get("salary_min"), item.get("salary_max")
        salary = ""
        try:
            if lo and hi and float(hi) > 0:
                salary = f"{int(float(lo)):,} - {int(float(hi)):,} / yr"
        except (TypeError, ValueError):
            pass
        out.append(_posting(
            title,
            (item.get("company") or {}).get("display_name") or "",
            (item.get("location") or {}).get("display_name") or city,
            url, fresh, "Adzuna", _strip_html(item.get("description") or ""), salary,
        ))
    return out


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
    if adzuna_enabled():
        jobs += search_adzuna(keyword, city, country, max_days, results)
    if jooble_enabled():
        jobs += search_jooble(keyword, display or city, max_days, results)
    return jobs
