"""Jooble client, with HTTP mocked."""
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
    monkeypatch.delenv("JOOBLE_API_KEY", raising=False)
    with mock.patch.object(keyed_sources.requests, "get") as get, mock.patch.object(keyed_sources.requests, "post") as post:
        assert keyed_sources.search_keyed_sources("python", "London", "uk", "London, UK", 14, 10) == []
    get.assert_not_called(); post.assert_not_called()


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
    keyed = [keyed_sources._posting("Data Engineer", "Zeta", "London", "https://jb/9",
                                    {"date_posted": "", "days_ago": None, "posted_label": "x"}, "Jooble")]
    with mock.patch.object(job_sources, "_scrape_one_site", return_value=pd.DataFrame([])), \
         mock.patch("hunter.keyed_sources.search_keyed_sources", return_value=keyed):
        jobs = job_sources.scrape_location("data", "London", "uk", "London, UK", max_days=14)
    assert [j["site"] for j in jobs] == ["Jooble"]


def test_adzuna_is_gone():
    assert not hasattr(keyed_sources, "search_adzuna")
