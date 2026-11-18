"""Jobs straight from companies' own careers pages, via the public job-board APIs of the
applicant-tracking systems they use (Greenhouse, Lever, Ashby, SmartRecruiters).

No API keys. A careers board lists only roles that are open right now, so every result is
live. Boards are fetched in parallel and cached for 30 minutes; a board that has moved or
been renamed returns an error and is skipped. Add or remove companies in
config.COMPANY_CAREER_BOARDS.
"""
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from config import COMPANY_CAREER_BOARDS
from hunter.freshness import MAX_POSTING_AGE_DAYS, assess

TIMEOUT = (3.0, 10.0)
LEVER_TIMEOUT = (3.0, 30.0)  # Lever returns every posting with full text in one large response
CACHE_TTL = 1800
GENERIC_TOKENS = {"engineer", "engineering", "developer", "senior", "junior", "lead", "jobs", "job", "role",
                  "specialist", "manager", "the", "and", "for", "with"}

_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; NexusHunt job search)"})


_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
_CACHE_LOCK = threading.Lock()


def _cache_get(key: str) -> Optional[List[Dict[str, Any]]]:
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
    return hit[1] if hit and time.time() - hit[0] < CACHE_TTL else None


def _cache_set(key: str, jobs: List[Dict[str, Any]]) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.time(), jobs)


def clear_cache() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()


def _posting(company: str, ats: str, title: str, location: str, url: str, posted: Any,
             remote: bool = False, description: str = "") -> Dict[str, Any]:
    fresh = assess(posted, max_days=36500, undated_label="Open on company board")
    if fresh["days_ago"] is not None and fresh["days_ago"] > MAX_POSTING_AGE_DAYS:
        # Still open (it's on the live board), just listed a while ago
        fresh = {"date_posted": "", "days_ago": None, "posted_label": "Open on company board"}
    desc = description or f"{title} at {company}. Apply on the company's careers page."
    return {
        "job_title": title.strip(),
        "company": company,
        "location": (location or ("Remote" if remote else "")).strip(),
        "is_remote": remote or bool(re.search(r"\b(remote|anywhere|worldwide)\b", location or "", re.I)),
        "site": f"{company} careers ({ats})",
        "source": f"{ats}: {company}",
        "source_type": "ats",
        "portal": url, "job_url": url, "apply_url": url,
        "salary": "", "salary_range": "",
        "hr_email": "", "has_hr_email": False,
        "description": re.sub(r"\s+", " ", desc)[:300],
        "full_description": desc,
        **fresh,
    }


def _greenhouse(slug: str, company: str) -> List[Dict[str, Any]]:
    r = _session.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", timeout=TIMEOUT)
    r.raise_for_status()
    return [
        _posting(company, "Greenhouse", j.get("title", ""), (j.get("location") or {}).get("name", ""),
                 j.get("absolute_url", ""), j.get("first_published") or j.get("updated_at"))
        for j in r.json().get("jobs", [])
    ]


def _lever(slug: str, company: str) -> List[Dict[str, Any]]:
    r = _session.get(f"https://api.lever.co/v0/postings/{slug}", params={"mode": "json"}, timeout=LEVER_TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json():
        cats = j.get("categories") or {}
        out.append(_posting(company, "Lever", j.get("text", ""), cats.get("location", ""), j.get("hostedUrl", ""),
                            j.get("createdAt"), remote=(j.get("workplaceType") == "remote"),
                            description=j.get("descriptionPlain", "")))
    return out


def _ashby(slug: str, company: str) -> List[Dict[str, Any]]:
    r = _session.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}", timeout=TIMEOUT)
    r.raise_for_status()
    return [
        _posting(company, "Ashby", j.get("title", ""), j.get("location", ""), j.get("jobUrl", ""),
                 j.get("publishedAt"), remote=bool(j.get("isRemote")), description=j.get("descriptionPlain", ""))
        for j in r.json().get("jobs", [])
    ]


def _smartrecruiters(slug: str, company: str) -> List[Dict[str, Any]]:
    r = _session.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings", params={"limit": 100}, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json().get("content", []):
        loc = j.get("location") or {}
        where = ", ".join(x for x in (loc.get("city"), loc.get("country", "").upper()) if x)
        out.append(_posting(company, "SmartRecruiters", j.get("name", ""), where,
                            f"https://jobs.smartrecruiters.com/{slug}/{j.get('id', '')}",
                            j.get("releasedDate"), remote=bool(loc.get("remote"))))
    return out


FETCHERS = {"greenhouse": _greenhouse, "lever": _lever, "ashby": _ashby, "smartrecruiters": _smartrecruiters}


def _fetch_board(board: Tuple[str, str, str]) -> List[Dict[str, Any]]:
    ats, slug, company = board
    key = f"board:{ats}:{slug}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        jobs = [j for j in FETCHERS[ats](slug, company) if j["job_title"] and j["job_url"]]
    except Exception as e:
        print(f"[Company Boards] {company} ({ats}/{slug}) skipped: {type(e).__name__}")
        jobs = []
    _cache_set(key, jobs)
    return jobs


def keyword_tokens(keyword: str) -> List[str]:
    words = [w for w in re.findall(r"[a-z0-9+#.]+", (keyword or "").lower()) if len(w) > 1]
    specific = [w for w in words if w not in GENERIC_TOKENS]
    return specific or words


def title_matches(title: str, tokens: Iterable[str]) -> bool:
    tokens = list(tokens)
    if not tokens:
        return True
    t = title.lower()
    return any(re.search(rf"(?<![a-z0-9]){re.escape(tok)}(?![a-z0-9])", t) for tok in tokens)


def search_company_boards(keyword: str = "", boards: Optional[List[Tuple[str, str, str]]] = None,
                          remote_only: bool = False) -> List[Dict[str, Any]]:
    """Open roles from every configured careers board whose title matches the keyword."""
    boards = boards if boards is not None else COMPANY_CAREER_BOARDS
    tokens = keyword_tokens(keyword)
    with ThreadPoolExecutor(max_workers=16) as pool:
        all_jobs = [j for batch in pool.map(_fetch_board, boards) for j in batch]
    return [
        j for j in all_jobs
        if title_matches(j["job_title"], tokens) and (not remote_only or j["is_remote"])
    ]
