"""One place that scrapes job boards through JobSpy and returns postings in one shape.

Which boards are searched depends on the country:

    every country   Indeed, LinkedIn, Glassdoor, Google Jobs (LinkedIn + Google only where
                    Indeed has no national site)
    USA / Canada    + ZipRecruiter
    Gulf & MENA     + Bayt
    India           + Naukri
    Bangladesh      + BDJobs
    France          + HelloWork

Glassdoor skips countries it doesn't cover on its own. Every board is queried with an
hours_old filter, and each board runs separately so one blocked or failing board doesn't
lose the results from the others. Jooble is added when its free API key is set (see
hunter/keyed_sources.py).
"""
import logging
import re
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Optional

from hunter.freshness import MAX_POSTING_AGE_DAYS, assess

BASE_SITES = ["indeed", "linkedin", "glassdoor", "google"]
COUNTRY_SITES = {
    "usa": ["zip_recruiter"],
    "canada": ["zip_recruiter"],
    "india": ["naukri"],
    "bangladesh": ["bdjobs"],
    "france": ["hellowork"],
}
BAYT_COUNTRIES = {"united arab emirates", "saudi arabia", "qatar", "kuwait", "bahrain", "oman", "egypt", "jordan", "lebanon", "morocco"}
SITE_LABELS = {
    "indeed": "Indeed", "linkedin": "LinkedIn", "glassdoor": "Glassdoor", "google": "Google Jobs",
    "zip_recruiter": "ZipRecruiter", "bayt": "Bayt", "naukri": "Naukri", "bdjobs": "BDJobs", "hellowork": "HelloWork",
}
PLACEHOLDER_COMPANIES = {"", "nan", "none", "verified employer", "gulf employer", "external job link"}


def _indeed_countries() -> set:
    try:
        from jobspy.model import Country
        return {c.value for c in Country}
    except Exception:
        return set()


INDEED_COUNTRIES = _indeed_countries()


# --- Board health -----------------------------------------------------------------
# JobSpy logs board failures instead of raising them. This handler reads those logs and
# pauses a board that is rate-limiting us (429), whose endpoint is gone (404), or that keeps
# returning nothing, so a 44-city search doesn't hammer a dead board 200 times. It also
# replaces JobSpy's per-request error lines with one line per pause.
LOGGER_TO_SITE = {"ziprecruiter": "zip_recruiter"}
PAUSE_RATE_LIMITED_S = 15 * 60
PAUSE_GONE_S = 6 * 3600
PAUSE_EMPTY_S = 30 * 60
EMPTY_STRIKES = 3


class _BoardHealth(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.paused_until: Dict[str, float] = {}
        self.empty_strikes: Dict[str, int] = {}
        self._state = threading.Lock()

    def _pause(self, site: str, seconds: int, reason: str) -> None:
        with self._state:
            if self.paused_until.get(site, 0) > time.time():
                return
            self.paused_until[site] = time.time() + seconds
        print(f"[Job Sources] {SITE_LABELS.get(site, site)} {reason}; skipping it for {seconds // 60} min")

    def emit(self, record: logging.LogRecord) -> None:
        part = record.name.split(".")[1] if record.name.count(".") >= 1 else ""
        site = LOGGER_TO_SITE.get(part, part)
        msg = record.getMessage().lower()
        if "429" in msg or "blocked" in msg or "rate limit" in msg:
            self._pause(site, PAUSE_RATE_LIMITED_S, "is rate-limiting requests (429)")
        elif "404" in msg or "403" in msg:
            self._pause(site, PAUSE_GONE_S, "rejected the request (404/403)")
        elif "no job data" in msg or "no jobs" in msg:
            with self._state:
                self.empty_strikes[site] = self.empty_strikes.get(site, 0) + 1
                strikes = self.empty_strikes[site]
            if strikes >= EMPTY_STRIKES:
                self._pause(site, PAUSE_EMPTY_S, f"returned no data {strikes} times in a row")

    def ok(self, site: str) -> None:
        with self._state:
            self.empty_strikes[site] = 0

    def available(self, sites: Iterable[str]) -> List[str]:
        now = time.time()
        with self._state:
            return [s for s in sites if self.paused_until.get(s, 0) <= now]


BOARD_HEALTH = _BoardHealth()
_jobspy_logger = logging.getLogger("jobspy")
_jobspy_logger.addHandler(BOARD_HEALTH)
_jobspy_logger.propagate = False


def sites_for_country(country: str) -> List[str]:
    c = (country or "").lower().strip()
    # Indeed and Glassdoor need a country they have a site for; otherwise search LinkedIn and Google only.
    base = BASE_SITES if c in INDEED_COUNTRIES else ["linkedin", "google"]
    sites = list(base) + COUNTRY_SITES.get(c, [])
    if c in BAYT_COUNTRIES:
        sites.append("bayt")
    return sites


def _text(value: Any) -> str:
    s = "" if value is None else str(value).strip()
    return "" if s.lower() in {"nan", "none", "null", "nat"} else s


def _salary(row: Dict[str, Any]) -> str:
    try:
        lo, hi = row.get("min_amount"), row.get("max_amount")
        cur = _text(row.get("currency"))
        per = _text(row.get("interval")) or "yr"
        lo_f = float(lo) if _text(lo) else 0
        hi_f = float(hi) if _text(hi) else 0
        if lo_f > 0 and hi_f > 0:
            return f"{cur} {int(lo_f):,} - {int(hi_f):,} / {per}".strip()
        if lo_f > 0:
            return f"{cur} {int(lo_f):,}+ / {per}".strip()
    except (TypeError, ValueError):
        pass
    return ""


def clean_description(text: str) -> str:
    """Strip markdown noise from JobSpy's markdown descriptions."""
    if not text:
        return ""
    cleaned = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"_{1,2}(.*?)_{1,2}", r"\1", cleaned)
    cleaned = re.sub(r"^\s*[-*•]\s*", "• ", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_row(row: Dict[str, Any], fallback_location: str, max_days: int, hours_window: int) -> Optional[Dict[str, Any]]:
    """Turn one JobSpy row into the app's posting shape, or None if it isn't usable/live."""
    from hunter.hr_finder import HRFinder

    title = _text(row.get("title"))
    company = _text(row.get("company"))
    if not title or company.lower() in PLACEHOLDER_COMPANIES:
        return None

    # The board was queried for postings from the last `hours_window` hours, so an undated
    # result still comes from inside that window.
    days = max(1, hours_window // 24)
    fresh = assess(row.get("date_posted"), max_days, undated_label=f"Posted within {days}d")
    if fresh is None:
        return None

    site = _text(row.get("site")).lower()
    url = _text(row.get("job_url_direct")) or _text(row.get("job_url"))
    desc = clean_description(_text(row.get("description")))
    # JobSpy gives a list, a comma-separated string, or NaN (a float) when there are no emails
    emails = row.get("emails")
    if isinstance(emails, str):
        emails = [e.strip() for e in emails.split(",") if e.strip()]
    elif not isinstance(emails, (list, tuple)):
        emails = []
    found = [e for e in emails if "@" in str(e)] or HRFinder.extract_emails_from_text(desc)
    hr_email = found[0] if found else ""
    snippet = re.sub(r"\s+", " ", desc)[:300].strip() + ("..." if len(desc) > 300 else "")
    encoded = urllib.parse.quote(f'"{company}"')
    salary = _salary(row)

    return {
        "job_title": title,
        "company": company,
        "location": _text(row.get("location")) or fallback_location,
        "site": SITE_LABELS.get(site, site.title() or "Job board"),
        "portal": url,
        "job_url": url,
        "apply_url": url,
        "salary": salary,
        "salary_range": salary,
        "hr_email": hr_email,
        "has_hr_email": bool(hr_email),
        "recruiter_dork": f"https://www.google.com/search?q=site:linkedin.com/in+('Technical+Recruiter'+OR+'Talent+Acquisition'+OR+'HR')+{encoded}",
        "description": snippet,
        "full_description": desc,
        **fresh,
    }


def _scrape_one_site(site: str, search_term: str, city: str, country: str, results_wanted: int, hours_old: int):
    from jobspy import scrape_jobs

    kwargs = dict(
        site_name=[site],
        search_term=search_term,
        location=city,
        results_wanted=results_wanted,
        hours_old=hours_old,
        description_format="markdown",
        verbose=0,
    )
    if country and country.lower() in INDEED_COUNTRIES:
        kwargs["country_indeed"] = country
    if site == "google":
        kwargs["google_search_term"] = f"{search_term} jobs near {city} since last week"
    if site in {"indeed", "linkedin"}:
        kwargs["fetch_description"] = True
    return scrape_jobs(**kwargs)


def scrape_location(
    search_term: str,
    city: str,
    country: str,
    display: Optional[str] = None,
    results_wanted: int = 10,
    max_days: int = MAX_POSTING_AGE_DAYS,
    sites: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    """Search every relevant board for one location (plus Jooble when its key is
    set); returns live, de-duplicated postings."""
    from hunter.keyed_sources import search_keyed_sources

    try:
        import jobspy  # noqa: F401
        chosen = BOARD_HEALTH.available(list(sites) if sites else sites_for_country(country))
    except ImportError:
        chosen = []

    hours_old = max_days * 24
    jobs: List[Dict[str, Any]] = []
    seen = set()

    def add(job: Optional[Dict[str, Any]]) -> None:
        if not job:
            return
        key = (job["job_title"].lower(), job["company"].lower())
        if key not in seen:
            seen.add(key)
            jobs.append(job)

    with ThreadPoolExecutor(max_workers=len(chosen) + 1) as pool:
        keyed = pool.submit(search_keyed_sources, search_term, city, country, display, max_days, results_wanted)
        futures = {
            pool.submit(_scrape_one_site, s, search_term, city, country, results_wanted, hours_old): s
            for s in chosen
        }
        for future, site in futures.items():
            try:
                df = future.result()
            except Exception as e:  # one board failing (blocked, changed markup) must not lose the rest
                print(f"[Job Sources] {SITE_LABELS.get(site, site)} failed for '{search_term}' in {city}: {type(e).__name__}: {e}")
                continue
            if df is None or df.empty:
                continue
            BOARD_HEALTH.ok(site)
            for row in df.to_dict("records"):
                add(normalize_row(row, display or city, max_days, hours_old))
        try:
            for job in keyed.result():
                add(job)
        except Exception as e:
            print(f"[Job Sources] Jooble failed for '{search_term}' in {city}: {type(e).__name__}: {e}")
    return jobs
