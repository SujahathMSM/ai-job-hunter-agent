import json
from pathlib import Path

from generators.fact_checker import FactChecker, format_feedback
from generators.style_checker import find_style_issues

PROFILE = json.loads((Path(__file__).resolve().parent.parent / "data" / "master_persona.example.json").read_text(encoding="utf-8"))


def _kinds(flags):
    return {(f["type"], f["claim"].lower()) for f in flags}


def test_stock_phrases_flagged_with_suggestion():
    flags = find_style_issues({"summary": "Results-driven engineer who spearheaded a migration and leveraged Docker."})
    kinds = _kinds(flags)
    assert ("ai_cliche", "results-driven") in kinds
    assert ("ai_cliche", "spearheaded") in kinds
    assert ("ai_cliche", "leveraged") in kinds
    assert all(f["detail"] for f in flags)


def test_generic_cover_letter_opener_flagged():
    flags = find_style_issues({"cover letter": "Dear Team,\nI am writing to express my interest in the role."})
    assert any(f["claim"].lower().startswith("i am writing to express") for f in flags)


def test_stacked_buzzword_adjectives_flagged():
    flags = find_style_issues({"summary": "Built an innovative, scalable and robust platform."})
    assert any(f["type"] == "stacked_adjectives" for f in flags)
    assert not find_style_issues({"summary": "Built a scalable ingestion service."})


def test_phrases_from_users_own_profile_are_not_flagged():
    corpus = "spearheaded the plant automation rollout"
    flags = find_style_issues({"work bullets": "Spearheaded the plant automation rollout"}, corpus)
    assert flags == []


def test_repeated_bullet_openers_flagged_only_for_drafted_bullets():
    bullets = ["Developed API A", "Developed API B", "Developed API C", "Fixed a bug"]
    assert any(f["type"] == "repeated_opener" for f in find_style_issues({}, "", bullets))
    corpus = " ".join(b.lower() for b in bullets)
    assert not any(f["type"] == "repeated_opener" for f in find_style_issues({}, corpus, bullets))


def test_plain_wording_passes():
    assert find_style_issues({"summary": "Backend engineer. Built the telemetry pipeline in Python and run it on AWS."}) == []


def test_style_flags_do_not_change_grounding_score():
    resume = {"summary": "Results-driven, passionate about cutting-edge systems.", "work_history": [], "projects": []}
    result = FactChecker(PROFILE).check(resume, "")
    assert result["style_flags"]
    assert result["score"] == FactChecker(PROFILE).check({"summary": "Engineer.", "work_history": [], "projects": []}, "")["score"]


def test_feedback_includes_style_rewrites():
    text = format_feedback([], [{"type": "ai_cliche", "claim": "spearheaded", "section": "summary", "detail": "use 'led'."}])
    assert "AI-generated" in text and "spearheaded" in text
