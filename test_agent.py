import os
import sys
import unittest
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from matcher.geo_rules import GeoLocationEngine
from matcher.jd_analyzer import JobDescriptionAnalyzer
from ingestion.persona_builder import PersonaBuilder
from generators.resume_tailorer import ResumeTailorer
from generators.cover_letter_gen import CoverLetterGenerator
from generators.pdf_builder import PDFResumeBuilder
from hunter.job_search import JobHunter
from outreach.tracker import ApplicationTracker
from outreach.email_sender import EmailDispatcher

class TestJobHunterAgent(unittest.TestCase):

    def setUp(self):
        self.builder = PersonaBuilder()
        self.profile = self.builder.get_profile()

    def test_geo_rules_strict_israel_exclusion(self):
        """Test that any job mentioning Israel or Israeli cities is strictly blocked."""
        # 1. Job in Tel Aviv, Israel
        is_el, reason, meta = GeoLocationEngine.evaluate_location("Tel Aviv, Israel", "Senior Software Engineer")
        self.assertFalse(is_el, "Should reject job in Israel")
        self.assertIn("STRICT_EXCLUSION", reason)

        # 2. Job with Israel in description
        is_el2, reason2, meta2 = GeoLocationEngine.evaluate_location("Remote", "Working with engineering teams in Israel")
        self.assertFalse(is_el2, "Should reject job with company or office in Israel")
        self.assertIn("STRICT_EXCLUSION", reason2)

    def test_geo_rules_gulf_acceptance(self):
        """Test that Gulf locations pass with GULF category."""
        locations = ["Dubai, UAE", "Riyadh, Saudi Arabia", "Doha, Qatar", "Muscat, Oman", "Kuwait City", "Manama, Bahrain"]
        for loc in locations:
            is_el, reason, meta = GeoLocationEngine.evaluate_location(loc)
            self.assertTrue(is_el, f"Should accept Gulf location: {loc}")
            self.assertEqual(meta.get("category"), "GULF")

    def test_geo_rules_migratable_acceptance(self):
        """Test that easily migratable destinations for Sri Lankan engineers pass."""
        locations = ["Singapore", "Berlin, Germany", "London, UK", "Sydney, Australia", "Auckland, New Zealand"]
        for loc in locations:
            is_el, reason, meta = GeoLocationEngine.evaluate_location(loc)
            self.assertTrue(is_el, f"Should accept migratable location: {loc}")
            self.assertEqual(meta.get("category"), "MIGRATABLE_GLOBAL")

    def test_pdf_generation(self):
        """Test compiling ATS Resume and Cover letter into valid PDFs."""
        pdf_builder = PDFResumeBuilder()
        out_cv = BASE_DIR / "data" / "test_cv.pdf"
        out_cl = BASE_DIR / "data" / "test_cl.pdf"

        resume_data = {
            "identity": {
                "full_name": "Kasun Perera",
                "professional_title": "Senior Systems Engineer",
                "email": "kasun@example.com",
                "phone": "+94 77 123 4567",
                "current_location": "Colombo, Sri Lanka",
                "linkedin": "linkedin.com/in/kasun-perera",
                "github": "github.com/kasun-eng"
            },
            "tailored_title": "Senior Systems & Cloud Engineer",
            "summary": "Engineering professional based in Sri Lanka, ready for relocation to Dubai.",
            "skills": ["Systems Engineering", "Python", "Docker", "AWS", "Root Cause Analysis"],
            "technical_stack": ["Linux", "Kubernetes", "PostgreSQL", "CI/CD"],
            "projects": [
                {
                    "title": "Automated Telemetry Pipeline",
                    "description": "Engineered high-throughput data processing pipeline handling 50k events/sec.",
                    "technologies": ["Python", "AWS", "Docker"]
                }
            ],
            "experience": [
                {
                    "title": "Lead Engineer",
                    "company": "Apex Global Solutions",
                    "started_on": "2021",
                    "finished_on": "Present",
                    "description": "Architected distributed systems and optimized performance bottlenecks."
                }
            ],
            "education": [{"details": "B.Sc. Engineering (Hons), University of Moratuwa"}]
        }

        # Build Resume PDF
        res_path = pdf_builder.build_resume_pdf(resume_data, out_cv)
        self.assertTrue(res_path.exists())
        self.assertGreater(os.path.getsize(res_path), 1000)

        # Build Cover Letter PDF
        cl_text = "Dear Hiring Team,\n\nI am writing to express my strong enthusiasm for the role in Dubai..."
        cl_path = pdf_builder.build_cover_letter_pdf(cl_text, "Kasun Perera", out_cl)
        self.assertTrue(cl_path.exists())
        self.assertGreater(os.path.getsize(cl_path), 1000)

    def test_job_analyzer_and_ats_score(self):
        """Test ATS analyzer for engineering alignment."""
        analyzer = JobDescriptionAnalyzer(self.profile)
        res = analyzer.analyze(
            job_title="Software & Systems Engineer",
            company="Tech Corp",
            location="Dubai, UAE",
            jd_text="Looking for an engineer with skills in Python, Docker, cloud systems, and problem solving."
        )
        self.assertTrue(res["geo_eligible"])
        self.assertTrue(res["is_engineering"])
        self.assertGreaterEqual(res["match_score"], 40)

    def test_sqlite_tracker_and_dispatch(self):
        """Test tracking applications in SQLite and drafting dispatch."""
        tracker = ApplicationTracker()
        app_id = tracker.add_application(
            job_title="Test Engineer",
            company="Test Co",
            location="Dubai, UAE",
            hr_email="hr@testco.com",
            status="Drafted",
            notes="Automated test entry"
        )
        self.assertIsInstance(app_id, int)
        apps = tracker.list_applications(1)
        self.assertEqual(apps[0]["company"], "Test Co")

if __name__ == "__main__":
    unittest.main()
