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

    def test_cv_parser_project_parsing(self):
        """Test CVParser correctly handles project lines and bullets without operator precedence bugs."""
        from ingestion.cv_parser import CVParser
        parser = CVParser()
        sample_project_text = """
AeroIntel | Python, FastAPI, Docker
• Engineered high-performance RAG pipeline with dense vector and BM25 search.
• Slashing controller startup times by 90% | Zero polling failures.
evalX | Pytest, LLM-as-a-Judge
• Automated testing harness for AI behavior.
"""
        parsed = parser._parse_project_items(sample_project_text)
        self.assertGreaterEqual(len(parsed), 2)
        # Bullet with pipe '|' must not start a new project!
        aero_bullets = parsed[0]["bullets"]
        self.assertGreaterEqual(len(aero_bullets), 2)
        self.assertIn("Slashing controller startup times", aero_bullets[1])

    def test_hr_finder_regex_and_deduction(self):
        """Test HRFinder email extraction and fallback deduction."""
        from hunter.hr_finder import HRFinder
        text = "Please reach out to talent.acquisition@enterprise.ae or hiring@enterprise.ae for details."
        extracted = HRFinder.extract_emails_from_text(text)
        self.assertIn("talent.acquisition@enterprise.ae", extracted)
        self.assertIn("hiring@enterprise.ae", extracted)

        deduced = HRFinder.deduce_company_hr_email("Emaar Properties")
        self.assertTrue(any("careers@emaarproperties.com" in e for e in deduced))

    def test_hr_finder_global_search(self):
        """Test HRFinder global recruiter and domain dork generator."""
        from hunter.hr_finder import HRFinder
        res = HRFinder.search_global_hr("Careem", domain="careem.com", region="GULF")
        self.assertEqual(res["company"], "Careem")
        self.assertEqual(res["domain"], "careem.com")
        self.assertGreaterEqual(len(res["search_dorks"]), 3)
        self.assertTrue(any("LinkedIn" in d["title"] for d in res["search_dorks"]))

    def test_resume_tailorer_ai_and_systems(self):
        """Test ResumeTailorer generates rich tailored content for AI roles."""
        tailorer = ResumeTailorer(self.profile)
        tailored = tailorer.generate_tailored_resume(
            job_title="Senior RAG & AI Engineer",
            company="Global AI Lab",
            location="Abu Dhabi, UAE",
            jd_text="Looking for an engineer with deep expertise in RAG, vector databases, LangGraph, FastAPI, and production AI."
        )
        self.assertIn("AI", tailored["tailored_title"])
        self.assertGreaterEqual(len(tailored["projects"]), 2)
        self.assertTrue(any("AeroIntel" in p["title"] for p in tailored["projects"]))

    def test_cover_letter_generator_fallback(self):
        """Test CoverLetterGenerator fallback renders without NameError and contains candidate strengths."""
        cl_gen = CoverLetterGenerator(self.profile)
        letter = cl_gen.generate(
            job_title="Distributed Backend Engineer",
            company="Tech Giants FZ-LLC",
            location="Dubai, UAE",
            jd_text="Seeking a backend engineer skilled in Python, high throughput, and database optimization."
        )
        self.assertIn("Tech Giants FZ-LLC", letter)
        self.assertIn("Dubai, UAE", letter)
        self.assertTrue(len(letter) > 200)

    def test_live_scraper_title_filter_and_queries(self):
        """Test LiveJobHunter title legitimacy filter, aggregator page rejection, and broad query expansions."""
        from hunter.live_scraper import LiveJobHunter
        scraper = LiveJobHunter()
        self.assertTrue(scraper._is_legitimate_engineering_job("Senior Backend Engineer"))
        self.assertTrue(scraper._is_legitimate_engineering_job("AI / ML Platform Specialist"))
        self.assertFalse(scraper._is_legitimate_engineering_job("Primary School Teacher"))
        self.assertFalse(scraper._is_legitimate_engineering_job("Restaurant Waiter"))
        # Must reject SEO aggregator category pages (e.g. 417 Vacancies, 4784 Jobs)
        self.assertFalse(scraper._is_legitimate_engineering_job("Rag Agentic Ai Jobs - 417 Vacancies (with Salaries) Oct 2026"))
        self.assertFalse(scraper._is_legitimate_engineering_job("Ai Rag Applications Jobs in Dubai - 4784 Vacancies Oct 2026"))

        expanded = scraper._expand_search_queries("RAG")
        self.assertTrue(any("AI Engineer" in q or "LLM" in q for q in expanded))

    def test_email_dispatcher_draft_creation(self):
        """Test EmailDispatcher builds draft EML with proper date format."""
        dispatcher = EmailDispatcher()
        res = dispatcher.send_or_draft_application(
            job_title="Lead Systems Architect",
            company="Alpha Systems",
            location="Doha, Qatar",
            recipient_email="careers@alphasystems.com",
            subject="Test Application",
            body_text="Dear Team,\n\nPlease review my application.",
            force_live_send=False  # Must save as draft
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["mode"], "DRAFT_SAVED")
        draft_file = Path(res["draft_file"])
        self.assertTrue(draft_file.exists())
        # Clean up test draft
        if draft_file.exists():
            draft_file.unlink()

if __name__ == "__main__":
    unittest.main()
