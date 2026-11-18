"""Company careers-page source, with the ATS APIs mocked."""
from datetime import date, timedelta
from unittest import mock

import pytest

from hunter import company_boards, job_sources

RECENT = (date.today() - timedelta(days=2)).isoformat()
OLD = (date.today() - timedelta(days=200)).isoformat()

PAYLOADS = {
    "greenhouse": {"jobs": [
        {"title": "Senior Python Engineer", "absolute_url": "https://gh/1", "location": {"name": "Dubai, UAE"}, "updated_at": RECENT},
        {"title": "Account Executive", "absolute_url": "https://gh/2", "location": {"name": "London"}, "updated_at": RECENT},
        {"title": "Python Platform Engineer", "absolute_url": "https://gh/3", "location": {"name": "Remote - Worldwide"}, "updated_at": OLD},
    ]},
    "lever": [
        {"text": "Backend Engineer (Python)", "hostedUrl": "https://lv/1", "categories": {"location": "Berlin"}, "createdAt": 1793520000000, "workplaceType": "onsite"},
    ],
    "ashby": {"jobs": [
        {"title": "Python Developer", "jobUrl": "https://ab/1", "location": "Anywhere", "isRemote": True, "publishedAt": RECENT},
    ]},
    "smartrecruiters": {"content": [
        {"id": "123", "name": "Python Data Engineer", "releasedDate": RECENT, "location": {"city": "Riyadh", "country": "sa", "remote": False}},
    ]},
}


def fake_get(url, **kwargs):
    resp = mock.Mock()
    resp.raise_for_status = mock.Mock()
    for ats, host in (("greenhouse", "greenhouse"), ("lever", "lever"), ("ashby", "ashby"), ("smartrecruiters", "smartrecruiters")):
        if host in url:
            resp.json = mock.Mock(return_value=PAYLOADS[ats])
            return resp
    raise AssertionError(url)


BOARDS = [("greenhouse", "acme", "Acme"), ("lever", "beta", "Beta"), ("ashby", "gamma", "Gamma"), ("smartrecruiters", "Delta", "Delta")]


@pytest.fixture(autouse=True)
def _fresh_cache():
    company_boards.clear_cache()
    yield
    company_boards.clear_cache()


def test_all_four_ats_parsed_and_filtered_by_keyword():
    with mock.patch.object(company_boards._session, "get", side_effect=fake_get):
        jobs = company_boards.search_company_boards("Python Developer", boards=BOARDS)
    titles = {j["job_title"] for j in jobs}
    assert titles == {"Senior Python Engineer", "Python Platform Engineer", "Backend Engineer (Python)", "Python Developer", "Python Data Engineer"}
    assert all(j["source_type"] == "ats" and j["job_url"] for j in jobs)
    sr = next(j for j in jobs if j["company"] == "Delta")
    assert sr["job_url"] == "https://jobs.smartrecruiters.com/Delta/123" and sr["location"] == "Riyadh, SA"


def test_open_board_roles_are_live_even_when_listed_long_ago():
    with mock.patch.object(company_boards._session, "get", side_effect=fake_get):
        jobs = company_boards.search_company_boards("python", boards=BOARDS[:1])
    old = next(j for j in jobs if j["job_title"] == "Python Platform Engineer")
    assert old["posted_label"] == "Open on company board" and old["date_posted"] == ""
    recent = next(j for j in jobs if j["job_title"] == "Senior Python Engineer")
    assert recent["days_ago"] == 2


def test_remote_only_filter():
    with mock.patch.object(company_boards._session, "get", side_effect=fake_get):
        jobs = company_boards.search_company_boards("python", boards=BOARDS, remote_only=True)
    assert {j["job_title"] for j in jobs} == {"Python Platform Engineer", "Python Developer"}


def test_failing_board_is_skipped_not_fatal():
    def flaky(url, **kwargs):
        if "lever" in url:
            raise ConnectionError("gone")
        return fake_get(url, **kwargs)
    with mock.patch.object(company_boards._session, "get", side_effect=flaky):
        jobs = company_boards.search_company_boards("python", boards=BOARDS)
    assert "Beta" not in {j["company"] for j in jobs} and len(jobs) == 4


def test_keyword_tokens_ignore_generic_words():
    assert company_boards.keyword_tokens("Senior Python Developer") == ["python"]
    assert company_boards.keyword_tokens("Software Engineer") == ["software"]
    assert company_boards.keyword_tokens("Engineer") == ["engineer"]


def test_careers_pages_feed_the_job_hunter_stream():
    from hunter.live_scraper import LiveJobHunter
    board_jobs = [company_boards._posting("Acme", "Greenhouse", "Python Backend Engineer", "Dubai, UAE", "https://gh/9", RECENT)]
    with mock.patch("hunter.live_scraper.search_company_boards", return_value=board_jobs), \
         mock.patch("hunter.live_scraper.scrape_location", return_value=[]):
        jobs = list(LiveJobHunter().stream_live("python", "GULF", max_results=5))
    assert [j["company"] for j in jobs] == ["Acme"]


def test_countries_without_indeed_use_linkedin_and_google():
    assert job_sources.sites_for_country("kenya") == ["linkedin", "google"]
