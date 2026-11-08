import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import PROFILE_PATH, GULF_COUNTRIES, MIGRATABLE_COUNTRIES, EXCLUDED_COUNTRIES

class PersonaBuilder:
    """Combines CV data, LinkedIn history, and LLM chat exports to synthesize a rich, accurate Master Persona."""

    def __init__(self, profile_path: Path = PROFILE_PATH, user_id: str = "default"):
        self.profile_path = profile_path
        self.user_id = user_id
        from outreach.tracker import ApplicationTracker
        self.tracker = ApplicationTracker()
        self.profile: Dict[str, Any] = self._load_or_init()

    def _load_or_init(self) -> Dict[str, Any]:
        # 1. Check SQLite multi-tenant profile table first
        db_prof = self.tracker.get_profile(self.user_id)
        if db_prof:
            return db_prof

        # 2. Check disk master_persona.json (ONLY for default seed migration)
        if self.user_id in ["default", "admin"] and self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tracker.save_profile(self.user_id, data)
                    return data
            except Exception:
                pass

        # 3. For any other user, initialize a clean generic candidate template
        default_data = self._default_template()
        self.tracker.save_profile(self.user_id, default_data)
        return default_data

    def _default_template(self) -> Dict[str, Any]:
        # For default admin account, load master persona if available
        if self.user_id in ["default", "admin"] and self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Clean generic candidate template for new multi-tenant accounts
        return {
            "identity": {
                "full_name": "Engineer Candidate",
                "professional_title": "Software & Systems Engineer",
                "email": "",
                "phone": "",
                "current_location": "",
                "nationality": "",
                "relocation_status": "Available for Full-time Roles",
                "linkedin": "",
                "github": ""
            },
            "summary": "Motivated software engineer with experience developing scalable services, reliable APIs, and modern automated workflows.",
            "core_skills": [
                "Software Architecture & API Design",
                "Backend Engineering & Microservices",
                "Database Modeling & Query Optimization",
                "Automated Testing & CI/CD Pipelines",
                "Cloud & Containerized Deployment"
            ],
            "technical_stack": [
                "Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs", "Git", "Linux"
            ],
            "work_history": [],
            "projects": [],
            "education": [],
            "certifications": [],
            "inferred_chat_projects": [],
            "communication_tone": {
                "style": "Technically rigorous, metric-driven, proactive problem-solver",
                "strengths": ["Clean code design", "Automated testing", "System reliability"]
            },
            "target_preferences": {
                "preferred_regions": ["Gulf Countries", "Remote / Global Pathways"],
                "excluded_countries": ["Israel", "Tel Aviv", "Jerusalem", "Haifa", "Beer Sheva"],
                "visa_requirements": "Open to sponsorship or direct relocation"
            },
            "core_skills_categorized": [
                {"category": "Programming & Backend", "skills": "Python, REST APIs, Docker, FastAPI"},
                {"category": "Data & Databases", "skills": "PostgreSQL, SQL, Schema Design"}
            ]
        }

    def build_from_sources(
        self,
        cv_data_list: List[Dict[str, Any]],
        chat_insights: List[Dict[str, Any]],
        linkedin_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        profile = self._default_template()

        raw_work = []
        raw_projects = []
        raw_edu = []

        # 1. Process CVs
        for cv in cv_data_list:
            c_name = cv.get("candidate_name", "").strip()
            if c_name and c_name.lower() not in ["contact", "curriculum", "resume", "engineer candidate", "software engineer"]:
                profile["identity"]["full_name"] = c_name

            contacts = cv.get("contact_info", {})
            if contacts.get("email"):
                profile["identity"]["email"] = contacts["email"]
            if contacts.get("phone"):
                profile["identity"]["phone"] = contacts["phone"]
            if contacts.get("linkedin"):
                profile["identity"]["linkedin"] = contacts["linkedin"]
            if contacts.get("github"):
                profile["identity"]["github"] = contacts["github"]

            sections = cv.get("sections", {})
            if sections.get("summary") and len(sections["summary"]) > 100:
                profile["summary"] = sections["summary"]

            # Collect raw parsed items for canonical deduplication
            raw_work.extend(cv.get("parsed_experience", []))
            raw_projects.extend(cv.get("parsed_projects", []))
            raw_edu.extend(cv.get("parsed_education", []))

            # Process skills
            if sections.get("skills"):
                raw_skills = sections["skills"].replace("\n", ", ")
                tokens = [s.strip(" •*-|:") for s in re.split(r",|•|\|", raw_skills) if s.strip()]
                for tok in tokens:
                    if 2 <= len(tok) <= 45 and not tok.startswith("http") and tok not in profile["technical_stack"]:
                        profile["technical_stack"].append(tok)

        # 2. Canonical Deduplication & Normalization
        profile["work_history"] = self._canonicalize_work_history(raw_work)
        profile["projects"] = self._canonicalize_projects(raw_projects)
        profile["education"] = self._canonicalize_education(raw_edu)

        # 2. Process LinkedIn Data
        if linkedin_data:
            li_name = linkedin_data.get("name", "").strip()
            if li_name and li_name.lower() not in ["contact", "resume", "curriculum vitae"] and len(li_name.split()) >= 2:
                # If CV name was not already definitive
                if profile["identity"]["full_name"] == "Engineer Candidate":
                    profile["identity"]["full_name"] = li_name
            if linkedin_data.get("headline"):
                profile["identity"]["professional_title"] = linkedin_data["headline"]
            if linkedin_data.get("top_skills"):
                for s in linkedin_data["top_skills"]:
                    if s not in profile["technical_stack"]:
                        profile["technical_stack"].append(s)

        # 3. Process Chat Insights
        for chat in chat_insights:
            topic = chat.get("topic", "Engineering Discussion")
            snippets = chat.get("user_snippets", [])
            summary = chat.get("summary", "")
            profile["inferred_chat_projects"].append({
                "source": chat.get("source", "AI Chat"),
                "topic": topic,
                "summary": summary,
                "context": snippets[0][:250] if snippets else ""
            })

        # 4. Synthesize Categorized Core Skills for ATS & PDF generation
        profile["core_skills_categorized"] = self._build_categorized_skills(profile.get("technical_stack", []))

        self.profile = profile
        # 5. Optionally enrich with live GitHub repositories if GitHub URL exists
        gh_url = profile.get("identity", {}).get("github", "")
        if gh_url:
            try:
                self.sync_github_repositories(gh_url)
            except Exception:
                pass

        self.save()
        return profile

    def _canonicalize_work_history(self, raw_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        seen = set()
        for item in raw_history:
            comp = item.get("company", "").strip()
            title = item.get("title", "").strip()
            if not comp and not title:
                continue
            key = f"{comp.lower()}_{title.lower()}"
            if key in seen:
                continue
            seen.add(key)
            raw_bullets = item.get("bullets", [])
            cleaned_bullets = []
            for b in raw_bullets:
                b_clean = re.sub(r"^[•\-*■\s]+", "", str(b)).strip()
                for sp in re.split(r"[■•]", b_clean):
                    sp_clean = sp.strip(" -–|:•■")
                    if len(sp_clean) > 15 and sp_clean not in cleaned_bullets:
                        cleaned_bullets.append(sp_clean)
            cleaned.append({
                "company": comp or "Company",
                "branch": item.get("branch", item.get("location", "")),
                "title": title or "Professional",
                "duration": item.get("duration", "Dates not specified"),
                "bullets": cleaned_bullets
            })
        if cleaned:
            return cleaned
        return self.profile.get("work_history", []) if hasattr(self, "profile") and isinstance(self.profile, dict) else []

    def _canonicalize_education(self, raw_edu: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned_edu = []
        seen = set()
        for item in raw_edu:
            deg = item.get("degree", "").strip()
            inst = item.get("institution", "").strip()
            if not deg and not inst:
                continue
            key = f"{deg.lower()}_{inst.lower()}"
            if key in seen:
                continue
            seen.add(key)
            cleaned_edu.append({
                "degree": deg or "Degree",
                "institution": inst or "University / Institution",
                "duration": item.get("duration", ""),
                "location": item.get("location", ""),
                "details": item.get("details", "")
            })
        if cleaned_edu:
            return cleaned_edu
        return self.profile.get("education", []) if hasattr(self, "profile") and isinstance(self.profile, dict) else []

    def _canonicalize_projects(self, raw_projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned_proj = []
        seen = set()
        for item in raw_projects:
            t = item.get("title", "").strip()
            if not t:
                continue
            key = t.lower()[:30]
            if key in seen:
                continue
            seen.add(key)
            raw_bullets = item.get("bullets", [])
            cleaned_bullets = [re.sub(r"^[•\-*■\s]+", "", str(b)).strip() for b in raw_bullets if len(str(b).strip()) > 15]
            cleaned_proj.append({
                "title": t,
                "technologies": item.get("technologies", item.get("tech_stack", "")),
                "bullets": cleaned_bullets or ([item.get("description", "")] if item.get("description") else [])
            })
        if cleaned_proj:
            return cleaned_proj
        return self.profile.get("projects", []) if hasattr(self, "profile") and isinstance(self.profile, dict) else []

    def _build_categorized_skills(self, skills: List[str]) -> List[Dict[str, str]]:
        categories = {
            "AI & Machine Learning": ["pytorch", "tensorflow", "rag", "langgraph", "langchain", "llamaindex", "ollama", "llm", "genai", "flower", "vision", "evalx", "aerointel", "machine learning", "deep learning", "nlp", "vector", "pgvector", "embeddings", "agent", "prompt", "scikit", "vlm", "llm-as-a-judge"],
            "Programming & Backend": ["python", "fastapi", "sql", "java", "c", "c++", "node", "express", "nest", "javascript", "typescript", "rest", "graphql", "websocket", "django", "flask"],
            "Data & Databases": ["postgres", "postgresql", "timescaledb", "mongodb", "redis", "mysql", "time-series", "pandas", "numpy", "matplotlib", "schema"],
            "Cloud, DevOps & Systems": ["aws", "docker", "kubernetes", "linux", "ci/cd", "gitlab", "github actions", "jenkins", "ansible", "ec2", "lambda", "s3", "rds"],
            "IoT & Integration": ["mqtt", "modbus", "raspberry", "stm32", "rtu", "rs485", "telemetry", "iot", "edge"],
            "Analysis & Delivery": ["agile", "scrum", "requirements", "root-cause", "code review", "system design", "testing", "regression"],
            "Documentation & Records Control": ["specifications", "runbooks", "procedures", "onboarding", "change control", "reporting", "documentation"]
        }

        bucketed: Dict[str, List[str]] = {cat: [] for cat in categories}
        seen = set()

        for s in skills:
            s_clean = s.strip()
            s_lower = s_clean.lower()
            if not s_clean or s_lower in seen:
                continue
            matched = False
            for cat, kws in categories.items():
                if any(kw in s_lower for kw in kws):
                    bucketed[cat].append(s_clean)
                    seen.add(s_lower)
                    matched = True
                    break
            if not matched:
                bucketed["Programming & Backend"].append(s_clean)
                seen.add(s_lower)

        # Fallbacks for admin/default profile if empty
        if self.user_id in ["default", "admin"]:
            if not bucketed["AI & Machine Learning"]:
                bucketed["AI & Machine Learning"] = [
                    "RAG (Retrieval-Augmented Generation)", "LangGraph", "Vector DBs (pgvector)",
                    "Ollama", "Vision LLMs (VLM)", "PyTorch", "LLM-as-a-Judge (evalX)", "Agentic Workflows"
                ]
            if not bucketed["Programming & Backend"]:
                bucketed["Programming & Backend"] = ["Python", "FastAPI", "REST APIs", "SQL"]
            if not bucketed["Data & Databases"]:
                bucketed["Data & Databases"] = ["PostgreSQL", "TimescaleDB", "Data Validation", "Pandas"]
            if not bucketed["Cloud, DevOps & Systems"]:
                bucketed["Cloud, DevOps & Systems"] = ["Docker", "Linux", "AWS (EC2, S3)", "GitLab CI/CD"]
            if not bucketed["IoT & Integration"]:
                bucketed["IoT & Integration"] = ["API Integration", "Real-Time Telemetry", "MQTT"]
            if not bucketed["Analysis & Delivery"]:
                bucketed["Analysis & Delivery"] = ["Requirements Analysis", "Solution Design", "Root-Cause Analysis", "Agile/Scrum"]
            if not bucketed["Documentation & Records Control"]:
                bucketed["Documentation & Records Control"] = ["Technical Specifications", "Runbooks", "Deployment Records", "Reporting"]

        result = []
        for cat, items in bucketed.items():
            if items:
                result.append({
                    "category": cat,
                    "skills": ", ".join(items[:12])
                })
        return result

    def sync_github_repositories(self, github_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries public GitHub API for candidate's real repositories to enrich portfolio."""
        url = github_url or self.profile.get("identity", {}).get("github", "")
        if not url:
            return []

        username = url.rstrip("/").split("/")[-1].strip()
        if not username or username.lower() in ["github.com", "none"]:
            return []

        import requests
        headers = {"User-Agent": "JobHunter-Agent"}
        try:
            resp = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=12", headers=headers, timeout=8)
            if resp.status_code == 200:
                repos = resp.json()
                synced = []
                for r in repos:
                    if r.get("fork"):
                        continue
                    name = r.get("name", "")
                    desc = r.get("description", "") or ""
                    lang = r.get("language", "") or "Software"
                    topics = r.get("topics", [])
                    techs = [lang] + [t for t in topics if t.lower() != lang.lower()]

                    if desc:
                        synced.append({
                            "title": f"{name} | {desc[:60]}",
                            "technologies": ", ".join(techs),
                            "bullets": [desc]
                        })
                if synced:
                    existing_titles = [p.get("title", "").lower() for p in self.profile.get("projects", [])]
                    for sp in synced:
                        p_name = sp["title"].split("|")[0].strip().lower()
                        if not any(p_name in et for et in existing_titles):
                            self.profile.setdefault("projects", []).append(sp)
                    self.save()
                    return synced
        except Exception as e:
            print(f"[GitHub Sync Warning]: {e}")
        return []

    def save(self):
        # 1. Multi-tenant persist in SQLite profiles table
        self.tracker.save_profile(self.user_id, self.profile)

        # 2. Synchronize file on disk if default user for backward compatibility
        if self.user_id == "default":
            try:
                with open(self.profile_path, "w", encoding="utf-8") as f:
                    json.dump(self.profile, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[Disk Backup Warning]: {e}")

    def get_profile(self) -> Dict[str, Any]:
        return self.profile

    def update_profile(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        self.profile.update(new_data)
        self.save()
        return self.profile
