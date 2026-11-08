import pytest
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outreach.tracker import ApplicationTracker
from ingestion.persona_builder import PersonaBuilder
from generators.resume_tailorer import ResumeTailorer
from matcher.geo_rules import GeoLocationEngine
from outreach.email_sender import EmailDispatcher

def test_password_auth_rejects_empty_credentials():
    tracker = ApplicationTracker()
    # Attempting to authenticate with empty password or non-existent user must fail
    assert tracker.authenticate_user("default_admin@example.com", "") is None
    assert tracker.authenticate_user("nonexistent@example.com", "any_password") is None
    assert tracker.authenticate_user("", "password") is None

def test_non_default_user_gets_isolated_profile():
    # User ff9988 must start with generic candidate template
    pb = PersonaBuilder(user_id="user_test_isolation_9988")
    profile = pb.profile
    assert profile["identity"]["full_name"] == "Engineer Candidate"
    assert profile.get("education", []) == []
    assert profile.get("work_history", []) == []

def test_non_default_user_canonicalize_preserves_authentic_data():
    pb = PersonaBuilder(user_id="user_custom_engineer_123")
    custom_cv = [{
        "candidate_name": "Jane Doe",
        "contact_info": {"email": "jane@example.com", "phone": "+44 7000 000000"},
        "parsed_experience": [{
            "company": "Acme Aerospace",
            "title": "Avionics Systems Engineer",
            "duration": "2021 - 2024",
            "bullets": ["Engineered flight control telemetry pipelines with fault-tolerant redundancy."]
        }],
        "parsed_education": [{
            "degree": "BSc Aerospace Engineering",
            "institution": "Imperial College London",
            "duration": "2017 - 2021"
        }],
        "parsed_projects": [{
            "title": "Satellite Telemetry Link",
            "technologies": "C++, Python",
            "bullets": ["Implemented real-time ground station packet decoding."]
        }],
        "sections": {"skills": "C++, Python, Linux, Telemetry"}
    }]
    
    built = pb.build_from_sources(custom_cv, chat_insights=[])
    
    # Must preserve Jane's real company and university, NOT overwrite with Blue Brand or Moratuwa
    companies = [w["company"] for w in built["work_history"]]
    institutions = [e["institution"] for e in built["education"]]
    
    assert "Acme Aerospace" in companies
    assert "Blue Brand - Advanced R&D and IP Institute" not in companies
    assert "Imperial College London" in institutions
    assert "University of Moratuwa" not in institutions

def test_resume_tailorer_fact_locking():
    mock_profile = {
        "identity": {"full_name": "Alice Smith", "current_location": "London"},
        "core_skills_categorized": [{"category": "Backend", "skills": "Go, Python, Docker"}],
        "technical_stack": ["Go", "Python", "Docker"],
        "work_history": [{
            "company": "Fintech Solutions UK",
            "branch": "London",
            "title": "Software Engineer",
            "duration": "Jan 2022 - Present",
            "bullets": ["Built high-throughput payment settlement microservices."]
        }],
        "projects": [{
            "title": "Ledger Engine",
            "technologies": "Go, PostgreSQL",
            "bullets": ["Engineered double-entry bookkeeping core."]
        }],
        "education": [{
            "degree": "BSc Computer Science",
            "institution": "University of Edinburgh",
            "duration": "2018 - 2022"
        }],
        "certifications": []
    }
    tailorer = ResumeTailorer(master_profile=mock_profile)
    tailored = tailorer.generate_tailored_resume(
        job_title="Senior Python Backend Developer",
        company="Global Payments Inc",
        location="Dubai, UAE",
        jd_text="Looking for an engineer to build scalable payment pipelines."
    )
    # Verification: company name, title, duration, and institution must remain immutable
    assert tailored["work_history"][0]["company"] == "Fintech Solutions UK"
    assert tailored["work_history"][0]["title"] == "Software Engineer"
    assert tailored["work_history"][0]["duration"] == "Jan 2022 - Present"
    assert tailored["education"][0]["institution"] == "University of Edinburgh"

def test_geo_rules_male_bug_fix():
    # A job in Lagos mentioning male/female candidates must NOT match Male (Maldives)
    is_el, reason, meta = GeoLocationEngine.evaluate_location(
        location_str="Lagos, Nigeria",
        job_text="Equal opportunity employer. Open to qualified male and female applicants for administrative role."
    )
    assert not is_el
    assert meta.get("category") != "MIGRATABLE_GLOBAL"

    # A genuine job in Male, Maldives MUST match
    is_el_real, reason_real, meta_real = GeoLocationEngine.evaluate_location(
        location_str="Male, Maldives",
        job_text="Hiring IT Systems Engineer for resort operations."
    )
    assert is_el_real
    assert meta_real.get("category") == "MIGRATABLE_GLOBAL"

def test_geo_rules_illinois_not_excluded():
    # Chicago, IL must NOT be excluded as Israel
    is_el, reason, meta = GeoLocationEngine.evaluate_location(
        location_str="Chicago, IL, USA",
        job_text="Senior Python Backend Engineer for trading firm in Chicago, IL. Must reside in US."
    )
    assert meta.get("flagged_country") != "Israel"

    # Tel Aviv, Israel MUST be strictly excluded
    is_el_isr, reason_isr, meta_isr = GeoLocationEngine.evaluate_location(
        location_str="Tel Aviv, Israel",
        job_text="Software developer position."
    )
    assert not is_el_isr
    assert meta_isr.get("category") == "EXCLUDED"
    assert "Israel" in reason_isr or "Tel Aviv" in reason_isr

def test_safe_mode_enforced_in_email_dispatcher(monkeypatch):
    import outreach.email_sender
    monkeypatch.setattr(outreach.email_sender, "SAFE_MODE", True)
    dispatcher = EmailDispatcher()
    # Even if client requests dry_run=False, server-side SAFE_MODE must prevent live SMTP
    result = dispatcher.dispatch(
        to_email="hr@example.com",
        subject="Application for Software Engineer",
        body_text="Dear Hiring Team...",
        job_title="Software Engineer",
        company="Example Corp",
        location="Dubai, UAE",
        dry_run=False,
        user_id="test_user_safe"
    )
    assert result.get("mode") == "DRAFT_SAVED"
    assert "draft_file" in result
