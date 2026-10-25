import json
import re
from typing import Dict, Any, List
from generators.llm_client import LLMClient

class ResumeTailorer:
    """Dynamically aligns candidate's Master Profile to target Job Description,
    preserving 100% of the candidate's real commercial experience, projects, and education
    while deeply tailoring the title, subtitle, executive profile, skills, work experience framing,
    and project highlights for maximum ATS alignment and hiring manager impact."""

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

        # Clean and enrich JD if empty or placeholder
        clean_jd = jd_text.strip() if jd_text and jd_text.strip().lower() not in ["none", "nan", "null"] else ""
        if len(clean_jd) < 80:
            clean_jd = f"""Target Position: {job_title} at {company} in {location}.
Key focus areas: Technical architecture, robust implementation, scalable backend integration, 
modern frameworks and libraries relevant to '{job_title}', production reliability, low latency, 
clean documentation, and full lifecycle engineering delivery."""

        prompt = f"""
You are an elite principal technical career strategist and executive CV writer.
You are tailoring the CV of candidate: {identity.get('full_name', 'M.S. MOHAMED SUJAHATH')}
for the specific role: '{job_title}' at '{company}' in '{location}'.

CANDIDATE'S AUTHENTIC MASTER BACKGROUND:
- Degree: BScEngHons (Bachelor of the Science of Engineering Honours), University of Moratuwa (Sri Lanka's top engineering school)
- Current Commercial Experience:
  1. Software Engineer at Blue Brand - Advanced R&D and IP Institute (HQ: Ploiesti, Romania / Sri Lanka Branch) (Mar 2025 - Present):
     Production Python/FastAPI microservices, distributed energy platform, real-time device data, REST/WebSocket/MQTT data flows, PostgreSQL/TimescaleDB, automated vision-model document extraction service (Energy Bill Extractor with evaluation harness), audit of 419-file codebase, reduced polling failures from 80% to 0%, slashed startup times by 90% (5-6 min to 15-30s), GitLab CI/CD, Docker, Ansible, AWS EC2/S3.
  2. Software Engineer Intern / Associate Engineer at CodeScale Pvt Ltd (Jul 2024 - Feb 2025):
     WheresNow real-time platform, Node.js (Express/Nest.js), Java, Firebase, REST/GraphQL, PostgreSQL, MongoDB, AWS (EC2, Lambda, S3), GitHub Actions, Jenkins.
  3. Trainee Engineer at Lanka Hydraulic Institute (Jan 2023 - Jun 2023):
     Python (Pandas, NumPy, Matplotlib), PostgreSQL, coastal spatial simulations.
- Candidate Verified GitHub Projects (github.com/SujahathMSM):
  1. AeroIntel (github.com/SujahathMSM/aerointel): Local-first hybrid RAG (Retrieval-Augmented Generation) pipeline over aviation maintenance manuals that refuses instead of guessing: hybrid search (pgvector + BM25), structural refusal gate, printed-page citations, and a trust layer validating every figure against source documents. Tech: Python, FastAPI, pgvector, PostgreSQL, Redis, BM25, Ollama, Docker. Evaluated on a published golden set.
  2. evalX (github.com/SujahathMSM/evalX): Comprehensive evaluation harness for LLM apps: golden test datasets, deterministic code assertions + LLM-as-a-judge scoring, regression tracking, and automated CI gates ("pytest for AI behavior"). Tech: Python, Pytest, Pydantic, LLM-as-a-Judge, CI/CD.
  3. EDGEOPS AI (github.com/SujahathMSM/EDGEOPS_AI): AI-assisted infrastructure incident triage platform using typed tools, strict permission boundaries, target access restrictions, and correlated audit logging. Tech: Python 3.11+, Pydantic, Agentic Workflows, Typed Tools.
  4. Energy Bill Extractor: Multimodal document extraction service converting complex bill PDFs and photos into validated structured JSON schemas with an evaluation harness. Tech: Python, FastAPI, Vision LLMs, Pydantic.
  5. Federated Learning for IoT Botnet Detection: Privacy-preserving distributed ML pipeline across 9 client nodes using PyTorch and Flower (99.71% federated accuracy). Tech: Python, PyTorch, Flower, NumPy.
- Location: Sri Lanka. 100% prepared for immediate international relocation to {location}.

TARGET ROLE: {job_title}
TARGET COMPANY: {company}
TARGET LOCATION: {location}
TARGET JOB DESCRIPTION / REQUIREMENTS:
{clean_jd[:1600]}

CRITICAL TAILORING OBJECTIVES:
1. 'tailored_title': A high-impact executive headline matching the target role (e.g. for AI/RAG/LangGraph: 'AI Engineer | GenAI, RAG, LangGraph & Scalable Systems Specialist').
2. 'tailored_subtitle': Refined subtitle featuring the exact core technologies needed for this role that match candidate's strengths (e.g. 'Python (AsyncIO, FastAPI) | LangGraph | RAG & Vector DBs | PyTorch | AWS | Docker | CI/CD | System Reliability').
3. 'summary': An impressive 4-5 sentence Executive Profile. Crucially highlight how his deep backend and production systems engineering rigor (FastAPI, distributed pipelines, zero-tolerance reliability, 80% to 0% polling failures) directly bridges with the target role's demands (building reliable, deterministic, production-grade agentic workflows, RAG pipelines, and scalable APIs rather than fragile toy prototypes). State readiness for immediate international relocation to {location}.
4. 'core_skills_categorized': Return a list of 7 skill category dicts ({{"category": "...", "skills": "..."}}). Intelligently prioritize and weave in the target role's key requirements:
   - For AI / GenAI / RAG roles: In 'AI & Machine Learning', explicitly showcase: 'LangGraph, RAG (Retrieval-Augmented Generation), Vector Databases (pgvector, ChromaDB), LangChain, LlamaIndex, PyTorch, TensorFlow, Prompt Engineering, Agentic Workflows, Vision-Model Document Extraction, LLM Evaluation Harnesses'.
   - In 'Programming & Backend': 'Python (AsyncIO, FastAPI, Pydantic), REST & Streaming APIs, WebSockets, SQL, Node.js (Express, Nest.js), GraphQL, Docker, C'.
   - In 'Data & Databases': 'PostgreSQL, pgvector, TimescaleDB, MongoDB, time-series data, schema design, query optimisation, data validation and reconciliation, Pandas, NumPy'.
   - Retain the other 4 categories with high density.
5. 'work_history': Return candidate's 3 real jobs. Tailor the bullet points of Blue Brand and CodeScale to strategically highlight the intersections with the target role (e.g. low-latency APIs, automated document intelligence / vision pipelines, data streaming, database optimization, eliminating failure rates, Docker/AWS deployment) while remaining 100% truthful to his background. Maintain 8-9 bullets for Blue Brand, 3 for CodeScale, 1 for Lanka Hydraulic.
6. 'projects': Intelligently select and return 3-4 projects from candidate's verified portfolio. For AI / GenAI / RAG / LangGraph roles, ALWAYS lead with 'AeroIntel' (deterministic RAG with pgvector & BM25), 'evalX' (LLM evaluation harness with CI gates), and 'EDGEOPS AI' or 'Energy Bill Extractor'. Highlight the exact technical overlap with the role (each with 1-2 concise, high-impact bullet points).

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
            tailored_subtitle = parsed.get("tailored_subtitle", identity.get("subtitle"))
            tailored_profile = parsed.get("summary", self.profile.get("summary"))
            tailored_skills = parsed.get("core_skills_categorized") or skills_cat
            tailored_work = parsed.get("work_history") or work_hist
            tailored_projects = parsed.get("projects") or projects
        else:
            # Deterministic Smart Fallback based on job keywords
            is_ai_role = any(kw in f"{job_title} {clean_jd}".lower() for kw in ["ai", "rag", "langgraph", "llm", "genai", "machine learning", "nlp"])
            if is_ai_role:
                tailored_title = f"{job_title} | GenAI, RAG & Scalable Systems Specialist"
                tailored_subtitle = "Python (AsyncIO, FastAPI) | LangGraph | RAG & Vector DBs | PyTorch | AWS | Docker | CI/CD | System Reliability"
                tailored_profile = (
                    f"Dynamic Engineer with proven expertise bridging production backend rigor and cutting-edge artificial intelligence to build "
                    f"enterprise-grade GenAI systems, RAG architectures, and agentic workflows. Track record of high-impact delivery in Python and FastAPI, "
                    f"including slashing controller startup times by 90% and eliminating polling failures from 80% to 0%. Experienced in building multimodal "
                    f"document intelligence pipelines and automated evaluation harnesses. Based in Sri Lanka and fully prepared for immediate international "
                    f"relocation to {location} to accelerate engineering delivery at {company}."
                )
                # Enhance AI skills
                tailored_skills = []
                for cat in skills_cat:
                    if cat.get("category") == "AI & Machine Learning":
                        tailored_skills.append({
                            "category": "AI & Machine Learning",
                            "skills": "LangGraph, RAG (Retrieval-Augmented Generation), Vector Databases (pgvector, ChromaDB), LangChain, LlamaIndex, PyTorch, TensorFlow, Prompt Engineering, Agentic Workflows, Vision-Model Document Extraction, LLM Evaluation Harnesses"
                        })
                    elif cat.get("category") == "Programming & Backend":
                        tailored_skills.append({
                            "category": "Programming & Backend",
                            "skills": "Python (AsyncIO, FastAPI, Pydantic), REST & Streaming APIs, WebSockets, SQL, Java, Node.js (Express, Nest.js), GraphQL, Docker, C"
                        })
                    else:
                        tailored_skills.append(cat)

                # Enhance projects with verified GitHub AI/RAG repositories
                tailored_projects = [
                    {
                        "title": "AeroIntel | Deterministic RAG Pipeline for Aviation Maintenance",
                        "technologies": "Python, FastAPI, pgvector, PostgreSQL, Redis, BM25, Ollama, Docker",
                        "bullets": [
                            "Engineered a local-first hybrid RAG system (dense vector + BM25 keyword search) with a structural refusal gate, printed-page citations, and a trust layer validating extracted figures against source maintenance manuals, benchmarked on a published golden test set."
                        ]
                    },
                    {
                        "title": "evalX | Evaluation Harness & Regression Testing for LLM Apps",
                        "technologies": "Python, Pytest, Pydantic, LLM-as-a-Judge, CI/CD Gates",
                        "bullets": [
                            "Built an automated testing harness for LLM behavior featuring golden test suites, hybrid scoring (code assertions + LLM-judge), regression tracking, and automated CI gating to eliminate hallucinations in production releases."
                        ]
                    },
                    {
                        "title": "Energy Bill Extractor & Vision RAG Pipeline",
                        "technologies": "Python, FastAPI, Multimodal Vision LLMs, Pydantic, Benchmark Harness",
                        "bullets": [
                            "Engineered an end-to-end multimodal pipeline turning messy PDFs and photos into validated structured JSON schemas, incorporating an automated evaluation benchmark harness to optimize extraction accuracy and handle edge cases."
                        ]
                    },
                    {
                        "title": "Federated Learning for IoT Threat & Botnet Detection",
                        "technologies": "Python, PyTorch, Flower, Distributed Systems, NumPy",
                        "bullets": [
                            "Built a privacy-preserving federated ML pipeline classifying Mirai and BASHLITE botnet traffic across 9 distributed client nodes; achieved 99.71% federated accuracy while maintaining complete data localization."
                        ]
                    }
                ]
                tailored_work = work_hist
            else:
                tailored_title = f"{job_title} | Backend, Data & Systems Specialist"
                tailored_subtitle = identity.get("subtitle")
                tailored_profile = self.profile.get("summary")
                tailored_skills = skills_cat
                tailored_work = work_hist
                tailored_projects = projects

        return {
            "identity": identity,
            "tailored_title": tailored_title,
            "tailored_subtitle": tailored_subtitle,
            "summary": tailored_profile,
            "tailored_summary": tailored_profile,
            "core_skills_categorized": tailored_skills,
            "work_history": tailored_work,
            "projects": tailored_projects,
            "education": education,
            "certifications": certs,
            "target_company": company,
            "target_location": location
        }
