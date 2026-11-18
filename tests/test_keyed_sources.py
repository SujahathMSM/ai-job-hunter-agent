"""Adzuna and Jooble clients, with HTTP mocked."""
from datetime import date, timedelta
from unittest import mock

import pandas as pd

from hunter import job_sources, keyed_sources

RECENT = (date.today() - timedelta(days=3)).isoformat() + "T09:00:00Z"
OLD = (date.today() - timedelta(days=90)).isoformat() + "T09:00:00Z"


def _resp(status=200, payload=None):
    r = mock.Mock(status_code=status, text="err")
    r.json = mock.Mock(return_value=payload or {})
    return r


def test_sources_do_nothing_without_keys(monkeypatch):
    for k in ("ADZUNA_APP_ID", "ADZUNA_APP_KEY", "JOOBLE_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    with mock.patch.object(keyed_sources.requests, "get") as get, mock.patch.object(keyed_sources.requests, "post") as post:
        assert keyed_sources.search_keyed_sources("python", "London", "uk", "London, UK", 14, 10) == []
    get.assert_not_called(); post.assert_not_called()


def test_adzuna_parses_results_and_skips_unsupported_countries(monkeypatch):
    monkeypatch.setenv("ADZUNA_APP_ID", "id"); monkeypatch.setenv("ADZUNA_APP_KEY", "k")
    payload = {"results": [
        {"title": "<strong>Python</strong> Developer", "company": {"display_name": "Acme"}, "location": {"display_name": "London"},
         "redirect_url": "https://adz/1", "created": RECENT, "description": "Build APIs", "salary_min": 50000, "salary_max": 70000},
        {"title": "Old Role", "company": {"display_name": "B"}, "location": {"display_name": "London"}, "redirect_url": "https://adz/2", "created": OLD},
    ]}
    with mock.patch.object(keyed_sources.requests, "get", return_value=_resp(payload=payload)) as get:
        jobs = keyed_sources.search_adzuna("python", "London", "uk", max_days=14)
        assert keyed_sources.search_adzuna("python", "Dubai", "united arab emirates", max_days=14) == []
    assert get.call_count == 1
    assert "/jobs/gb/search/1" in get.call_args.args[0]
    assert get.call_args.kwargs["params"]["max_days_old"] == 14
    assert [j["job_title"] for j in jobs] == ["Python Developer"]
    assert jobs[0]["company"] == "Acme" and jobs[0]["salary"] == "50,000 - 70,000 / yr" and jobs[0]["days_ago"] == 3


def test_jooble_parses_results_and_drops_undated(monkeypatch):
    monkeypatch.setenv("JOOBLE_API_KEY", "jk")
    payload = {"jobs": [
        {"title": "Backend Engineer", "company": "Gamma", "location": "Dubai", "link": "https://jb/1", "updated": RECENT, "snippet": "Python", "source": "bayt.com", "salary": ""},
        {"title": "No Date", "company": "Delta", "location": "Dubai", "link": "https://jb/2", "updated": ""},
        {"title": "Old", "company": "Eps", "location": "Dubai", "link": "https://jb/3", "updated": OLD},
    ]}
    with mock.patch.object(keyed_sources.requests, "post", return_value=_resp(payload=payload)) as post:
        jobs = keyed_sources.search_jooble("backend", "Dubai, UAE", max_days=14)
    assert post.call_args.args[0] == "https://jooble.org/api/jk"
    assert post.call_args.kwargs["json"]["keywords"] == "backend"
    assert [j["company"] for j in jobs] == ["Gamma"] and jobs[0]["site"] == "Jooble (bayt.com)"


def test_errors_are_logged_not_raised(monkeypatch):
    monkeypatch.setenv("JOOBLE_API_KEY", "jk")
    with mock.patch.object(keyed_sources.requests, "post", return_value=_resp(status=403)):
        assert keyed_sources.search_jooble("x", "Dubai", 14) == []
    with mock.patch.object(keyed_sources.requests, "post", side_effect=keyed_sources.requests.ConnectionError()):
        assert keyed_sources.search_jooble("x", "Dubai", 14) == []


def test_keyed_results_merge_into_location_search():
    keyed = [keyed_sources._posting("Data Engineer", "Zeta", "London", "https://adz/9",
                                    {"date_posted": "", "days_ago": None, "posted_label": "x"}, "Adzuna")]
    with mock.patch.object(job_sources, "_scrape_one_site", return_value=pd.DataFrame([])), \
         mock.patch("hunter.keyed_sources.search_keyed_sources", return_value=keyed):
        jobs = job_sources.scrape_location("data", "London", "uk", "London, UK", max_days=14)
    assert [j["site"] for j in jobs] == ["Adzuna"]
