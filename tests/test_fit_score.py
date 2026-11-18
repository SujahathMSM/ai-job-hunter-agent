import json
from pathlib import Path

import pytest

from matcher.jd_analyzer import JobDescriptionAnalyzer, WEIGHTS, parse_required_years, title_level

PROFILE = json.loads((Path(__file__).resolve().parent.parent / "data" / "master_persona.example.json").read_text(encoding="utf-8"))
PROFILE["work_history"][0]["duration"] = "Jan 2022 - Dec 2025"  # fixed 4.0 years, independent of today's date


@pytest.fixture
def analyzer():
    return JobDescriptionAnalyzer(PROFILE)


@pytest.mark.parametrize("text,expected", [
    ("3-5 years of experience", (3, 5)),
    ("5+ years in backend", (5, None)),
    ("minimum 2 years", (2, None)),
    ("4 years of relevant experience", (4, None)),
    ("Great team", None),
])
def test_parse_required_years(text, expected):
    assert parse_required_years(text) == expected


@pytest.mark.parametrize("title,level", [
    ("Senior Backend Engineer", 3), ("Junior Developer", 1), ("Lead Engineer", 4),
    ("Software Engineering Intern", 0), ("Backend Engineer", None),
])
def test_title_level(title, level):
    assert title_level(title) == level


def test_strong_fit_when_everything_lines_up(analyzer):
    r = analyzer.analyze("Backend Engineer", "Acme", "Dubai, UAE",
                         "Python, FastAPI, PostgreSQL and Docker. 3-5 years of experience. Bachelor's degree.")
    assert r["match_score"] >= 80 and r["fit_label"] == "Strong fit"
    assert r["score_breakdown"]["skills"]["score"] == 1.0
    assert r["score_breakdown"]["experience"]["score"] == 1.0
    assert r["missing_tech"] == []


def test_gaps_lower_the_score_and_are_explained(analyzer):
    r = analyzer.analyze("Senior Backend Engineer", "Acme", "Dubai, UAE",
                         "Python, Kubernetes, Kafka and Terraform. 7+ years. Fintech payments platform.")
    assert r["match_score"] < 60 and r["fit_label"] == "Stretch"
    assert set(r["missing_tech"]) >= {"Kubernetes", "Kafka", "Terraform"}
    reasons = " ".join(r["fit_reasons"])
    assert "missing" in reasons and "short" in reasons


def test_unstated_factors_are_left_out_not_penalised(analyzer):
    r = analyzer.analyze("Backend Engineer", "Acme", "Dubai, UAE", "We use Python and Docker.")
    bd = r["score_breakdown"]
    assert bd["experience"]["score"] is None and bd["education"]["score"] is None and bd["domain"]["score"] is None
    assert r["match_score"] >= 80


def test_no_information_is_labelled_not_scored(analyzer):
    r = analyzer.analyze("Software Engineer", "Acme", "London, UK", "Great team, apply now.")
    assert r["fit_label"] == "Not enough detail"


def test_excluded_location_scores_zero_unless_geo_disabled(analyzer):
    r = analyzer.analyze("Backend Engineer", "Acme", "Tel Aviv, Israel", "Python")
    assert r["match_score"] == 0
    assert analyzer.analyze("Backend Engineer", "Acme", "Tel Aviv, Israel", "Python", enforce_geo=False)["match_score"] > 0


def test_location_text_does_not_trigger_keywords(analyzer):
    # "ai" inside "Dubai" must not count as an AI skill requirement
    r = analyzer.analyze("Office Coordinator", "Acme", "Dubai, UAE", "Based in Dubai.")
    assert "Rag" not in r["matched_skills"] and r["missing_tech"] == []


def test_weights_match_the_documented_model():
    assert WEIGHTS == {"skills": 3, "experience": 2, "seniority": 2, "domain": 2, "projects": 1, "education": 1}


def test_feed_scores_are_replaced_with_users_fit(monkeypatch):
    import api

    class FakeBuilder:
        def __init__(self, user_id):
            self.profile = PROFILE

    monkeypatch.setattr(api, "PersonaBuilder", FakeBuilder)
    jobs = [
        {"job_title": "Kafka Platform Lead", "location": "Dubai", "description": "Kafka, Kubernetes, Terraform. 10+ years.", "match_score": 97},
        {"job_title": "Backend Engineer", "location": "Dubai", "description": "Python, FastAPI, PostgreSQL, Docker. 3-5 years.", "match_score": 91},
    ]
    scored = api.score_jobs_for_user(jobs, "user_test")
    assert scored[0]["job_title"] == "Backend Engineer"
    assert scored[1]["match_score"] < 60 and scored[1]["match_score"] != 97
    assert all("fit_reasons" in j["fit_analysis"] for j in scored)
