import os
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from ingestion.cv_parser import CVParser
from ingestion.chat_parser import ChatHistoryParser
from ingestion.linkedin_parser import LinkedInParser
from ingestion.persona_builder import PersonaBuilder
from matcher.geo_rules import GeoLocationEngine
from matcher.jd_analyzer import JobDescriptionAnalyzer
from generators.resume_tailorer import ResumeTailorer
from generators.cover_letter_gen import CoverLetterGenerator
from generators.pdf_builder import PDFResumeBuilder
from hunter.job_search import JobHunter
from outreach.email_sender import EmailDispatcher
from outreach.tracker import ApplicationTracker

def main():
    parser = argparse.ArgumentParser(description="Autonomous Engineering Job Hunter CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # 1. search command
    p_search = subparsers.add_parser("search", help="Search engineering jobs")
    p_search.add_argument("--keyword", default="", help="Filter keyword")
    p_search.add_argument("--region", choices=["ALL", "GULF", "MIGRATABLE"], default="ALL", help="Region filter")

    # 2. apply command
    p_apply = subparsers.add_parser("apply", help="Tailor and apply for a job")
    p_apply.add_argument("--title", required=True, help="Job title")
    p_apply.add_argument("--company", required=True, help="Company name")
    p_apply.add_argument("--location", required=True, help="Location")
    p_apply.add_argument("--email", required=True, help="HR recipient email")
    p_apply.add_argument("--jd", default="", help="Job description text or file path")
    p_apply.add_argument("--live", action="store_true", help="Send live email instead of draft")

    # 3. list-applied command
    p_list = subparsers.add_parser("list", help="List tracked applications")

    args = parser.parse_args()

    if args.command == "search":
        hunter = JobHunter()
        jobs = hunter.search_jobs(keyword=args.keyword, region_filter=args.region)
        print(f"\nFound {len(jobs)} eligible engineering opportunities:")
        print("-" * 75)
        for j in jobs:
            print(f"[{j['id']}] {j['job_title']} | {j['company']}")
            print(f"     Location: {j['location']} (Category: {j['geo_meta'].get('category')})")
            print(f"     HR Contact: {j.get('hr_email')}")
            print("-" * 75)

    elif args.command == "apply":
        # Geo check
        is_el, reason, meta = GeoLocationEngine.evaluate_location(args.location, args.jd)
        if not is_el:
            print(f"\n[REJECTED] Geographic Rule: {reason}")
            sys.exit(1)

        builder = PersonaBuilder()
        profile = builder.get_profile()

        print(f"\n[1/3] Tailoring CV for {args.title} at {args.company}...")
        tailorer = ResumeTailorer(profile)
        tailored = tailorer.generate_tailored_resume(args.title, args.company, args.location, args.jd)

        print("[2/3] Writing impressive cover letter...")
        cl_gen = CoverLetterGenerator(profile)
        cl_text = cl_gen.generate(args.title, args.company, args.location, args.jd)

        print("[3/3] Generating ATS PDFs...")
        pdf_builder = PDFResumeBuilder()
        safe_comp = "".join(c for c in args.company if c.isalnum())
        cv_pdf = BASE_DIR / "data" / "generated_cvs" / f"CV_{safe_comp}.pdf"
        cl_pdf = BASE_DIR / "data" / "generated_cvs" / f"CL_{safe_comp}.pdf"
        pdf_builder.build_resume_pdf(tailored, cv_pdf)
        pdf_builder.build_cover_letter_pdf(cl_text, profile.get("identity", {}).get("full_name", "Candidate"), cl_pdf)

        print(f"      PDFs saved: {cv_pdf.name}, {cl_pdf.name}")

        dispatcher = EmailDispatcher()
        subject = f"Application for {args.title} - {profile.get('identity', {}).get('full_name')} (Engineer)"
        body = f"Dear Hiring Team,\n\nPlease find attached my tailored CV and cover letter for {args.title} at {args.company}."

        res = dispatcher.send_or_draft_application(
            job_title=args.title,
            company=args.company,
            location=args.location,
            recipient_email=args.email,
            subject=subject,
            body_text=body,
            cv_pdf_path=cv_pdf,
            cover_letter_pdf_path=cl_pdf,
            force_live_send=args.live
        )
        print(f"\n[RESULT] {res['message']}")

    elif args.command == "list":
        tracker = ApplicationTracker()
        apps = tracker.list_applications(20)
        print(f"\nTracked Applications ({len(apps)}):")
        print("-" * 80)
        for a in apps:
            print(f"#{a['id']} [{a['status']}] {a['job_title']} @ {a['company']} ({a['location']})")
            print(f"     HR: {a['hr_email']} | Date: {a['applied_date']}")
            print("-" * 80)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
