import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

from ingestion.cv_parser import CVParser
from ingestion.persona_builder import PersonaBuilder
from config import GENERATED_DIR, UPLOADS_DIR

class IntakeEngine:
    """Orchestrates multi-source candidate intake:
    - Multiple CVs (PDF/DOCX/TXT)
    - LLM Chat History (ChatGPT/Claude JSON/MD/TXT)
    - LinkedIn Profile (URL / pasted text / PDF)
    - GitHub Profile (Repositories, tech breakdown, stars, descriptions)
    - Personal Portfolio Website (Scraped bio, projects, tech stack)
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.cv_parser = CVParser()
        self.persona_builder = PersonaBuilder(user_id=user_id)

    def parse_multiple_cvs(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        results = []
        for p in file_paths:
            try:
                parsed = self.cv_parser.parse_file(p)
                results.append(parsed)
            except Exception as e:
                results.append({
                    "source_file": p.name,
                    "error": str(e),
                    "candidate_name": "",
                    "sections": {},
                    "parsed_experience": [],
                    "parsed_projects": [],
                    "parsed_education": []
                })
        return results

    def parse_chat_history_file(self, file_path: Path) -> List[Dict[str, Any]]:
        insights = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            # If JSON (ChatGPT export format)
            if file_path.suffix.lower() == ".json":
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data[:10]:
                            title = item.get("title", "Engineering Conversation")
                            messages = []
                            mapping = item.get("mapping", {})
                            for node_id, node in mapping.items():
                                msg = node.get("message")
                                if msg and msg.get("content", {}).get("parts"):
                                    parts = msg["content"]["parts"]
                                    text_parts = [p for p in parts if isinstance(p, str)]
                                    if text_parts:
                                        messages.append(" ".join(text_parts))
                            summary = " ".join(messages)[:400]
                            if summary:
                                insights.append({
                                    "source": f"ChatGPT: {title}",
                                    "topic": title,
                                    "summary": summary,
                                    "key_terms": self._extract_tech_terms(summary)
                                })
                except Exception:
                    pass

            if not insights:
                # Text or Markdown conversation logs
                blocks = re.split(r"\n(?=(?:###|User:|Human:|Assistant:|\*\*User\*\*))", content)
                for b in blocks[:8]:
                    b_clean = b.strip()
                    if len(b_clean) > 80:
                        lines = b_clean.split("\n")
                        topic = lines[0][:80].replace("#", "").strip()
                        insights.append({
                            "source": file_path.name,
                            "topic": topic or "Technical Discussion",
                            "summary": b_clean[:500],
                            "key_terms": self._extract_tech_terms(b_clean)
                        })
        except Exception as e:
            print(f"[Chat History Parse Error]: {e}")
        return insights

    def parse_github_profile(self, url_or_username: str) -> Dict[str, Any]:
        """Queries GitHub public API without needing authentication."""
        clean = url_or_username.strip().rstrip("/")
        username = clean.split("/")[-1].replace("@", "").strip()
        if not username:
            return {"error": "Invalid GitHub username or URL"}

        headers = {
            "User-Agent": "NexusHunt-AI-IntakeEngine",
            "Accept": "application/vnd.github.v3+json"
        }

        # 1. Fetch User Profile
        user_info = {}
        try:
            r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
            if r.status_code == 200:
                user_info = r.json()
        except Exception as e:
            print(f"[GitHub User Fetch Error]: {e}")

        # 2. Fetch Public Repositories
        repos_data = []
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15",
                headers=headers,
                timeout=10
            )
            if r.status_code == 200:
                repos = r.json()
                for repo in repos:
                    if repo.get("fork"):
                        continue
                    name = repo.get("name", "")
                    desc = repo.get("description") or "Production engineering repository."
                    lang = repo.get("language") or "Python"
                    stars = repo.get("stargazers_count", 0)
                    topics = repo.get("topics", [])
                    html_url = repo.get("html_url", "")
                    techs = [lang] + [t for t in topics if t.lower() != lang.lower()]

                    repos_data.append({
                        "name": name,
                        "title": f"{name} | {desc[:60]}",
                        "description": desc,
                        "language": lang,
                        "stars": stars,
                        "technologies": ", ".join([t for t in techs if t]),
                        "url": html_url,
                        "bullets": [
                            desc,
                            f"Primary stack: {lang} with open-source stars ({stars}) and verified commit history."
                        ]
                    })
        except Exception as e:
            print(f"[GitHub Repos Fetch Error]: {e}")

        return {
            "username": username,
            "name": user_info.get("name") or username,
            "bio": user_info.get("bio") or "",
            "location": user_info.get("location") or "",
            "blog": user_info.get("blog") or "",
            "public_repos_count": user_info.get("public_repos", len(repos_data)),
            "avatar_url": user_info.get("avatar_url") or "",
            "profile_url": f"https://github.com/{username}",
            "repositories": repos_data
        }

    def parse_linkedin_text_or_url(self, linkedin_url: str, raw_text: str = "") -> Dict[str, Any]:
        """Parses LinkedIn information from URL or pasted profile text."""
        clean_url = linkedin_url.strip()
        if clean_url and not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = f"https://{clean_url}"

        username = clean_url.rstrip("/").split("/")[-1].strip()

        result = {
            "linkedin_url": clean_url,
            "username": username,
            "headline": "",
            "summary": "",
            "skills": [],
            "experience": [],
            "status": "connected"
        }

        # Automatically update master profile's linkedin URL
        if clean_url:
            self.persona_builder.profile.setdefault("identity", {})["linkedin"] = clean_url
            self.persona_builder.save()

        text = raw_text.strip()
        if text:
            # Extract headline
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for l in lines[:6]:
                if any(kw in l.lower() for kw in ["engineer", "developer", "architect", "lead", "specialist", "intern", "iot", "systems"]):
                    result["headline"] = l
                    break

            # Extract skills keywords
            tech_matches = self._extract_tech_terms(text)
            result["skills"] = tech_matches

            # Extract about / summary
            if "About" in text:
                parts = text.split("About", 1)
                about_body = parts[1].split("Experience")[0].split("Activity")[0].strip()
                result["summary"] = about_body[:600]
            elif len(text) > 40 and not result["summary"]:
                result["summary"] = text[:400]

            # Merge into profile if substantial
            if result["headline"]:
                self.persona_builder.profile.setdefault("identity", {})["professional_title"] = result["headline"]
            if result["skills"]:
                for s in result["skills"]:
                    if s not in self.persona_builder.profile.get("technical_stack", []):
                        self.persona_builder.profile.setdefault("technical_stack", []).append(s)
            if result["summary"] and len(result["summary"]) > 80:
                self.persona_builder.profile["summary"] = result["summary"]

            self.persona_builder.save()
            result["status"] = "parsed"
        else:
            result["status"] = "url_saved"
            result["message"] = "LinkedIn profile URL saved to Master Persona! To extract detailed headline, bio, and skills, paste your profile text below or upload a LinkedIn PDF export."

        return result

    def parse_linkedin_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Parses an official LinkedIn PDF export (generated via LinkedIn 'More' -> 'Save to PDF')."""
        parsed_cv = self.cv_parser.parse_file(pdf_path)
        raw_text = parsed_cv.get("raw_text", "")

        return self.parse_linkedin_text_or_url(
            linkedin_url=parsed_cv.get("contact_info", {}).get("linkedin", ""),
            raw_text=raw_text
        )

    def scrape_personal_website(self, website_url: str) -> Dict[str, Any]:
        """Scrapes candidate's personal portfolio website for bio, projects, and technologies."""
        url = website_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        result = {
            "url": url,
            "title": "",
            "description": "",
            "extracted_text": "",
            "detected_projects": [],
            "detected_tech": []
        }

        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NexusHunt-CareerAgent/2.4"},
                timeout=10
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")

                # Remove scripts and styles
                for s in soup(["script", "style", "noscript"]):
                    s.decompose()

                result["title"] = soup.title.string.strip() if soup.title and soup.title.string else ""

                meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                if meta_desc and meta_desc.get("content"):
                    result["description"] = meta_desc["content"].strip()

                text = soup.get_text(separator="\n")
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                clean_text = "\n".join(lines[:200])  # top 200 lines
                result["extracted_text"] = clean_text[:2000]

                # Extract projects mentioned
                project_headers = soup.find_all(["h2", "h3", "h4"])
                for ph in project_headers[:10]:
                    txt = ph.get_text().strip()
                    if len(txt) > 3 and not any(skip in txt.lower() for skip in ["menu", "navigation", "contact", "about", "skills", "experience"]):
                        result["detected_projects"].append(txt)

                result["detected_tech"] = self._extract_tech_terms(clean_text)
        except Exception as e:
            result["error"] = str(e)
            print(f"[Website Scrape Error]: {e}")

        return result

    def synthesize_master_profile(
        self,
        cv_data_list: List[Dict[str, Any]],
        chat_insights: List[Dict[str, Any]],
        github_data: Optional[Dict[str, Any]] = None,
        linkedin_data: Optional[Dict[str, Any]] = None,
        website_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synthesizes all parsed materials into the canonical Master Persona profile."""
        pb = self.persona_builder
        profile = pb.profile

        # 1. Merge CVs
        if cv_data_list:
            profile = pb.build_from_sources(
                cv_data_list=cv_data_list,
                chat_insights=chat_insights,
                linkedin_data=linkedin_data
            )

        # 2. Enrich with GitHub Data
        if github_data and github_data.get("repositories"):
            repos = github_data["repositories"]
            existing_projects = profile.get("projects", [])
            existing_titles = [p.get("title", "").lower() for p in existing_projects]

            for repo in repos:
                repo_title = repo.get("name", "")
                if not any(repo_title.lower() in t for t in existing_titles):
                    existing_projects.append({
                        "title": repo.get("title") or repo_title,
                        "technologies": repo.get("technologies") or repo.get("language", "Python"),
                        "bullets": repo.get("bullets", [repo.get("description", "")])
                    })

            profile["projects"] = existing_projects

            if github_data.get("profile_url"):
                profile["identity"]["github"] = github_data["profile_url"]

        # 3. Enrich with Personal Website
        if website_data and website_data.get("url"):
            profile["identity"]["website"] = website_data["url"]
            if website_data.get("detected_tech"):
                for t in website_data["detected_tech"]:
                    if t not in profile.get("technical_stack", []):
                        profile.setdefault("technical_stack", []).append(t)

        # 4. Enrich with Chat Insights
        if chat_insights:
            for ci in chat_insights:
                profile.setdefault("inferred_chat_projects", []).append(ci)
                for term in ci.get("key_terms", []):
                    if term not in profile.get("technical_stack", []):
                        profile.setdefault("technical_stack", []).append(term)

        # Rebuild categorized skills
        profile["core_skills_categorized"] = pb._build_categorized_skills(profile.get("technical_stack", []))

        # Save to disk
        pb.profile = profile
        pb.save()
        return profile

    def _extract_tech_terms(self, text: str) -> List[str]:
        known_techs = [
            "Python", "FastAPI", "PostgreSQL", "TimescaleDB", "Docker", "AWS", "Redis",
            "MQTT", "Modbus", "Raspberry Pi", "AsyncIO", "pgvector", "LangGraph", "PyTorch",
            "TensorFlow", "Linux", "GitLab CI/CD", "GitHub Actions", "Ansible", "Java",
            "Node.js", "TypeScript", "React", "Vue", "REST APIs", "GraphQL", "WebSockets"
        ]
        found = []
        for t in known_techs:
            if re.search(rf"\b{re.escape(t)}\b", text, re.IGNORECASE):
                found.append(t)
        return found
