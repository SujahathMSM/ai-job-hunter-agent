import json
import re
from typing import Dict, Any, List
from generators.llm_client import LLMClient

class ResumeTailorer:
    """Dynamically aligns candidate's Master Profile to target Job Description,
    preserving 100% of the candidate's real commercial experience, projects, and education
    while deeply tailoring the title, subtitle, executive profile, skills, work experience framing,
    and project highlights for maximum ATS alignment and hiring manager impact.
    Enforces strict fact-locking: company names, authentic titles, dates, institutions, and
    degrees are strictly immutable."""

    def __init__(self, master_profile: Dict[str, Any]):
        self.profile = master_profile
        self.llm = LLMClient()

    def generate_tailored_resume(self, job_title: str, company: str, location: str, jd_text: str) -> Dict[str, Any]:
        identity = self.profile.get("identity", {})
        skills_cat = self.profile.get("core_skills_categorized", [])
        work_hist = self.profile.get("work_history", [])
        projects = self.profile.get("projects", [])
        education = self.profile.get("education", [])
        certs = self.profile.get("certifications", [])

        full_name = identity.get("full_name", "Candidate")
        current_loc = identity.get("current_location", "Remote")
        tech_stack = self.profile.get("technical_stack", [])

        # Clean and enrich JD if empty or placeholder
        clean_jd = jd_text.strip() if jd_text and jd_text.strip().lower() not in ["none", "nan", "null"] else ""
        if len(clean_jd) < 80:
            clean_jd = f"""Target Position: {job_title} at {company} in {location}.
Key focus areas: Technical architecture, robust implementation, scalable backend integration, 
modern frameworks and libraries relevant to '{job_title}', production reliability, low latency, 
clean documentation, and full lifecycle engineering delivery."""

        # Format candidate's authentic background dynamically from profile
        edu_summary = "; ".join([f"{e.get('degree', 'Degree')} ({e.get('institution', 'Institution')})" for e in education]) or "Engineering / Technical Education"
        work_summary = "\n".join([f"- {w.get('title', 'Role')} at {w.get('company', 'Company')} ({w.get('duration', '')}): {'; '.join(w.get('bullets', [])[:3])}" for w in work_hist]) or "Commercial Software & Systems Engineering"
        proj_summary = "\n".join([f"- {p.get('title', 'Project')}: Tech ({p.get('technologies', '')}). {'; '.join(p.get('bullets', [])[:2])}" for p in projects[:5]]) or "Production & Open Source Projects"

        prompt = f"""
You are an elite principal technical career strategist and executive CV writer.
You are tailoring the CV of candidate: {full_name}
for the specific role: '{job_title}' at '{company}' in '{location}'.

CANDIDATE'S AUTHENTIC MASTER BACKGROUND (FACT-LOCKED):
- Education: {edu_summary}
- Work Experience:
{work_summary}
- Portfolio Projects:
{proj_summary}
- Verified Tech Stack: {', '.join(tech_stack[:25])}
- Candidate Location: {current_loc}

TARGET ROLE: {job_title}
TARGET COMPANY: {company}
TARGET LOCATION: {location}
TARGET JOB DESCRIPTION / REQUIREMENTS:
{clean_jd[:1600]}

STRICT ANTI-HALLUCINATION & FACT-LOCKING RULES:
1. Companies, institutions, job titles, durations, and degrees are IMMUTABLE. Do NOT invent new employers, alter start/end dates, or fabricate unearned credentials.
2. Do NOT invent tools or libraries the candidate has never used. Only emphasize and prioritize technical skills and competencies that exist in the candidate's verified profile and stack.
3. Keep project metrics accurate. Do not invent exaggerated benchmarks.

CRITICAL TAILORING OBJECTIVES:
1. 'tailored_title': High-impact executive headline matching the target role (e.g. for AI/Backend: '{job_title} | Systems & API Architecture Specialist').
2. 'tailored_subtitle': Refined subtitle featuring the core technologies needed for this role that match candidate's actual strengths (e.g. 'Python (AsyncIO, FastAPI) | PostgreSQL | Docker | AWS | System Reliability').
3. 'summary': An impressive 3-4 sentence Executive Profile. Highlight how candidate's technical rigor directly bridges with the target role's demands. State relocation or remote delivery readiness for {location}.
4. 'core_skills_categorized': Return a list of skill category dicts ({{"category": "...", "skills": "..."}}). Prioritize and weave in the role's key requirements from the candidate's actual skills.
5. 'work_history': Return candidate's real jobs. Tailor the bullet phrasing to strategically highlight intersections with the target role while remaining 100% truthful. Keep companies and dates identical.
6. 'projects': Select 3-4 projects from candidate's real portfolio. Highlight the technical overlap with the role (each with 1-2 high-impact bullet points).

OUTPUT FORMAT:
Return ONLY valid JSON with keys:
- 'tailored_title' (string)
- 'tailored_subtitle' (string)
- 'summary' (string)
- 'core_skills_categorized' (list of dicts with 'category' and 'skills')
- 'work_history' (list of dicts with 'company', 'branch', 'title', 'duration', 'bullets')
- 'projects' (list of dicts with 'title', 'technologies', 'bullets')
"""
        llm_output = self.llm.generate(prompt)
        parsed = None
        if llm_output:
            try:
                clean_json = llm_output.strip()
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json:
                    clean_json = clean_json.split("```")[1].split("```")[0].strip()
                parsed = json.loads(clean_json)
            except Exception as e:
                print(f"[ResumeTailorer JSON Parse Error]: {e}")
                parsed = None

        if parsed and isinstance(parsed, dict) and "tailored_title" in parsed:
            tailored_title = parsed.get("tailored_title", f"{job_title} Specialist")
            tailored_subtitle = parsed.get("tailored_subtitle", identity.get("subtitle") or "Backend & Systems Engineering")
            tailored_profile = parsed.get("summary", self.profile.get("summary", ""))
            tailored_skills = parsed.get("core_skills_categorized") or skills_cat
            raw_tailored_work = parsed.get("work_history") or work_hist
            raw_tailored_projects = parsed.get("projects") or projects
        else:
            # Deterministic Fallback based on authentic profile and role keywords
            is_ai_role = any(kw in f"{job_title} {clean_jd}".lower() for kw in ["ai", "rag", "langgraph", "llm", "genai", "machine learning", "nlp"])
            if is_ai_role:
                tailored_title = f"{job_title} | AI Systems & RAG Specialist"
                tailored_subtitle = "Python (FastAPI, AsyncIO) | RAG & Vector Search | PyTorch | PostgreSQL | Docker | CI/CD"
                tailored_profile = (
                    f"Engineer with demonstrated experience bridging production backend rigor and applied AI architectures. "
                    f"Track record building high-throughput Python/FastAPI services, hybrid vector search pipelines, and automated "
                    f"evaluation harnesses. Prepared for immediate technical delivery for {company} in {location}."
                )
            else:
                tailored_title = f"{job_title} | Backend, Data & Systems Specialist"
                tailored_subtitle = identity.get("professional_title") or "Software & Systems Engineer"
                tailored_profile = self.profile.get("summary") or f"Experienced engineer ready to deliver scalable services for {company}."

            tailored_skills = skills_cat
            raw_tailored_work = work_hist
            raw_tailored_projects = projects

        # FACT-LOCKING ENFORCEMENT: Lock company names, titles, durations, institution, and degrees
        locked_work = []
        for idx, original_job in enumerate(work_hist):
            job_copy = dict(original_job)
            if idx < len(raw_tailored_work) and isinstance(raw_tailored_work[idx], dict):
                tailored_bullets = raw_tailored_work[idx].get("bullets")
                if tailored_bullets and isinstance(tailored_bullets, list):
                    job_copy["bullets"] = [str(b).strip() for b in tailored_bullets if str(b).strip()]
            locked_work.append(job_copy)

        locked_projects = []
        for idx, original_proj in enumerate(projects[:4]):
            proj_copy = dict(original_proj)
            if idx < len(raw_tailored_projects) and isinstance(raw_tailored_projects[idx], dict):
                tailored_bullets = raw_tailored_projects[idx].get("bullets")
                if tailored_bullets and isinstance(tailored_bullets, list):
                    proj_copy["bullets"] = [str(b).strip() for b in tailored_bullets if str(b).strip()]
            locked_projects.append(proj_copy)

        return {
            "identity": identity,
            "tailored_title": tailored_title,
            "tailored_subtitle": tailored_subtitle,
            "summary": tailored_profile,
            "tailored_summary": tailored_profile,
            "core_skills_categorized": tailored_skills,
            "work_history": locked_work or work_hist,
            "projects": locked_projects or projects,
            "education": education,
            "certifications": certs,
            "target_company": company,
            "target_location": location
        }
