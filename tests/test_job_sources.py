"""Live-postings-only rules and multi-board scraping, with the job boards mocked."""
from datetime import date, timedelta
from unittest import mock

import pandas as pd
import pytest

from hunter import freshness, job_sources
from hunter.freshness import assess, parse_posted_date


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


# --- freshness -----------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    ("2026-11-01", date(2026, 11, 1)),
    ("2026-11-01T10:30:00Z", date(2026, 11, 1)),
    ("Sun, 01 Nov 2026 10:30:00 +0000", date(2026, 11, 1)),
    (1793520000, date(2026, 11, 1)),
    ("Recently", None), ("Trending Now", None), ("", None), (None, None), ("nan", None),
])
def test_parse_posted_date(value, expected):
    assert parse_posted_date(value) == expected


def test_recent_posting_kept_with_label():
    fresh = assess(_days_ago(3), max_days=30)
    assert fresh["days_ago"] == 3 and fresh["posted_label"] == "Posted 3d ago"


def test_old_posting_dropped():
    assert assess(_days_ago(45), max_days=30) is None


def test_undated_posting_dropped_unless_source_vouches():
    assert assess("Recently", max_days=30) is None
    assert assess("", max_days=30, undated_label="Posted within 14d")["posted_label"] == "Posted within 14d"


# --- board selection -------------------------------------------------------------

def test_sites_per_country():
    assert set(job_sources.sites_for_country("usa")) == {"indeed", "linkedin", "glassdoor", "google", "zip_recruiter"}
    assert "bayt" in job_sources.sites_for_country("united arab emirates")
    assert "naukri" in job_sources.sites_for_country("india")
    assert "zip_recruiter" not in job_sources.sites_for_country("uk")


# --- scrape_location ------------------------------------------------------------

def _frame(rows):
    return pd.DataFrame(rows)


def test_scrape_location_merges_boards_drops_stale_and_survives_failures():
    boards = {
        "indeed": _frame([
            {"site": "indeed", "title": "Backend Engineer", "company": "Acme", "location": "Dubai", "date_posted": _days_ago(2), "job_url": "https://x/1", "description": "Python"},
            {"site": "indeed", "title": "Old Role", "company": "Acme", "location": "Dubai", "date_posted": _days_ago(90), "job_url": "https://x/2"},
        ]),
        "linkedin": _frame([
            {"site": "linkedin", "title": "Backend Engineer", "company": "Acme", "location": "Dubai", "date_posted": None, "job_url": "https://x/3"},  # duplicate
            {"site": "linkedin", "title": "Data Engineer", "company": "Beta", "location": "Dubai", "date_posted": None, "job_url": "https://x/4"},
            {"site": "linkedin", "title": "Placeholder", "company": "nan", "location": "Dubai", "date_posted": _days_ago(1)},
        ]),
    }

    def fake(site, *args, **kwargs):
        if site == "glassdoor":
            raise RuntimeError("blocked")
        return boards.get(site, _frame([]))

    with mock.patch.object(job_sources, "_scrape_one_site", side_effect=fake):
        jobs = job_sources.scrape_location("Engineer", "Dubai", "united arab emirates", "Dubai, UAE", max_days=14)

    titles = {(j["job_title"], j["site"]) for j in jobs}
    assert titles == {("Backend Engineer", "Indeed"), ("Data Engineer", "LinkedIn")}
    data_eng = next(j for j in jobs if j["job_title"] == "Data Engineer")
    assert data_eng["posted_label"] == "Posted within 14d" and data_eng["date_posted"] == ""


# --- Dubai and remote feeds -----------------------------------------------------

def test_dubai_results_are_only_live_scraped_postings():
    from hunter import dubai_hunter
    assert not hasattr(dubai_hunter, "VERIFIED_DUBAI_PORTALS")
    live = [{"job_title": "IT Support Engineer", "company": "Gamma", "location": "Dubai", "site": "Bayt",
             "description": "", "full_description": "", "date_posted": _days_ago(1), "days_ago": 1, "posted_label": "Posted 1d ago"}]
    dubai_hunter.GLOBAL_DUBAI_CACHE.clear()
    with mock.patch("hunter.job_sources.scrape_location", return_value=live):
        jobs = dubai_hunter.DubaiJobHunter().search_dubai_jobs(keyword="it support", max_results=10)
    assert [j["company"] for j in jobs] == ["Gamma"]
    assert jobs[0]["category"] == "IT_SUPPORT" and "match_score" not in jobs[0]


def test_remote_feed_keeps_only_dated_recent_or_company_board_posts():
    from hunter import remote_hunter
    hunter = remote_hunter.GlobalRemoteHunter()
    items = [
        {"job_title": "Fresh", "company": "A", "location": "Worldwide", "source": "Remotive", "date_posted": _days_ago(5), "is_worldwide": True},
        {"job_title": "Stale", "company": "B", "location": "Worldwide", "source": "Remotive", "date_posted": _days_ago(60), "is_worldwide": True},
        {"job_title": "Undated", "company": "C", "location": "Worldwide", "source": "Himalayas", "date_posted": "", "is_worldwide": True},
        {"job_title": "Board Role", "company": "D", "location": "Remote", "source": "Greenhouse (GitLab)", "date_posted": "", "is_worldwide": True},
    ]
    remote_hunter.GLOBAL_REMOTE_CACHE.clear()
    with mock.patch.object(hunter, "fetch_remoteok", return_value=items), \
         mock.patch.object(hunter, "fetch_remotive", return_value=[]), \
         mock.patch.object(hunter, "fetch_jobicy", return_value=[]), \
         mock.patch.object(hunter, "fetch_himalayas", return_value=[]), \
         mock.patch.object(hunter, "fetch_weworkremotely", return_value=[]), \
         mock.patch.object(hunter, "fetch_arbeitnow", return_value=[]), \
         mock.patch.object(hunter, "fetch_direct_ats", return_value=[]):
        jobs = hunter.search_all_remote(keyword="zzz-test", limit=10)
    by_title = {j["job_title"]: j for j in jobs}
    assert set(by_title) == {"Fresh", "Board Role"}
    assert by_title["Board Role"]["posted_label"] == "Open on company board"


def test_worldwide_region_accepts_any_country_but_not_excluded():
    from hunter.live_scraper import LiveJobHunter
    assert LiveJobHunter.region_meta("Tokyo, Japan", "Backend Engineer", "WORLDWIDE")["category"] == "WORLDWIDE"
    assert LiveJobHunter.region_meta("Tokyo, Japan", "Backend Engineer", "GULF") is None
    assert LiveJobHunter.region_meta("Tel Aviv, Israel", "Backend Engineer", "WORLDWIDE") is None


def test_nan_emails_and_dates_do_not_crash():
    row = {"site": "indeed", "title": "IT Support Engineer", "company": "Gamma", "location": "Dubai",
           "date_posted": float("nan"), "emails": float("nan"), "job_url": "https://x/9", "description": float("nan")}
    job = job_sources.normalize_row(row, "Dubai", max_days=14, hours_window=14 * 24)
    assert job["hr_email"] == "" and job["posted_label"] == "Posted within 14d"


def test_rate_limited_board_is_paused_then_skipped():
    import logging
    logging.getLogger("jobspy.linkedin").error("response status code 429 (blocked: use a proxy)")
    for _ in range(3):
        logging.getLogger("jobspy.google").error("no job data returned")
    available = job_sources.BOARD_HEALTH.available(["indeed", "linkedin", "google"])
    assert available == ["indeed"]
