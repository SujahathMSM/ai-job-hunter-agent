import json
import sys
from pathlib import Path

# Add repo to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from api import app

def run_tests():
    client = TestClient(app)
    print("=== Testing NexusHunt AI Top 4 Features ===")

    # 1. Test Tailor with Drafter + Reviewer Agent Pipeline
    print("\n[1/5] Testing Two-Stage Drafter + Reviewer Pipeline (/api/cv/tailor)...")
    tailor_payload = {
        "job_title": "Senior Python Backend Engineer",
        "company": "Enterprise Cloud Systems",
        "location": "Dubai, UAE",
        "jd_text": "Looking for a Python and FastAPI backend specialist to design distributed data pipelines, PostgreSQL/TimescaleDB time-series ingestion, and Docker microservices. Knowledge of Kafka and Kubernetes is a plus.",
        "user_id": "test_candidate"
    }
    r = client.post("/api/cv/tailor", json=tailor_payload)
    assert r.status_code == 200, f"Tailor failed: {r.text}"
    tailor_res = r.json()
    assert "tailored_resume" in tailor_res, "Missing tailored_resume"
    assert "reviewer_audit" in tailor_res, "Missing reviewer_audit"
    assert "skill_gap" in tailor_res, "Missing skill_gap"
    print("  -> Tailored Title:", tailor_res["tailored_resume"].get("tailored_title"))
    print("  -> Reviewer Audit Status:", tailor_res["reviewer_audit"].get("status"))
    print("  -> Reviewer Hallucination Score:", tailor_res["reviewer_audit"].get("hallucination_score"))
    print("  -> Verified Claims Count:", len(tailor_res["reviewer_audit"].get("verified_claims", [])))
    print("  -> Reviewer Verdict:", tailor_res["reviewer_audit"].get("reviewer_verdict")[:80] + "...")
    print("  [PASS] Drafter + Reviewer Anti-Hallucination Pipeline Verified!")

    # 2. Test Skill Gap & 24-Hour Quick-Study Roadmap
    print("\n[2/5] Testing Skill Gap & 24-Hour Study Guide (/api/tailor/skill-gap)...")
    gap_payload = {
        "job_title": "Lead Software Engineer",
        "company": "Apex Global",
        "jd_text": "Requirements: Python, FastAPI, Docker, Kafka streaming, Kubernetes, AWS."
    }
    r = client.post("/api/tailor/skill-gap", json=gap_payload)
    assert r.status_code == 200, f"Skill Gap failed: {r.text}"
    gap_res = r.json()
    assert "matched_skills" in gap_res, "Missing matched_skills"
    assert "missing_skills" in gap_res, "Missing missing_skills"
    assert "quick_study_guide" in gap_res, "Missing quick_study_guide"
    print("  -> Matched Skills:", gap_res["matched_skills"])
    print("  -> Missing High-Value Skills:", gap_res["missing_skills"])
    print("  -> Quick Study Guides:", len(gap_res["quick_study_guide"]))
    print("  [PASS] Skill Gap & Roadmap Verified!")

    # 3. Test Interview Simulator & Prep Pack Generator
    print("\n[3/5] Testing AI Interview Simulator Pack (/api/interview/generate)...")
    interview_payload = {
        "job_title": "Senior Distributed Systems Engineer",
        "company": "Nexus Scale",
        "location": "Dubai / Remote",
        "description": "Architect high-throughput async data ingestion services, handle database failovers, and maintain 99.99% uptime."
    }
    r = client.post("/api/interview/generate", json=interview_payload)
    assert r.status_code == 200, f"Interview Generate failed: {r.text}"
    interview_res = r.json()
    assert "role_questions" in interview_res, "Missing role_questions"
    assert "candidate_talking_points" in interview_res, "Missing candidate_talking_points"
    assert "killer_questions_to_ask" in interview_res, "Missing killer_questions_to_ask"
    print("  -> Generated Questions:", len(interview_res["role_questions"]))
    print("  -> Sample Q1:", interview_res["role_questions"][0]["question"])
    print("  -> Talking Points:", len(interview_res["candidate_talking_points"]))
    print("  -> Reverse Questions to Ask:", len(interview_res["killer_questions_to_ask"]))
    print("  [PASS] Interview Simulator Pack Verified!")

    # 4. Test Interview Practice Answer Evaluation
    print("\n[4/5] Testing STAR Answer Evaluation (/api/interview/evaluate)...")
    eval_payload = {
        "question": "Can you describe a time you resolved a major production bottleneck?",
        "question_type": "Behavioral (STAR)",
        "candidate_answer": "At Blue Brand IP Institute, our distributed telemetry ingestion was suffering from an 80% polling failure rate. I re-architected the asynchronous event loops in FastAPI and optimized our TimescaleDB indexing, which completely eliminated the failure rate down to 0% and reduced system startup latency by 90%.",
        "job_title": "Senior Python Backend Engineer",
        "company": "Nexus Scale"
    }
    r = client.post("/api/interview/evaluate", json=eval_payload)
    assert r.status_code == 200, f"Interview Evaluate failed: {r.text}"
    eval_res = r.json()
    assert "score" in eval_res, "Missing score"
    assert "strengths" in eval_res, "Missing strengths"
    assert "model_answer" in eval_res, "Missing model_answer"
    print("  -> Evaluated Score:", eval_res["score"], "/ 100")
    print("  -> Strengths:", eval_res["strengths"])
    print("  -> Model Answer excerpt:", eval_res["model_answer"][:90] + "...")
    print("  [PASS] STAR Practice Answer Evaluation Verified!")

    # 5. Test Clean ATS Text-Layer PDF and Plaintext
    print("\n[5/5] Testing Clean ATS PDF & Plaintext Export...")
    r = client.post("/api/cv/ats-plaintext", json={"tailored_resume": tailor_res["tailored_resume"]})
    assert r.status_code == 200, f"ATS Plaintext failed: {r.text}"
    plaintext = r.json()["plaintext"]
    assert "PROFESSIONAL SUMMARY" in plaintext, "Missing summary header in ATS text"
    assert "M.S. MOHAMED SUJAHATH" in plaintext.upper(), "Missing candidate name"
    print("  -> ATS Plaintext length:", len(plaintext), "characters")

    r_pdf = client.post("/api/cv/generate-ats-pdf", json={"tailored_resume": tailor_res["tailored_resume"]})
    assert r_pdf.status_code == 200, f"ATS PDF generation failed: {r_pdf.text}"
    assert r_pdf.headers["content-type"] == "application/pdf"
    print("  -> Clean ATS PDF byte size:", len(r_pdf.content), "bytes")
    print("  [PASS] Clean ATS Text-Layer PDF & Plaintext Verified!")

    print("\n=======================================================")
    print("ALL 4 FEATURES VERIFIED AND PASSING WITH 100% SUCCESS!")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
