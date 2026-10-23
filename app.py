import os
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd

# Ensure project path is accessible
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import (
    UPLOADS_DIR, GENERATED_DIR, DRAFTS_DIR, PROFILE_PATH,
    GULF_COUNTRIES, MIGRATABLE_COUNTRIES, EXCLUDED_COUNTRIES,
    DEFAULT_LLM_PROVIDER, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SENDER_NAME
)
from ingestion.cv_parser import CVParser
from ingestion.chat_parser import ChatHistoryParser
from ingestion.linkedin_parser import LinkedInParser
from matcher.geo_rules import GeoLocationEngine
from matcher.jd_analyzer import JobDescriptionAnalyzer
import importlib
import generators.pdf_builder
importlib.reload(generators.pdf_builder)
from generators.pdf_builder import PDFResumeBuilder
import generators.resume_tailorer
importlib.reload(generators.resume_tailorer)
from generators.resume_tailorer import ResumeTailorer
import generators.cover_letter_gen
importlib.reload(generators.cover_letter_gen)
from generators.cover_letter_gen import CoverLetterGenerator
import ingestion.persona_builder
importlib.reload(ingestion.persona_builder)
from ingestion.persona_builder import PersonaBuilder
import hunter.live_scraper
importlib.reload(hunter.live_scraper)
import hunter.job_search
importlib.reload(hunter.job_search)
from hunter.job_search import JobHunter

from hunter.hr_finder import HRFinder
from outreach.email_sender import EmailDispatcher
from outreach.tracker import ApplicationTracker

# Page Configuration
st.set_page_config(
    page_title="AI Engineer Job Hunter Agent (Gulf & Global)",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f2942;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .badge-gulf {
        background-color: #0284c7;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-migratable {
        background-color: #059669;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-excluded {
        background-color: #dc2626;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
st.session_state.persona_builder = PersonaBuilder()
current_work = st.session_state.get("active_profile", {}).get("work_history", [])
if (
    "active_profile" not in st.session_state
    or len(current_work) > 3
    or any(w.get("company") == "Engineering Organization" for w in current_work)
    or any(w.get("company") == "Commercial Engineering Experience" for w in current_work)
):
    st.session_state.active_profile = st.session_state.persona_builder.get_profile()
if "selected_job" not in st.session_state:
    st.session_state.selected_job = None
if "tailored_resume" not in st.session_state:
    st.session_state.tailored_resume = None
if "cover_letter_text" not in st.session_state:
    st.session_state.cover_letter_text = None
if "cv_pdf_path" not in st.session_state:
    st.session_state.cv_pdf_path = None
if "cl_pdf_path" not in st.session_state:
    st.session_state.cl_pdf_path = None

tracker = ApplicationTracker()
hunter = JobHunter()
dispatcher = EmailDispatcher()

# Sidebar: Regional Directives & Mode
with st.sidebar:
    st.title("🎯 Job Hunter Agent")
    st.markdown("**Focus Areas:**")
    st.markdown('<span class="badge-gulf">Gulf Countries</span> UAE, KSA, Qatar, Oman, Kuwait, Bahrain', unsafe_allow_html=True)
    st.markdown('<span class="badge-migratable">Migratable Pathways</span> Singapore, UK, Germany, Australia, NZ', unsafe_allow_html=True)
    st.markdown('<span class="badge-excluded">Strict Blocklist</span> Israel (Strictly excluded)', unsafe_allow_html=True)
    st.divider()

    st.subheader("🛡️ Safety & Sending Mode")
    safe_review_mode = st.toggle("Safe Review Mode (Drafts First)", value=True, help="When enabled, applications are saved as draft EML files and queued for review rather than sent directly.")

    st.divider()
    try:
        from generators.llm_client import LLMClient
        _client = LLMClient()
        if hasattr(_client, "is_active"):
            _llm_info = _client.is_active()
        else:
            _has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"))
            _llm_info = {"active": _has_key, "provider": "Google Gemini" if _has_key else "Offline"}
    except Exception:
        _has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"))
        _llm_info = {"active": _has_key, "provider": "Google Gemini" if _has_key else "Offline"}

    if _llm_info.get("active"):
        st.markdown(f"**AI Engine:** 🟢 `{_llm_info.get('provider')}` (Live API)")
    else:
        st.markdown("**AI Engine:** 🟡 `Local Offline Engine`")

    st.divider()
    metrics = tracker.get_metrics()
    st.markdown("### 📊 Application Stats")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Queued", metrics["total"])
    col_m2.metric("Sent Live", metrics["applied"])
    col_m3, col_m4 = st.columns(2)
    col_m3.metric("Drafts", metrics["drafted"])
    col_m4.metric("Interviews", metrics["interviews"])

# Main Title
st.markdown('<div class="main-header">Autonomous Engineering Job Hunter & Application Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Intakes your CVs, Claude / Gemini / ChatGPT histories, and LinkedIn profile to synthesize your authentic persona, discover engineering roles across Gulf & Global pathways, tailor ATS-optimized CVs & Cover Letters, and dispatch applications to HR.</div>', unsafe_allow_html=True)

# Tabs
tab_persona, tab_hunter, tab_tailor, tab_outreach, tab_tracker, tab_settings = st.tabs([
    "🧠 1. Understand Me (Data Intake)",
    "🔎 2. Job Hunter & Matcher",
    "📝 3. Tailor CV & Cover Letter",
    "🚀 4. HR Email & Dispatch",
    "📋 5. Application Tracker",
    "⚙️ 6. Settings"
])

# ==========================================
# TAB 1: UNDERSTAND ME (INTAKE & PERSONA)
# ==========================================
with tab_persona:
    st.header("🧠 Data Intake & Persona Synthesis")
    st.write("Upload your existing CVs, chat history exports from Claude / Gemini / ChatGPT, and your LinkedIn profile. The agent will read between the lines, uncover your real engineering projects and problem-solving depth, and build a unified Master Persona.")

    col_u1, col_u2, col_u3 = st.columns(3)

    with col_u1:
        st.subheader("📄 1. Your CVs")
        uploaded_cvs = st.file_uploader(
            "Upload one or more CVs (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            key="upload_cvs"
        )

    with col_u2:
        st.subheader("💬 2. AI Chat Histories")
        uploaded_chats = st.file_uploader(
            "Upload Claude, Gemini, or ChatGPT exports (JSON or TXT)",
            type=["json", "txt", "md"],
            accept_multiple_files=True,
            key="upload_chats",
            help="ChatGPT: conversations.json. Claude: export JSON. Gemini: JSON/text export."
        )

    with col_u3:
        st.subheader("💼 3. LinkedIn Profile")
        uploaded_linkedin = st.file_uploader(
            "Upload LinkedIn PDF or archive CSV",
            type=["pdf", "csv"],
            key="upload_linkedin",
            help="Use LinkedIn 'More -> Save to PDF' or exported data CSV."
        )

    if st.button("🚀 Analyze Everything & Build Master Persona", type="primary", use_container_width=True):
        with st.spinner("Parsing CVs, mining chat conversations for technical projects, and validating LinkedIn profile..."):
            cv_parser = CVParser()
            chat_parser = ChatHistoryParser()
            linkedin_parser = LinkedInParser()

            parsed_cvs = []
            if uploaded_cvs:
                for f in uploaded_cvs:
                    dest = UPLOADS_DIR / f.name
                    with open(dest, "wb") as out:
                        out.write(f.getbuffer())
                    parsed_cvs.append(cv_parser.parse_file(dest))

            chat_insights = []
            if uploaded_chats:
                for f in uploaded_chats:
                    dest = UPLOADS_DIR / f.name
                    with open(dest, "wb") as out:
                        out.write(f.getbuffer())
                    chat_insights.extend(chat_parser.parse_any(dest))

            linkedin_data = {}
            if uploaded_linkedin:
                dest = UPLOADS_DIR / uploaded_linkedin.name
                with open(dest, "wb") as out:
                    out.write(uploaded_linkedin.getbuffer())
                linkedin_data = linkedin_parser.parse_any(dest)

            # Build Persona
            new_profile = st.session_state.persona_builder.build_from_sources(
                cv_data_list=parsed_cvs,
                chat_insights=chat_insights,
                linkedin_data=linkedin_data
            )
            st.session_state.active_profile = new_profile
            st.success("✅ Master Persona successfully synthesized and updated!")

    # Master Persona Viewer / Editor
    st.divider()
    st.subheader("👤 Synthesized Master Professional Profile")
    p = st.session_state.active_profile

    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.markdown("#### 📌 Identity & International Relocation")
        id_info = p.get("identity", {})
        c_name = st.text_input("Full Name", value=id_info.get("full_name", ""))
        c_title = st.text_input("Professional Title", value=id_info.get("professional_title", ""))
        c_email = st.text_input("Email", value=id_info.get("email", ""))
        c_phone = st.text_input("Phone", value=id_info.get("phone", ""))
        c_loc = st.text_input("Current Location", value=id_info.get("current_location", "Colombo, Sri Lanka"))
        c_reloc = st.text_input("Relocation Status", value=id_info.get("relocation_status", "Immediately ready for Gulf & Global relocation"))

        summary = st.text_area("Executive Summary", value=p.get("summary", ""), height=130)

    with col_p2:
        st.markdown("#### 🛠️ Skills & Discovered Technical Projects")
        skills_str = ", ".join(p.get("core_skills", []))
        new_skills = st.text_area("Core Skills (comma separated)", value=skills_str, height=110)

        tech_str = ", ".join(p.get("technical_stack", []))
        new_tech = st.text_area("Technical Stack & Tools (comma separated)", value=tech_str, height=110)

        st.markdown("#### 💡 Inferred Engineering Projects from AI Chats")
        chat_projects = p.get("inferred_chat_projects", [])
        if chat_projects:
            for proj in chat_projects[:3]:
                st.info(f"**{proj.get('topic')}** ({proj.get('source')}): {proj.get('summary')}")
        else:
            st.caption("No chat exports uploaded yet. Upload ChatGPT/Claude/Gemini exports above to extract deep project details.")

    if st.button("💾 Save Profile Changes"):
        p["identity"]["full_name"] = c_name
        p["identity"]["professional_title"] = c_title
        p["identity"]["email"] = c_email
        p["identity"]["phone"] = c_phone
        p["identity"]["current_location"] = c_loc
        p["identity"]["relocation_status"] = c_reloc
        p["summary"] = summary
        p["core_skills"] = [s.strip() for s in new_skills.split(",") if s.strip()]
        p["technical_stack"] = [s.strip() for s in new_tech.split(",") if s.strip()]
        st.session_state.persona_builder.update_profile(p)
        st.session_state.active_profile = p
        st.success("Profile saved successfully!")

# ==========================================
# TAB 2: JOB HUNTER & MATCHER
# ==========================================
with tab_hunter:
    st.header("🔎 Discover & Evaluate Engineering Jobs")
    st.write("Targeted specifically for **Gulf Countries** (UAE, Saudi Arabia, Qatar, Oman, Kuwait, Bahrain) and **Easily Migratable Countries** (Singapore, Malaysia, Maldives, UK, Germany, Australia, NZ). Jobs in Israel are strictly blocked.")

    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2, 1, 1, 1, 1])
    with col_f1:
        search_kw = st.text_input("Filter Keyword", value="RAG", placeholder="e.g. RAG, Embedded, Python, AI Engineer, Systems")
    with col_f2:
        region_filter = st.selectbox("Region Filter", ["ALL", "GULF", "MIGRATABLE"])
    with col_f3:
        max_age_option = st.selectbox("Max Posting Age", ["Last 14 Days (2 Weeks)", "Last 7 Days (1 Week)"])
        max_days = 7 if "7" in max_age_option else 14
    with col_f4:
        sort_mode = st.selectbox("Sort Results By", ["🕒 Latest Postings First", "🎯 Highest ATS Match"])
    with col_f5:
        st.write("")
        st.write("")
        do_search = st.button("🔍 Hunt Live Jobs", type="primary", use_container_width=True)

    live_scrape_toggle = st.checkbox("🌐 Broad Live Multi-Portal Search (LinkedIn, Glassdoor, Indeed, Gulf Boards)", value=True, help="Expands search queries, scrapes multi-city hubs, fetches full markdown job descriptions, and limits results strictly to the last 1-2 weeks.")

    if "job_search_results" not in st.session_state or do_search:
        with st.spinner(f"Broadly hunting active engineering opportunities for '{search_kw}' (posted within {max_days} days)..."):
            try:
                st.session_state.job_search_results = hunter.search_jobs(
                    keyword=search_kw,
                    region_filter=region_filter,
                    include_live=live_scrape_toggle,
                    max_days_old=max_days
                )
            except TypeError:
                st.session_state.job_search_results = hunter.search_jobs(
                    search_kw,
                    region_filter
                )

    raw_jobs = st.session_state.job_search_results
    analyzer = JobDescriptionAnalyzer(st.session_state.active_profile)

    # Filter out non-engineering / geo-ineligible jobs
    scored_jobs = []
    for j in raw_jobs:
        analysis = analyzer.analyze(j["job_title"], j["company"], j["location"], j.get("description", ""))
        if analysis.get("is_engineering", True) and analysis.get("geo_eligible", True) and analysis.get("match_score", 0) >= 40:
            scored_jobs.append((j, analysis))

    # Apply user-selected sort
    if "Latest" in sort_mode:
        def _sort_date(x):
            d = x[0].get("date_posted", "")
            return (str(d) if d else "1970-01-01", x[1].get("match_score", 0))
        scored_jobs.sort(key=_sort_date, reverse=True)
    else:
        def _sort_score(x):
            d = x[0].get("date_posted", "")
            return (x[1].get("match_score", 0), str(d) if d else "1970-01-01")
        scored_jobs.sort(key=_sort_score, reverse=True)

    st.markdown(f"Found **{len(scored_jobs)}** active engineering opportunities for **'{search_kw or 'Engineering'}'** ({sort_mode}, strictly $\\le$ {max_days} days old):")

    for j, analysis in scored_jobs:
        portal_badge = "🌐 " + j.get("portal", "Portal") if j.get("is_live") else "🏛️ " + j.get("portal", "Directory")
        posted_str = j.get("posted_label", "Recent")
        with st.expander(f"💼 {j['job_title']} — {j['company']} ({j['location']}) | 🕒 {posted_str} | Match: {analysis['match_score']}%"):
            c_left, c_right = st.columns([2, 1])
            with c_left:
                st.markdown(f"**Location:** {j['location']}")
                st.markdown(f"**Date Posted:** `🕒 {posted_str}` ({j.get('date_posted', 'Recent')})")
                st.markdown(f"**Portal / Source:** `{portal_badge}`")
                if j.get("apply_url"):
                    st.markdown(f"**Direct Link:** [Open Posting]({j['apply_url']})")
                st.markdown(f"**HR Contact:** `{j.get('hr_email', 'careers@company.com')}`")
                st.markdown(f"**Full Job Description:**\n\n{j.get('description', '')}")
            with c_right:
                st.markdown(f"**ATS Match Score:** `{analysis['match_score']}%`")
                st.markdown(f"**Recommendation:** **{analysis['recommendation']}**")
                if analysis.get("matched_skills"):
                    st.markdown(f"**Matched Skills:** {', '.join(analysis['matched_skills'][:5])}")
                if analysis.get("recommended_keywords"):
                    st.markdown(f"**Keywords to Highlight:** {', '.join(analysis['recommended_keywords'])}")

                if st.button("🎯 Select for Tailored Application", key=f"select_{j['id']}"):
                    st.session_state.selected_job = j
                    st.success(f"Selected: {j['job_title']} at {j['company']}. Proceed to Tab 3 to generate CV & Cover Letter!")

    st.divider()
    st.subheader("🔗 Or Import Any Job from URL or Paste Description")
    col_c1, col_c2 = st.columns([1, 1])

    with col_c1:
        job_url = st.text_input("Fetch Job from Web URL (LinkedIn, Bayt, GulfTalent, etc.)")
        if st.button("🌐 Scrape Job Link"):
            if job_url:
                with st.spinner("Fetching job content and detecting HR email..."):
                    fetched = hunter.fetch_job_from_url(job_url)
                    st.session_state.selected_job = fetched
                    st.success(f"Loaded: {fetched['job_title']} from URL!")

    with col_c2:
        custom_title = st.text_input("Custom Role Title", "Senior Systems Engineer")
        custom_company = st.text_input("Company Name", "Engineering Enterprise")
        custom_loc = st.text_input("Location", "Dubai, UAE")
        custom_jd = st.text_area("Paste Job Description", height=100)
        custom_hr = st.text_input("HR / Recruiter Email", "recruitment@enterprise.com")

        if st.button("📌 Use Custom Job"):
            # Check Geo rules first
            is_el, reason, meta = GeoLocationEngine.evaluate_location(custom_loc, custom_jd)
            if not is_el:
                st.error(f"❌ Geographic Rule Rejection: {reason}")
            else:
                st.session_state.selected_job = {
                    "id": "custom",
                    "job_title": custom_title,
                    "company": custom_company,
                    "location": custom_loc,
                    "portal": "Direct / Custom",
                    "hr_email": custom_hr,
                    "description": custom_jd
                }
                st.success(f"Job set: {custom_title} at {custom_company} ({meta.get('category')})")

# ==========================================
# TAB 3: TAILOR CV & COVER LETTER
# ==========================================
with tab_tailor:
    st.header("📝 Tailor ATS-Optimized CV & Impressive Cover Letter")

    selected = st.session_state.selected_job
    if not selected:
        st.warning("⚠️ No target job selected yet! Please select an opportunity or paste a job in Tab 2.")
    else:
        st.info(f"Targeting: **{selected.get('job_title')}** at **{selected.get('company')}** ({selected.get('location')})")

        if st.button("⚡ Generate Tailored Resume & Cover Letter Now", type="primary", use_container_width=True):
            with st.spinner("Aligning Master Profile with Job Description, optimizing ATS keywords, and compiling PDFs..."):
                tailorer = ResumeTailorer(st.session_state.active_profile)
                cl_gen = CoverLetterGenerator(st.session_state.active_profile)
                pdf_builder = PDFResumeBuilder()

                # Generate content
                tailored = tailorer.generate_tailored_resume(
                    job_title=selected.get("job_title", "Engineer"),
                    company=selected.get("company", "Company"),
                    location=selected.get("location", "Gulf"),
                    jd_text=selected.get("description", "")
                )
                cl_text = cl_gen.generate(
                    job_title=selected.get("job_title", "Engineer"),
                    company=selected.get("company", "Company"),
                    location=selected.get("location", "Gulf"),
                    jd_text=selected.get("description", "")
                )

                # Generate PDFs
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_comp = "".join(c for c in selected.get("company", "Company") if c.isalnum())
                cv_pdf_file = GENERATED_DIR / f"CV_{safe_comp}_{ts}.pdf"
                cl_pdf_file = GENERATED_DIR / f"CoverLetter_{safe_comp}_{ts}.pdf"

                pdf_builder.build_resume_pdf(tailored, cv_pdf_file)
                candidate_name = st.session_state.active_profile.get("identity", {}).get("full_name", "Candidate")
                pdf_builder.build_cover_letter_pdf(cl_text, candidate_name, cl_pdf_file)

                st.session_state.tailored_resume = tailored
                st.session_state.cover_letter_text = cl_text
                st.session_state.cv_pdf_path = cv_pdf_file
                st.session_state.cl_pdf_path = cl_pdf_file

                st.success("🎉 Tailored CV and Cover Letter generated and compiled to PDF!")

        # Previews
        if st.session_state.tailored_resume and st.session_state.cover_letter_text:
            col_v1, col_v2 = st.columns(2)

            with col_v1:
                st.subheader("📄 Tailored CV Preview")
                t_res = st.session_state.tailored_resume
                st.markdown(f"**Target Role:** {t_res.get('tailored_title')}")
                st.markdown(f"**Executive Summary:**\n{t_res.get('summary')}")
                st.markdown(f"**ATS Highlighted Skills:**\n{', '.join(t_res.get('skills', []))}")

                if st.session_state.cv_pdf_path and st.session_state.cv_pdf_path.exists():
                    with open(st.session_state.cv_pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Tailored CV (PDF)",
                            data=f.read(),
                            file_name=st.session_state.cv_pdf_path.name,
                            mime="application/pdf",
                            use_container_width=True
                        )

            with col_v2:
                st.subheader("✉️ Impressive Cover Letter Preview")
                cl_edit = st.text_area("Cover Letter Content (Editable)", value=st.session_state.cover_letter_text, height=350)
                st.session_state.cover_letter_text = cl_edit

                if st.session_state.cl_pdf_path and st.session_state.cl_pdf_path.exists():
                    with open(st.session_state.cl_pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Cover Letter (PDF)",
                            data=f.read(),
                            file_name=st.session_state.cl_pdf_path.name,
                            mime="application/pdf",
                            use_container_width=True
                        )

# ==========================================
# TAB 4: HR EMAIL & DISPATCH
# ==========================================
with tab_outreach:
    st.header("🚀 HR Outreach & Email Dispatch")

    selected = st.session_state.selected_job
    if not selected:
        st.warning("⚠️ No job selected. Please select a job in Tab 2 and tailor your documents in Tab 3.")
    else:
        st.markdown(f"### Preparing Application for **{selected.get('job_title')}** at **{selected.get('company')}**")

        col_e1, col_e2 = st.columns([1, 1])

        with col_e1:
            hr_recipient = st.text_input("HR / Recruiter Email", value=selected.get("hr_email", "careers@company.com"))
            candidate_name = st.session_state.active_profile.get("identity", {}).get("full_name", "Candidate")
            default_subj = f"Application for {selected.get('job_title')} - {candidate_name} (Engineering Graduate / Specialist)"
            email_subj = st.text_input("Email Subject Line", value=default_subj)

            default_body = f"""Dear Hiring Team,

Please accept my application for the {selected.get('job_title')} position at {selected.get('company')}. 

I am an experienced engineering professional currently based in Sri Lanka, offering immediate international relocation readiness to {selected.get('location')} with full visa flexibility. 

I have attached my tailored CV and an executive cover letter outlining my technical engineering accomplishments and how my background matches your team's objectives.

I look forward to discussing this opportunity.

Sincerely,

{candidate_name}
{st.session_state.active_profile.get('identity', {}).get('phone', '')} | {st.session_state.active_profile.get('identity', {}).get('email', '')}
"""
            email_body = st.text_area("Email Body Text", value=default_body, height=220)

        with col_e2:
            st.markdown("#### 📎 Attachments Ready for Dispatch")
            if st.session_state.cv_pdf_path and st.session_state.cv_pdf_path.exists():
                st.success(f"✅ Attached CV: `{st.session_state.cv_pdf_path.name}`")
            else:
                st.warning("⚠️ CV PDF not generated yet. Visit Tab 3 to generate.")

            if st.session_state.cl_pdf_path and st.session_state.cl_pdf_path.exists():
                st.success(f"✅ Attached Cover Letter: `{st.session_state.cl_pdf_path.name}`")
            else:
                st.warning("⚠️ Cover Letter PDF not generated yet. Visit Tab 3 to generate.")

            st.divider()
            st.markdown(f"**Sending Mode:** {'🛡️ Safe Review Mode (Drafts .EML)' if safe_review_mode else '⚡ Direct Live SMTP'}")

            send_clicked = st.button("📤 Dispatch Application Now", type="primary", use_container_width=True)

            if send_clicked:
                if not hr_recipient or "@" not in hr_recipient:
                    st.error("Please enter a valid HR recipient email address.")
                else:
                    with st.spinner("Dispatching application..."):
                        result = dispatcher.send_or_draft_application(
                            job_title=selected.get("job_title", ""),
                            company=selected.get("company", ""),
                            location=selected.get("location", ""),
                            recipient_email=hr_recipient,
                            subject=email_subj,
                            body_text=email_body,
                            cv_pdf_path=st.session_state.cv_pdf_path,
                            cover_letter_pdf_path=st.session_state.cl_pdf_path,
                            force_live_send=not safe_review_mode
                        )

                        if result["success"]:
                            if result["mode"] == "LIVE_SENT":
                                st.balloons()
                                st.success(f"🚀 Email successfully sent to {hr_recipient}!")
                            else:
                                st.success(f"📁 Application prepared in Safe Draft mode! File: {result.get('draft_file')}")
                        else:
                            st.error(f"Failed to process application: {result.get('message')}")

# ==========================================
# TAB 5: APPLICATION TRACKER
# ==========================================
with tab_tracker:
    st.header("📋 Application Tracker & Dashboard")
    st.write("Track all submitted applications, drafted outreach, interview invites, and follow-up deadlines.")

    all_apps = tracker.list_applications()

    if not all_apps:
        st.info("No applications logged yet. When you generate and dispatch applications, they will appear here.")
    else:
        df = pd.DataFrame(all_apps)
        display_cols = ["id", "job_title", "company", "location", "hr_email", "status", "applied_date", "notes"]
        existing_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[existing_cols], use_container_width=True)

        st.subheader("✏️ Update Application Status")
        col_t1, col_t2, col_t3 = st.columns([1, 1, 1])
        with col_t1:
            app_id = st.selectbox("Application ID", options=[a["id"] for a in all_apps])
        with col_t2:
            new_st = st.selectbox("New Status", ["Drafted", "Sent", "Interview", "Follow-up Due", "Rejected", "Offer"])
        with col_t3:
            st.write("")
            st.write("")
            if st.button("Update Status"):
                tracker.update_status(app_id, new_st)
                st.success(f"Updated Application #{app_id} to {new_st}")
                st.rerun()

# ==========================================
# TAB 6: SETTINGS
# ==========================================
with tab_settings:
    st.header("⚙️ Agent Configuration & API Keys")

    st.subheader("🤖 LLM Provider")
    st.write("The agent works out of the box with intelligent offline heuristic templates. You can connect Google Gemini, OpenAI, or Anthropic for dynamic prose.")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        gemini_key_input = st.text_input("Google Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
        openai_key_input = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")

    with col_s2:
        anthropic_key_input = st.text_input("Anthropic Claude API Key", value=os.getenv("ANTHROPIC_API_KEY", ""), type="password")

    if st.button("Save API Keys"):
        from config import update_env_file
        updates = {}
        if gemini_key_input:
            os.environ["GEMINI_API_KEY"] = gemini_key_input
            updates["GEMINI_API_KEY"] = gemini_key_input
        if openai_key_input:
            os.environ["OPENAI_API_KEY"] = openai_key_input
            updates["OPENAI_API_KEY"] = openai_key_input
        if anthropic_key_input:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key_input
            updates["ANTHROPIC_API_KEY"] = anthropic_key_input
        update_env_file(updates)
        st.success("API Keys saved permanently to .env file!")

    st.divider()
    st.subheader("📬 SMTP Outbound Email Credentials")
    st.write("For live automated email dispatch directly to HR mailboxes.")

    col_smtp1, col_smtp2 = st.columns(2)
    with col_smtp1:
        s_user = st.text_input("SMTP Email Address (e.g. Gmail / Outlook)", value=SMTP_USER)
        s_pass = st.text_input("SMTP App Password", value=SMTP_PASSWORD, type="password", help="For Gmail, use a Google 16-character App Password.")
    with col_smtp2:
        s_host = st.text_input("SMTP Host", value=SMTP_HOST)
        s_port = st.number_input("SMTP Port", value=SMTP_PORT)

    if st.button("Save SMTP Credentials"):
        from config import update_env_file
        os.environ["SMTP_USER"] = s_user
        os.environ["SMTP_PASSWORD"] = s_pass
        os.environ["SMTP_HOST"] = s_host
        os.environ["SMTP_PORT"] = str(s_port)
        update_env_file({
            "SMTP_USER": s_user,
            "SMTP_PASSWORD": s_pass,
            "SMTP_HOST": s_host,
            "SMTP_PORT": str(s_port)
        })
        st.success("SMTP Credentials saved permanently to .env file!")

    st.divider()
    st.subheader("🌍 Regional Policies & Exclusions")
    st.markdown("**Target Gulf Hubs:** UAE (Dubai, Abu Dhabi), Saudi Arabia (Riyadh, NEOM), Qatar (Doha), Oman, Kuwait, Bahrain")
    st.markdown("**Target Migratable Pathways:** Singapore, Malaysia, Maldives, United Kingdom, Germany, Australia, New Zealand, Canada")
    st.error("**HARD RULE ENFORCED:** Israel is strictly blacklisted and any job in or from Israel will be automatically rejected.")
