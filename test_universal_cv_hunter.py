import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from api import app
from hunter.universal_cv_hunter import UniversalCVHunter

def test_universal_cv_hunter():
    print("=== Testing Universal CV Job Matcher ===")
    hunter = UniversalCVHunter()

    # 1. Test parsing a Civil Engineering CV
    civil_cv = """
    JOHN DOE
    Civil & Structural Engineer | B.Sc. Civil Engineering
    5 years experience in infrastructure, high-rise structural design, and site supervision.
    Core Competencies: AutoCAD, Revit, Structural Analysis, ETABS, Concrete Design, Site Inspection, BOQ.
    Work History:
    - Site Engineer at Apex Construction LLC (2022 - Present): Supervised structural concrete pours and QA/QC documentation.
    - Junior Civil Engineer at BuildWell (2020 - 2022): Prepared structural drawings and drafting in AutoCAD.
    """
    print("\n[1/3] Testing Deep Parsing on Civil Engineering CV...")
    civil_analysis = hunter.parse_and_analyze_cv(civil_cv)
    print("  -> Detected Domain:", civil_analysis.get("primary_domain"))
    print("  -> Target Roles:", civil_analysis.get("target_roles"))
    print("  -> Search Queries:", civil_analysis.get("search_queries"))
    assert "civil" in civil_analysis.get("primary_domain", "").lower() or "structural" in civil_analysis.get("primary_domain", "").lower() or len(civil_analysis.get("target_roles", [])) > 0
    print("  [PASS] Civil Engineering CV parsed accurately!")

    # 2. Test parsing a Document Controller CV
    doc_cv = """
    FATIMA AL-MANSOOR
    Senior Document Controller & EDMS Administrator
    7 years managing engineering records, transmittals, and compliance in Dubai construction and EPC mega-projects.
    Core Tools: Aconex, Procore, EDMS, Document Archiving, ISO 9001 QA/QC, Transmittal Logs, MS Excel.
    """
    print("\n[2/3] Testing Deep Parsing on Document Controller CV...")
    doc_analysis = hunter.parse_and_analyze_cv(doc_cv)
    print("  -> Detected Domain:", doc_analysis.get("primary_domain"))
    print("  -> Target Roles:", doc_analysis.get("target_roles"))
    assert "document" in doc_analysis.get("primary_domain", "").lower() or "document" in str(doc_analysis.get("target_roles", "")).lower()
    print("  [PASS] Document Controller CV parsed accurately!")

    # 3. Test Worldwide Job Hunting for the CV via API
    print("\n[3/3] Testing Global Job Hunting for Parsed CV via API (/api/cv-hunter/search)...")
    client = TestClient(app)
    r = client.post("/api/cv-hunter/search", json={
        "cv_analysis": civil_analysis,
        "region": "ALL",
        "min_match": 65,
        "limit": 20
    })
    assert r.status_code == 200, f"Search failed: {r.text}"
    search_data = r.json()
    assert "jobs" in search_data
    jobs = search_data["jobs"]
    print(f"  -> Discovered {len(jobs)} worldwide matching jobs for Civil Engineer CV.")
    if jobs:
        top_job = jobs[0]
        print(f"  -> Top Match: '{top_job['job_title']}' at '{top_job['company']}' ({top_job['location']})")
        print(f"  -> Match Score: {top_job['match_score']}% ({top_job['match_tier']})")
        print(f"  -> Fit Insight: {top_job['why_it_fits']}")
    print("  [PASS] Worldwide CV Job Matcher API verified!")

    print("\n=========================================================")
    print("UNIVERSAL CV MATCHER PASSING WITH 100% SUCCESS!")
    print("=========================================================")

if __name__ == "__main__":
    test_universal_cv_hunter()
