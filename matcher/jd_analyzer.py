import re
from typing import Dict, Any, List, Set
from config import ENGINEERING_KEYWORDS
from matcher.geo_rules import GeoLocationEngine

class JobDescriptionAnalyzer:
    """Analyzes job descriptions for engineering discipline alignment,
    extracts requirements, keywords, and computes ATS match scores against Master Profile."""

    def __init__(self, master_profile: Dict[str, Any]):
        self.master_profile = master_profile

    def analyze(self, job_title: str, company: str, location: str, jd_text: str) -> Dict[str, Any]:
        # 1. Geographic eligibility & strict exclusion check
        is_geo_eligible, geo_reason, geo_meta = GeoLocationEngine.evaluate_location(location, jd_text)

        # 2. Engineering relevance check
        combined_text = f"{job_title} {jd_text}".lower()
        matched_eng_keywords = [kw for kw in ENGINEERING_KEYWORDS if re.search(rf"\b{kw}\b", combined_text)]
        is_engineering = len(matched_eng_keywords) > 0

        # 3. Extract technical keywords from JD
        jd_words = set(re.findall(r"\b[A-Za-z0-9+#.]{2,20}\b", jd_text.lower()))
        
        # User skills pool
        user_skills: Set[str] = set()
        for cat in self.master_profile.get("core_skills_categorized", []):
            for s in re.split(r"[,;|\n•/]", cat.get("skills", "")):
                clean_s = s.strip().lower()
                if 2 <= len(clean_s) <= 35:
                    user_skills.add(clean_s)
        for s in self.master_profile.get("core_skills", []):
            user_skills.add(s.lower())
        for s in self.master_profile.get("technical_stack", []):
            user_skills.add(s.lower())

        # Direct skill overlap
        matched_skills = []
        for skill in user_skills:
            if re.search(rf"\b{re.escape(skill)}\b", jd_text.lower()) or re.search(rf"\b{re.escape(skill)}\b", job_title.lower()):
                matched_skills.append(skill.title())

        # Inferred missing / recommended keywords to address in cover letter or highlighted projects
        potential_tech = set(re.findall(r"\b(?:python|react|docker|kubernetes|aws|azure|sql|c\+\+|cad|solidworks|plc|ansys|sap|graphql|linux|ci/cd|terraform|scada|matlab|revit|agile|scrum|embedded|mqtt|modbus|timescaledb)\b", jd_text.lower()))
        unmatched_tech = [t.title() for t in potential_tech if t not in [s.lower() for s in matched_skills]]

        # Compute realistic, multi-factor ATS match percentage
        if not is_engineering or not is_geo_eligible:
            total_score = 0
            breakdown = {"title_match": 0, "skills_overlap": 0, "systems_depth": 0}
        else:
            # 1. Title match (0 - 25 points)
            title_lower = job_title.lower()
            core_roles = [
                "software", "backend", "systems", "python", "ai", "data", "platform", "engineer", "developer",
                "analyst", "support", "document", "controller", "coordinator", "administrator", "specialist"
            ]
            title_hits = sum(1 for r in core_roles if r in title_lower)
            title_score = min(title_hits * 8, 25)

            # 2. Skills overlap (0 - 50 points)
            unique_matched = set(s.lower() for s in matched_skills)
            skill_score = min(len(unique_matched) * 6, 50)

            # 3. Systems engineering & production depth (0 - 25 points)
            depth_terms = ["production", "scale", "api", "architecture", "docker", "cloud", "aws", "database", "sql", "ci/cd", "reliability"]
            depth_hits = sum(1 for term in depth_terms if term in combined_text)
            depth_score = min(depth_hits * 3, 25)

            total_score = max(min(title_score + skill_score + depth_score, 98), 40)
            breakdown = {
                "title_match": title_score,
                "skills_overlap": skill_score,
                "systems_depth": depth_score
            }

        return {
            "job_title": job_title,
            "company": company,
            "location": location,
            "geo_eligible": is_geo_eligible,
            "geo_reason": geo_reason,
            "geo_meta": geo_meta,
            "is_engineering": is_engineering,
            "matched_discipline_keywords": matched_eng_keywords[:5],
            "match_score": total_score,
            "score_breakdown": breakdown,
            "matched_skills": matched_skills,
            "recommended_keywords": unmatched_tech[:6],
            "recommendation": "Strong Match" if total_score >= 75 else ("Fair Match" if total_score >= 50 else "Weak Match")
        }
