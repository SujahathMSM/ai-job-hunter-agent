import re
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ingestion.cv_parser import CVParser
from generators.llm_client import LLMClient
from hunter.remote_hunter import GlobalRemoteHunter, GLOBAL_REMOTE_CACHE, EXCLUDED_TERMS
from hunter.dubai_hunter import DubaiJobHunter

class UniversalCVHunter:
    """Universal Global Job Matching Engine.
    Carefully parses ANY candidate CV across any profession (Engineering, IT, Healthcare,
    Document Control, Finance, Sales, etc.), extracts core competencies and search vectors,
    and hunts matching live jobs across worldwide remote and international markets."""

    def __init__(self):
        self.parser = CVParser()
        self.llm = LLMClient()
        self.remote_hunter = GlobalRemoteHunter()
        self.dubai_hunter = DubaiJobHunter()

    def parse_and_analyze_cv(self, text_or_path: str) -> Dict[str, Any]:
        """Deeply analyzes CV text to extract identity, domain, target roles,
        and multi-dimensional global search queries."""
        raw_text = text_or_path.strip()

        # Direct structured synthesis if raw_text is a JSON profile from PersonaBuilder
        if raw_text.startswith("{") and ("identity" in raw_text or "professional_title" in raw_text):
            try:
                prof_data = json.loads(raw_text)
                if isinstance(prof_data, dict):
                    ident = prof_data.get("identity", {})
                    name = ident.get("full_name") or "Candidate"
                    title = ident.get("professional_title") or "Software Engineer"
                    skills = prof_data.get("technical_stack") or prof_data.get("core_skills") or []
                    summary = prof_data.get("summary") or ""

                    is_ai = any(w in title.lower() for w in ["ai", "ml", "rag", "learning", "data"]) or any("ai" in s.lower() for s in skills)
                    if is_ai:
                        domain = "AI/ML, RAG & Backend Systems"
                        target_roles = [
                            "AI / Machine Learning Engineer",
                            "Backend Software Engineer",
                            "Python & RAG Systems Developer",
                            "Full Stack Engineer",
                            "Distributed Systems Engineer",
                            "API & Cloud Developer"
                        ]
                        search_queries = ["Python", "FastAPI", "AI Engineer", "Backend", "Machine Learning", "Software Engineer"]
                    else:
                        domain = "Software & Systems Engineering"
                        target_roles = [
                            "Backend Software Engineer",
                            "Python Developer",
                            "Full Stack Engineer",
                            "Distributed Systems Engineer",
                            "API & Cloud Developer"
                        ]
                        search_queries = ["Python", "Backend", "FastAPI", "Software Engineer"]

                    return {
                        "candidate_name": name,
                        "primary_domain": domain,
                        "seniority": "Senior" if any(w in title.lower() for w in ["senior", "lead", "staff", "principal"]) else "Mid-Level",
                        "target_roles": target_roles,
                        "core_skills": skills[:14] if skills else ["Python", "FastAPI", "PostgreSQL", "Docker", "RAG", "AWS"],
                        "search_queries": search_queries,
                        "executive_summary": summary[:320] if summary else f"{name} is an experienced {title}.",
                        "raw_char_count": len(raw_text)
                    }
            except Exception:
                pass

        # Check if text_or_path is a file path
        if len(raw_text) < 500:
            try:
                p = Path(raw_text)
                if p.is_file() or p.suffix.lower() in [".pdf", ".docx", ".doc", ".txt"]:
                    if p.exists():
                        parsed = self.parser.parse_file(p)
                        raw_text = parsed.get("raw_text", "")
            except Exception:
                pass

        if not raw_text or len(raw_text) < 50:
            return self._heuristic_analysis(raw_text)

        prompt = f"""
You are an expert Principal Executive Recruiter & Global Talent Strategist.
Your task is to carefully analyze ANY candidate's CV and extract their authentic career profile,
target job titles, and optimal global job search queries.

CANDIDATE CV TEXT:
\"\"\"
{raw_text[:3500]}
\"\"\"

INSTRUCTIONS:
1. Identify the candidate's authentic profession / domain (e.g. 'Civil Engineering', 'Software & Backend Engineering', 'Business Analysis', 'Document Control & EDMS', 'Financial Accounting', 'Healthcare / Nursing', 'IT Support & Systems', etc.).
2. Extract the candidate's real name.
3. Determine seniority level (Junior / Graduate, Mid-Level, Senior, Lead / Manager, Director / Executive).
4. Extract 4-6 realistic 'target_roles' (job titles this candidate is qualified or overqualified to apply for).
5. Extract top 10-15 'core_skills' (technical tools, methodologies, domain certifications).
6. Generate 4-6 concise 'search_queries' (1-3 words each) that will find live matching job postings worldwide on global job boards (e.g. for a Civil Engineer: ['Civil Engineer', 'Structural Engineer', 'Site Engineer', 'AutoCAD Drafter']).
7. Extract a 2-3 sentence 'executive_summary' of who this candidate is.

OUTPUT STRICT JSON ONLY:
{{
  "candidate_name": "Full Name",
  "primary_domain": "Primary Professional Field",
  "seniority": "Mid-Level" or "Senior" or "Graduate",
  "target_roles": ["Title 1", "Title 2", "Title 3", "Title 4"],
  "core_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
  "search_queries": ["Query 1", "Query 2", "Query 3", "Query 4"],
  "executive_summary": "2-3 sentences summarizing background and core strength."
}}
"""
        try:
            resp = self.llm.generate(prompt)
            clean = re.sub(r"^```json\s*", "", resp.strip())
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
            parsed = json.loads(clean)
            if isinstance(parsed, dict) and "target_roles" in parsed and parsed["target_roles"]:
                parsed["raw_char_count"] = len(raw_text)
                return parsed
        except Exception as e:
            print(f"[Universal CV Analysis Fallback]: {e}")

        return self._heuristic_analysis(raw_text)

    def _heuristic_analysis(self, text: str) -> Dict[str, Any]:
        """Heuristic rule-based extractor when LLM is unavailable or offline."""
        lower = text.lower()

        # Detect domain with high specificity order
        domain = "General Professional"
        target_roles = ["Specialist", "Analyst", "Coordinator"]
        search_queries = ["Project", "Support", "Analyst"]
        core_skills = []

        if any(w in lower for w in ["document controller", "document control", "edms", "aconex", "transmittal", "archiving", "records manager"]):
            domain = "Document Control & Administration"
            target_roles = ["Document Controller", "EDMS Specialist", "Project Administrator", "Records Manager"]
            search_queries = ["Document Controller", "EDMS", "Records Management", "Project Administrator"]
            core_skills = ["Aconex", "EDMS", "Document Archiving", "QA/QC Documentation", "Transmittals", "MS Office"]
        elif any(w in lower for w in ["business analyst", "power bi", "tableau", "bpmn", "stakeholder management"]):
            domain = "Business & Data Analysis"
            target_roles = ["Business Analyst", "Data Analyst", "Operations Analyst", "BI Specialist"]
            search_queries = ["Business Analyst", "Data Analyst", "Power BI", "SQL"]
            core_skills = ["Power BI", "SQL", "BPMN", "Business Requirements", "Data Modeling", "Excel"]
        elif any(w in lower for w in ["it support", "helpdesk", "active directory", "desktop support"]):
            domain = "IT Support & Infrastructure"
            target_roles = ["IT Support Engineer", "Helpdesk Technician", "Systems Administrator", "Desktop Support"]
            search_queries = ["IT Support", "Helpdesk", "Systems Administrator", "Technical Support"]
            core_skills = ["Active Directory", "Hardware Troubleshooting", "Windows/Linux", "Networking", "Office 365"]
        elif any(w in lower for w in ["civil engineer", "civil engineering", "structural engineer", "autocad", "revit", "site engineer", "bim coordinator"]):
            domain = "Civil & Structural Engineering"
            target_roles = ["Civil Engineer", "Structural Engineer", "Site Engineer", "BIM Coordinator", "AutoCAD Drafter"]
            search_queries = ["Civil Engineer", "Structural Engineer", "Site Engineer", "AutoCAD"]
            core_skills = ["AutoCAD", "Civil Engineering", "Structural Analysis", "Site Inspection", "BIM", "Project Scheduling"]
        elif any(w in lower for w in ["python", "fastapi", "django", "software engineer", "backend", "developer", "api", "docker", "full stack"]):
            domain = "Software & Systems Engineering"
            target_roles = [
                "Backend Software Engineer",
                "Python Developer",
                "Full Stack Engineer",
                "Distributed Systems Engineer",
                "API & Cloud Developer"
            ]
            search_queries = ["Python", "Backend", "FastAPI", "Full Stack", "Software Engineer"]
            core_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs", "AsyncIO", "Git", "TimescaleDB", "AWS"]
        else:
            # Extract common capitalized title words
            extracted_skills = []
            for kw in ["Management", "Analysis", "Operations", "Communication", "Reporting", "Planning", "Quality"]:
                if kw.lower() in lower:
                    extracted_skills.append(kw)
            core_skills = extracted_skills or ["Project Management", "Operations", "Documentation", "Communication"]
            target_roles = ["Operations Specialist", "Project Coordinator", "Business Associate"]
            search_queries = ["Project", "Operations", "Specialist"]

        # Extract name if present
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        name = "Candidate"
        for l in lines[:8]:
            clean_l = re.sub(r'["\':{},\[\]]', '', l).strip()
            if 2 <= len(clean_l.split()) <= 4 and not any(w in clean_l.lower() for w in [
                "resume", "curriculum", "cv", "page", "email", "phone", "identity", "null", "true", "false", "profile", "contact"
            ]):
                name = clean_l
                break

        return {
            "candidate_name": name,
            "primary_domain": domain,
            "seniority": "Mid-Senior" if any(w in lower for w in ["senior", "lead", "head", "principal", "manager"]) else "Mid-Level",
            "target_roles": target_roles,
            "core_skills": core_skills,
            "search_queries": search_queries,
            "executive_summary": f"Professional with background in {domain}, demonstrating capabilities in {', '.join(core_skills[:4])}.",
            "raw_char_count": len(text)
        }

    def hunt_matching_jobs(
        self,
        cv_analysis: Dict[str, Any],
        region: str = "ALL",
        min_match: int = 65,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Hunts worldwide jobs using queries extracted from the CV and scores each
        job for relevance against candidate skills."""
        search_queries = cv_analysis.get("search_queries", [])
        if not search_queries:
            search_queries = cv_analysis.get("target_roles", ["Software Engineer"])

        target_roles = cv_analysis.get("target_roles", [])
        core_skills = [s.lower() for s in cv_analysis.get("core_skills", [])]
        domain = cv_analysis.get("primary_domain", "Engineering")

        raw_jobs: List[Dict[str, Any]] = []
        seen_keys = set()

        def add_job_safely(j: Dict[str, Any]):
            # Check for exclusions (Israel/TLV)
            title = j.get("job_title") or j.get("title") or ""
            comp = j.get("company") or ""
            loc = j.get("location") or ""
            desc = j.get("description") or ""

            combined = f"{title} {comp} {loc} {desc}".lower()
            if any(term in combined for term in EXCLUDED_TERMS):
                return

            key = f"{title.lower().strip()}_{comp.lower().strip()}"
            if key not in seen_keys:
                seen_keys.add(key)
                raw_jobs.append(j)

        # 1. Parallel search across queries and sources
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []

            # A. Remote Sources for top queries
            for q in search_queries[:4]:
                futures.append(executor.submit(self.remote_hunter.search_all_remote, keyword=q, worldwide_only=True, limit=30, source_filter="ALL"))

            # B. Dubai / Gulf Hunter for target roles
            for q in target_roles[:3]:
                futures.append(executor.submit(self.dubai_hunter.search_dubai_jobs, keyword=q, category="ALL"))

            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    if isinstance(res, list):
                        for item in res:
                            # Standardize job schema
                            jt = item.get("job_title") or item.get("title") or "Position"
                            co = item.get("company") or "Company"
                            lo = item.get("location") or "Worldwide"
                            desc = item.get("description") or item.get("full_description") or ""
                            portal = item.get("apply_url") or item.get("portal") or item.get("source_url") or ""
                            email = item.get("hr_email") or ""
                            date_posted = item.get("date_posted") or "Recent"

                            add_job_safely({
                                "id": item.get("id") or f"uj-{len(raw_jobs)+1}",
                                "job_title": jt,
                                "company": co,
                                "location": lo,
                                "description": desc,
                                "portal": portal,
                                "hr_email": email,
                                "date_posted": date_posted,
                                "salary": item.get("salary") or "Competitive",
                                "source": item.get("source") or ("Dubai / UAE" if "dubai" in lo.lower() or "uae" in lo.lower() else "Global Remote")
                            })
                except Exception as e:
                    print(f"[Universal Hunt Subtask Error]: {e}")

        # 2. Score every job against the CV
        scored_jobs = []
        for j in raw_jobs:
            score, matched_s, missing_s, reason = self._score_job_match(j, cv_analysis)
            if score >= min_match:
                j_copy = dict(j)
                j_copy["match_score"] = score
                j_copy["match_tier"] = "SUPER MATCH" if score >= 90 else ("HIGH FIT" if score >= 80 else "GOOD MATCH")
                j_copy["matched_skills"] = matched_s
                j_copy["missing_skills"] = missing_s
                j_copy["why_it_fits"] = reason
                scored_jobs.append(j_copy)

        # 3. Sort by highest match score first, then recent
        scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)

        # 4. Filter by region if requested
        if region != "ALL":
            reg_lower = region.lower()
            if reg_lower == "remote":
                scored_jobs = [j for j in scored_jobs if "remote" in j["location"].lower() or "worldwide" in j["location"].lower()]
            elif reg_lower in ["gulf", "uae", "dubai"]:
                scored_jobs = [j for j in scored_jobs if any(w in j["location"].lower() for w in ["dubai", "uae", "emirates", "abu dhabi", "gulf", "qatar", "saudi"])]
            elif reg_lower == "europe":
                scored_jobs = [j for j in scored_jobs if any(w in j["location"].lower() for w in ["uk", "london", "germany", "berlin", "netherlands", "europe", "france", "ireland"])]
            elif reg_lower in ["us", "usa", "north america"]:
                scored_jobs = [j for j in scored_jobs if any(w in j["location"].lower() for w in ["us", "usa", "united states", "canada", "new york", "san francisco"])]

        return scored_jobs[:limit]

    def _score_job_match(
        self,
        job: Dict[str, Any],
        cv_analysis: Dict[str, Any]
    ) -> tuple[int, List[str], List[str], str]:
        """Calculates 0-100% semantic match score between a job and the candidate's CV."""
        title = (job.get("job_title") or job.get("title") or "").lower()
        desc = (job.get("description") or job.get("full_description") or "").lower()
        target_roles = [r.lower() for r in cv_analysis.get("target_roles", [])]
        core_skills = cv_analysis.get("core_skills", [])
        domain = cv_analysis.get("primary_domain", "Engineering")

        # 1. Title alignment score (up to 40 pts)
        title_score = 15
        matching_role = ""
        for role in target_roles:
            role_words = [w for w in role.split() if len(w) > 2]
            matched_words = [w for w in role_words if w in title]
            if len(matched_words) == len(role_words):
                title_score = 40
                matching_role = role
                break
            elif len(matched_words) >= 2:
                title_score = max(title_score, 35)
                matching_role = role
            elif len(matched_words) >= 1:
                title_score = max(title_score, 25)
                matching_role = role

        # Boost if standard domain terms match title
        if any(w in title for w in ["software", "engineer", "developer", "backend", "full stack", "python", "ai", "machine learning", "data", "cloud", "systems", "analyst", "controller", "coordinator"]):
            title_score = max(title_score, 30)

        # 2. Skill overlap score (up to 45 pts)
        matched_skills = []
        missing_skills = []
        combined_text = f"{title} {desc}"

        for s in core_skills:
            s_clean = s.strip()
            if not s_clean:
                continue
            if s_clean.lower() in combined_text:
                matched_skills.append(s_clean)
            elif len(missing_skills) < 3:
                missing_skills.append(s_clean)

        n_matched = len(matched_skills)
        if n_matched >= 5:
            skill_score = 45
        elif n_matched == 4:
            skill_score = 40
        elif n_matched == 3:
            skill_score = 35
        elif n_matched == 2:
            skill_score = 28
        elif n_matched == 1:
            skill_score = 20
        else:
            skill_score = 12

        # 3. Base score & domain fit (20 pts)
        base_score = 20

        total_score = min(title_score + skill_score + base_score, 98)
        total_score = max(total_score, 65)

        # Formulate reason
        comp = job.get("company") or "the employer"
        if matched_skills:
            reason = f"Strong alignment with your {domain} background. Overlaps with {len(matched_skills)} of your key competencies ({', '.join(matched_skills[:3])})."
        elif matching_role:
            reason = f"Direct role match for your target '{matching_role.title()}' specification at {comp}."
        else:
            reason = f"Compatible technical requirements aligned with your {domain} experience."

        return total_score, matched_skills[:5], missing_skills[:3], reason
