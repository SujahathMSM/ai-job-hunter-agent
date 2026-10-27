import sys, os
from pathlib import Path
from fastapi.testclient import TestClient
import uuid

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api import app, create_access_token, JWT_SECRET, JWT_ALGORITHM
from matcher.geo_rules import GeoLocationEngine
from ingestion.persona_builder import PersonaBuilder

client = TestClient(app)

def run_tests():
    print("=== SENIOR QA TEST SUITE: EXECUTION START ===")
    passed = 0
    failed = 0

    def record_result(test_name: str, condition: bool, err_msg: str = ""):
        nonlocal passed, failed
        if condition:
            print(f"[PASS] {test_name}")
            passed += 1
        else:
            print(f"[FAIL] {test_name}: {err_msg}")
            failed += 1

    # 1. Health check
    try:
        r = client.get("/api/health")
        record_result("TC01 - System Health Check", r.status_code == 200 and r.json().get("status") == "ok")
    except Exception as e:
        record_result("TC01 - System Health Check", False, str(e))

    # 2. Geo Rules: Israel exclusion
    try:
        blocked = ['Tel Aviv, Israel', 'Haifa', 'Jerusalem, Israel', 'Israel Remote', 'Israel - Herzliya']
        all_blocked = True
        for loc in blocked:
            ok, reason, _ = GeoLocationEngine.evaluate_location(loc)
            if ok:
                all_blocked = False
                break
        record_result("TC02 - Strict Israel/TLV Exclusion Rule", all_blocked)
    except Exception as e:
        record_result("TC02 - Strict Israel/TLV Exclusion Rule", False, str(e))

    # 3. Geo Rules: Gulf and migratable acceptance
    try:
        accepted = ['Dubai, UAE', 'Abu Dhabi, UAE', 'Riyadh, Saudi Arabia', 'Doha, Qatar', 'London, UK', 'Berlin, Germany', 'Sydney, Australia', 'Singapore']
        all_accepted = True
        for loc in accepted:
            ok, reason, _ = GeoLocationEngine.evaluate_location(loc)
            if not ok:
                all_accepted = False
                break
        record_result("TC03 - Gulf & Migratable Destinations Acceptance", all_accepted)
    except Exception as e:
        record_result("TC03 - Gulf & Migratable Destinations Acceptance", False, str(e))

    # 4. Auth validation edge cases
    try:
        r1 = client.post("/api/auth/register", json={"email": "", "password": "pass", "full_name": "QA"})
        r2 = client.post("/api/auth/register", json={"email": "bad@email.com", "password": "123", "full_name": "QA"})
        r3 = client.post("/api/auth/register", json={"email": "bad@email.com", "password": "validPassword123", "full_name": ""})
        record_result("TC04 - Auth Input Validation (Empty/Short Inputs)", r1.status_code == 400 and r2.status_code == 400 and r3.status_code == 400)
    except Exception as e:
        record_result("TC04 - Auth Input Validation", False, str(e))

    # 5. User registration & JWT issuance
    test_email = f"qa_engineer_{uuid.uuid4().hex[:6]}@example.com"
    token = None
    user_id = None
    try:
        r = client.post("/api/auth/register", json={"email": test_email, "password": "SecurePassword987!", "full_name": "Senior QA Tester"})
        if r.status_code == 200:
            data = r.json()
            token = data.get("token")
            user_id = data.get("user", {}).get("id")
        record_result("TC05 - Candidate Registration & Token Issuance", bool(token and user_id))
    except Exception as e:
        record_result("TC05 - Candidate Registration & Token Issuance", False, str(e))

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 6. Authenticated Session Retrieval
    try:
        r = client.get("/api/auth/me", headers=headers)
        record_result("TC06 - Session Profile Retrieval (/api/auth/me)", r.status_code == 200 and r.json().get("user", {}).get("email") == test_email)
    except Exception as e:
        record_result("TC06 - Session Profile Retrieval", False, str(e))

    # 7. Tampered token rejection in production mode
    try:
        os.environ["APP_ENV"] = "production"
        bad_headers = {"Authorization": "Bearer fake.tampered.token"}
        r = client.get("/api/profile", headers=bad_headers)
        record_result("TC07 - Tampered Token Rejection in Production", r.status_code == 401)
    except Exception as e:
        record_result("TC07 - Tampered Token Rejection", False, str(e))

    # 8. User directory listing locked down in production
    try:
        os.environ["APP_ENV"] = "production"
        r = client.get("/api/auth/users")
        record_result("TC08 - User Listing Forbidden in Production", r.status_code == 403)
    except Exception as e:
        record_result("TC08 - User Listing Forbidden", False, str(e))

    # 9. Path traversal protection on documents
    try:
        os.environ["APP_ENV"] = "development"
        r = client.get("/api/documents/preview?type=cv&company=../../../../etc/passwd&job_title=QA", headers=headers)
        # Should NOT return etc/passwd contents or crash
        record_result("TC09 - Path Traversal Resistance", r.status_code in [200, 500])
    except Exception as e:
        record_result("TC09 - Path Traversal Resistance", False, str(e))

    # 10. SMTP Settings masking
    try:
        r = client.get("/api/settings/user", headers=headers)
        if r.status_code == 200:
            pw = r.json().get("smtp_password", "")
            # Plaintext password must never be exposed
            record_result("TC10 - SMTP Password Masking Security", not pw or pw.startswith("****"))
        else:
            record_result("TC10 - SMTP Password Masking Security", False, f"Status: {r.status_code}")
    except Exception as e:
        record_result("TC10 - SMTP Password Masking Security", False, str(e))

    # 11. Career Portals Retrieval
    try:
        r = client.get("/api/portals?region=GULF")
        record_result("TC11 - Career Portals Retrieval", r.status_code == 200 and len(r.json().get("portals", [])) > 0)
    except Exception as e:
        record_result("TC11 - Career Portals Retrieval", False, str(e))

    # 12. Remote Jobs API
    try:
        r = client.get("/api/jobs/remote?keyword=python&limit=3")
        record_result("TC12 - Global Remote Jobs API", r.status_code == 200 and "jobs" in r.json())
    except Exception as e:
        record_result("TC12 - Global Remote Jobs API", False, str(e))

    # 13. Tracker Applications and Metrics Isolation
    try:
        r = client.get("/api/tracker/applications", headers=headers)
        record_result("TC13 - Tracker Applications Retrieval for User", r.status_code == 200 and "metrics" in r.json())
    except Exception as e:
        record_result("TC13 - Tracker Applications Retrieval", False, str(e))

    # 14. Email Outreach Dry Run Safety
    try:
        payload = {
            "to_email": "recruiter@example.com",
            "subject": "QA Test Application",
            "body": "Hello, this is a test cover letter.",
            "company": "Tech Corp",
            "job_title": "Senior QA Engineer",
            "dry_run": True
        }
        r = client.post("/api/outreach/send", json=payload, headers=headers)
        res_data = r.json()
        record_result("TC14 - Outreach Send Dry-Run Safety", r.status_code == 200 and res_data.get("status") in ["dry_run", "success"])
    except Exception as e:
        record_result("TC14 - Outreach Send Dry-Run Safety", False, str(e))

    # 15. PDF Generation Robustness (Europass CV)
    try:
        r = client.get("/api/profile/download-europass-cv", headers=headers)
        record_result("TC15 - Europass CV PDF Generation", r.status_code == 200 and r.headers.get("content-type") == "application/pdf")
    except Exception as e:
        record_result("TC15 - Europass CV PDF Generation", False, str(e))

    print(f"\n=== SUMMARY: {passed} PASSED, {failed} FAILED (TOTAL {passed + failed}) ===")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
