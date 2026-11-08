import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generators.fact_checker import FactChecker, estimate_experience_years
from generators.llm_client import LLMClient
from generators.reviewer_agent import ReviewerAgent
from generators import pipeline

PROFILE = {
    "identity": {"full_name": "Jane Doe"},
    "summary": "Backend engineer building Python and FastAPI services.",
    "technical_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "work_history": [{
        "company": "Acme", "title": "Engineer", "duration": "Jan 2024 - Dec 2024",
        "bullets": ["Cut polling failures from 80% to 0% using FastAPI and PostgreSQL."],
    }],
    "projects": [{"title": "Tool", "technologies": "Python, Docker", "bullets": ["Built a CLI."]}],
    "education": [],
}


def _resume(summary="Backend engineer.", skills="Python, FastAPI", bullets=None):
    return {
        "summary": summary,
        "tailored_subtitle": "Python | FastAPI",
        "core_skills_categorized": [{"category": "Backend", "skills": skills}],
        "work_history": [{"bullets": bullets or ["Cut polling failures from 80% to 0% using FastAPI."]}],
        "projects": [],
    }


def test_clean_draft_has_no_flags():
    res = FactChecker(PROFILE).check(_resume(), "Dear Team, I use Python and FastAPI. Sincerely, Jane")
    assert res["clean"] and res["score"] == 100


def test_unverified_tool_is_flagged():
    res = FactChecker(PROFILE).check(_resume(skills="Python, Kubernetes, Kafka"))
    claims = {f["claim"] for f in res["flags"] if f["type"] == "unverified_tool"}
    assert {"kubernetes", "kafka"} <= claims
    assert res["score"] < 100


def test_unverified_metric_is_flagged_but_profile_metric_is_not():
    res = FactChecker(PROFILE).check(_resume(summary="Improved throughput by 300% and cut failures from 80% to 0%."))
    metrics = {f["claim"] for f in res["flags"] if f["type"] == "unverified_metric"}
    assert "300%" in metrics and "80%" not in metrics


def test_inflated_years_flagged():
    assert round(estimate_experience_years(PROFILE["work_history"]), 1) == 1.0
    res = FactChecker(PROFILE).check(_resume(summary="Engineer with 7 years of experience."))
    assert any(f["type"] == "inflated_experience" for f in res["flags"])


def test_strip_unverified_skills_keeps_real_ones():
    resume = _resume(skills="Python, Kubernetes, Docker, Terraform")
    removed = FactChecker(PROFILE).strip_unverified_skills(resume)
    assert set(removed) == {"Kubernetes", "Terraform"}
    assert resume["core_skills_categorized"][0]["skills"] == "Python, Docker"


def test_reviewer_fails_closed_when_llm_unavailable(monkeypatch):
    monkeypatch.setattr(LLMClient, "generate", lambda self, *a, **k: "")
    audit = ReviewerAgent(PROFILE).audit_and_verify(_resume(), "Dear Team, Sincerely, Jane", "Engineer", "Co", "jd")
    assert audit["status"].startswith("PARTIAL")
    assert audit["ai_review"] is False
    assert audit["hallucination_score"] == 100  # rule checks passed; status still not a verified PASS
    assert "unverified" in audit["reviewer_verdict"].lower()


def test_reviewer_flags_fabrication_even_if_llm_says_perfect(monkeypatch):
    monkeypatch.setattr(
        LLMClient, "generate",
        lambda self, *a, **k: '{"hallucination_score": 100, "verified_claims": ["x"], "flagged_claims": [], "reviewer_verdict": "ok"}',
    )
    audit = ReviewerAgent(PROFILE).audit_and_verify(
        _resume(summary="Led a team of 40 and saved $5M."), "", "Engineer", "Co", "jd"
    )
    assert audit["status"].startswith("FLAGGED")
    assert audit["hallucination_score"] < 100
    assert audit["flagged_claims"]


def test_pipeline_revises_until_clean(monkeypatch):
    drafts = iter([
        _resume(summary="Expert with 300% gains."),   # first draft: fabricated metric
        _resume(summary="Backend engineer."),          # revision: clean
    ])
    seen_feedback = []

    def fake_tailor(self, job_title, company, location, jd_text, feedback=""):
        seen_feedback.append(feedback)
        return next(drafts)

    monkeypatch.setattr(pipeline.ResumeTailorer, "generate_tailored_resume", fake_tailor)
    monkeypatch.setattr(pipeline.CoverLetterGenerator, "generate", lambda self, *a, **k: "Dear Team, Sincerely, Jane")
    monkeypatch.setattr(LLMClient, "generate", lambda self, *a, **k: "")

    resume, letter, audit, _ = pipeline.run_drafter_reviewer(PROFILE, "Engineer", "Co", "Dubai", "jd")
    assert audit["revision_rounds"] == 1
    assert "300%" in seen_feedback[1]
    assert resume["summary"] == "Backend engineer."
    assert audit["corrected_claims"] and not audit["flagged_claims"]
    assert audit["status"].startswith("PARTIAL (CORRECTED")


def test_pipeline_stops_when_no_progress(monkeypatch):
    calls = []

    def fake_tailor(self, *a, feedback="", **k):
        calls.append(feedback)
        return _resume(summary="Cut costs by 300%.")

    monkeypatch.setattr(pipeline.ResumeTailorer, "generate_tailored_resume", fake_tailor)
    monkeypatch.setattr(pipeline.CoverLetterGenerator, "generate", lambda self, *a, **k: "Dear Team")
    monkeypatch.setattr(LLMClient, "generate", lambda self, *a, **k: "")

    _, _, audit, _ = pipeline.run_drafter_reviewer(PROFILE, "Engineer", "Co", "Dubai", "jd", max_revisions=2)
    assert len(calls) == 2  # initial draft + one revision, then stops (same flags)
    assert audit["status"].startswith("FLAGGED")


def test_tailorer_matches_projects_by_name_not_position(monkeypatch):
    from generators.resume_tailorer import ResumeTailorer
    profile = {
        **PROFILE,
        "projects": [
            {"title": "Alpha | First", "technologies": "Python", "bullets": ["Alpha original bullet text here."]},
            {"title": "Beta | Second", "technologies": "Docker", "bullets": ["Beta original bullet text here."]},
        ],
    }
    # Drafter returns Beta first, with rewritten bullets, and tries to alter technologies
    llm_json = (
        '{"tailored_title": "Eng", "tailored_subtitle": "Python", "summary": "S", '
        '"core_skills_categorized": [], "work_history": [], '
        '"projects": [{"title": "Beta | Second", "technologies": "Kafka", "bullets": ["Beta rewritten bullet text here."]}]}'
    )
    monkeypatch.setattr(LLMClient, "generate", lambda self, *a, **k: llm_json)
    out = ResumeTailorer(profile).generate_tailored_resume("Eng", "Co", "Dubai", "jd " * 40)
    assert [p["title"] for p in out["projects"]] == ["Beta | Second"]
    assert out["projects"][0]["technologies"] == "Docker"  # locked, not "Kafka"
    assert out["projects"][0]["bullets"] == ["Beta rewritten bullet text here."]
