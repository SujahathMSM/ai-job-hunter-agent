"""Fit score: how well the candidate's actual background fits one job posting.

Six weighted factors, each scored 0-1 from the profile and the posting text:

    skills overlap      x3   tools/technologies the posting asks for that the profile has
    years of experience x2   profile years vs the range the posting states
    seniority           x2   level in the job title vs the level the profile's years support
    domain              x2   industries the posting names that appear in the profile
    project relevance   x1   requested tools that show up in the candidate's projects
    education           x1   degree level the posting asks for vs the profile's highest degree

A factor the posting gives no information about is left out and the remaining weights
are rescaled, so a short posting is not penalised for what it doesn't say. Each factor
also produces a one-line reason, which the UI shows next to the score.
"""
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from config import ENGINEERING_KEYWORDS
from generators.fact_checker import _terms_in, estimate_experience_years
from matcher.geo_rules import GeoLocationEngine

WEIGHTS = {"skills": 3, "experience": 2, "seniority": 2, "domain": 2, "projects": 1, "education": 1}
STRONG_FIT, MODERATE_FIT = 80, 60

PRETTY = {
    "fastapi": "FastAPI", "postgresql": "PostgreSQL", "mongodb": "MongoDB", "javascript": "JavaScript",
    "typescript": "TypeScript", "graphql": "GraphQL", "mysql": "MySQL", "pytorch": "PyTorch",
    "tensorflow": "TensorFlow", "github actions": "GitHub Actions", "gitlab": "GitLab", "power bi": "Power BI",
    "langchain": "LangChain", "langgraph": "LangGraph", "llamaindex": "LlamaIndex", "numpy": "NumPy",
    "openai": "OpenAI", "timescaledb": "TimescaleDB", "dynamodb": "DynamoDB", "bigquery": "BigQuery",
    "rabbitmq": "RabbitMQ", "chromadb": "ChromaDB", "websocket": "WebSocket", ".net": ".NET",
    "node.js": "Node.js", "next.js": "Next.js", "nest.js": "NestJS", "scikit-learn": "scikit-learn",
    "pgvector": "pgvector", "sqlite": "SQLite", "elasticsearch": "Elasticsearch", "spring boot": "Spring Boot",
}
UPPER = {"aws", "gcp", "sql", "rag", "sap", "bpmn", "mqtt", "grpc", "ec2", "s3", "dbt", "php"}

DOMAINS: Dict[str, List[str]] = {
    "finance & payments": ["fintech", "payments", "banking", "financial services", "insurance"],
    "oil & gas": ["oil and gas", "oil & gas", "petroleum", "upstream", "downstream", "refinery"],
    "construction & infrastructure": ["construction", "epc", "infrastructure", "civil works", "mega-project"],
    "healthcare": ["healthcare", "hospital", "clinical", "medical", "pharma"],
    "e-commerce & retail": ["e-commerce", "ecommerce", "retail", "marketplace"],
    "logistics": ["logistics", "supply chain", "shipping", "freight", "warehouse"],
    "telecom": ["telecom", "telecommunications", "5g"],
    "energy & utilities": ["energy", "utilities", "power plant", "renewable", "solar", "grid"],
    "real estate": ["real estate", "property management", "proptech"],
    "aviation": ["aviation", "airline", "airport", "aerospace"],
    "public sector": ["government", "public sector", "ministry"],
    "education": ["edtech", "education", "university"],
    "manufacturing": ["manufacturing", "factory", "industrial automation"],
    "iot & telemetry": ["iot", "internet of things", "telemetry", "sensor", "embedded"],
}

LEVEL_NAMES = ["intern", "junior", "mid-level", "senior", "lead", "manager"]
_TITLE_LEVELS: List[Tuple[int, str]] = [
    (0, r"intern|internship|trainee|graduate"),
    (5, r"manager|head of|director|vp"),
    (4, r"lead|staff|principal|architect"),
    (3, r"senior|sr\.?|iii"),
    (1, r"junior|jr\.?|associate|entry[- ]level"),
    (2, r"mid[- ]level|intermediate|ii"),
]

_YEARS_RANGE = re.compile(r"\b(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I)
_YEARS_PLUS = re.compile(r"\b(\d{1,2})\s*\+\s*(?:years?|yrs?)", re.I)
_YEARS_MIN = re.compile(r"\b(?:minimum|at least|min\.?)\s*(?:of\s*)?(\d{1,2})\s*(?:years?|yrs?)", re.I)
_YEARS_PLAIN = re.compile(r"\b(\d{1,2})\s*(?:years?|yrs?)\s*(?:of\s+)?(?:\w+\s+){0,3}(?:experience|exp\b)", re.I)

_EDU_LEVELS: List[Tuple[int, str]] = [
    (4, r"ph\.?d|doctorate"),
    (3, r"master'?s?|m\.?sc|msc|mba|m\.?eng|m\.?tech"),
    (2, r"bachelor'?s?|b\.?sc|bsc|b\.?eng|b\.?e\.|b\.?tech|undergraduate degree|degree in|university degree|graduate degree"),
    (1, r"diploma|associate degree|hnd"),
]
EDU_NAMES = {1: "diploma", 2: "bachelor's degree", 3: "master's degree", 4: "PhD"}


def pretty(term: str) -> str:
    if term in PRETTY:
        return PRETTY[term]
    if term in UPPER:
        return term.upper()
    return term[:1].upper() + term[1:]


def _has(pattern: str, text: str) -> bool:
    return re.search(rf"(?<![\w]){pattern}(?![\w])", text, re.I) is not None


def parse_required_years(text: str) -> Optional[Tuple[int, Optional[int]]]:
    """Return (min, max) years the posting asks for; max is None for open-ended ("5+")."""
    m = _YEARS_RANGE.search(text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return (min(lo, hi), max(lo, hi)) if lo <= 30 and hi <= 40 else None
    for regex in (_YEARS_PLUS, _YEARS_MIN, _YEARS_PLAIN):
        m = regex.search(text)
        if m and int(m.group(1)) <= 30:
            return int(m.group(1)), None
    return None


def title_level(title: str) -> Optional[int]:
    for level, pattern in _TITLE_LEVELS:
        if _has(pattern, title):
            return level
    return None


def level_from_years(years: float) -> int:
    if years < 1:
        return 0
    if years < 2.5:
        return 1
    if years < 5:
        return 2
    if years < 8:
        return 3
    return 4


def education_level(text: str) -> Optional[int]:
    for level, pattern in _EDU_LEVELS:
        if _has(pattern, text):
            return level
    return None


def _component(score: Optional[float], detail: str) -> Dict[str, Any]:
    return {"score": None if score is None else round(max(0.0, min(1.0, score)), 3), "detail": detail}


class JobDescriptionAnalyzer:
    """Scores one job posting against the candidate's master profile."""

    def __init__(self, master_profile: Dict[str, Any]):
        self.master_profile = master_profile or {}
        self.corpus = json.dumps(self.master_profile, ensure_ascii=False).lower()
        self.profile_terms: Set[str] = _terms_in(self.corpus)
        self.profile_years = estimate_experience_years(self.master_profile.get("work_history", []))
        project_text = json.dumps(self.master_profile.get("projects", []), ensure_ascii=False)
        self.project_terms: Set[str] = _terms_in(project_text)
        self.has_projects = bool(self.master_profile.get("projects"))
        self.profile_domains = {d for d, aliases in DOMAINS.items() if any(_has(re.escape(a), self.corpus) for a in aliases)}
        edu_levels = [education_level(json.dumps(e, ensure_ascii=False)) for e in self.master_profile.get("education", [])]
        known_edu = [lvl for lvl in edu_levels if lvl is not None]
        self.profile_edu: Optional[int] = max(known_edu) if known_edu else (0 if not self.master_profile.get("education") else None)
        self.user_skills = self._user_skills()

    def _user_skills(self) -> Set[str]:
        skills: Set[str] = set()
        for cat in self.master_profile.get("core_skills_categorized", []):
            for s in re.split(r"[,;|\n•/]", str(cat.get("skills", ""))):
                s = s.strip().lower()
                if 2 <= len(s) <= 35:
                    skills.add(s)
        for key in ("core_skills", "technical_stack"):
            skills.update(str(s).strip().lower() for s in self.master_profile.get(key, []) if str(s).strip())
        return skills

    # ------------------------------------------------------------------ factors
    def _skills(self, required: Set[str], text: str) -> Tuple[Dict[str, Any], List[str], List[str]]:
        matched = sorted(required & self.profile_terms)
        missing = sorted(required - self.profile_terms)
        if required:
            detail = f"You have {len(matched)} of {len(required)} tools the posting names"
            if missing:
                detail += f" (missing {', '.join(pretty(t) for t in missing[:3])}{'…' if len(missing) > 3 else ''})"
            return _component(len(matched) / len(required), detail), matched, missing
        # Postings outside tech rarely name tools from the vocabulary: fall back to the profile's own skill list.
        own = sorted(s for s in self.user_skills if _has(re.escape(s), text))
        if own:
            return _component(min(1.0, 0.25 * len(own)), f"{len(own)} of your listed skills appear in the posting"), own, []
        return _component(None, "The posting names no specific tools or skills"), [], []

    def _experience(self, text: str) -> Dict[str, Any]:
        req = parse_required_years(text)
        if req is None:
            return _component(None, "The posting doesn't state years of experience")
        if self.profile_years is None:
            return _component(None, "Couldn't work out your years of experience from your work history dates")
        lo, hi = req
        yrs = self.profile_years
        wanted = f"{lo}-{hi}" if hi is not None else f"{lo}+"
        if yrs + 0.25 < lo:
            gap = lo - yrs
            return _component(1 - 0.3 * gap, f"{yrs:.1f} yrs vs {wanted} required ({gap:.1f} yrs short)")
        if hi is not None and yrs > hi + 1:
            return _component(max(0.6, 1 - 0.1 * (yrs - hi)), f"{yrs:.1f} yrs vs {wanted} required (above the range)")
        return _component(1.0, f"{yrs:.1f} yrs fits the {wanted} yrs asked for")

    def _seniority(self, job_title: str, text: str) -> Dict[str, Any]:
        if self.profile_years is None:
            return _component(None, "Couldn't work out your level from your work history")
        job_level = title_level(job_title)
        source = "title"
        if job_level is None:
            req = parse_required_years(text)
            if req is None:
                return _component(None, "The posting doesn't indicate a seniority level")
            job_level, source = level_from_years(req[0] + 0.5), "years asked for"
        mine = level_from_years(self.profile_years)
        diff = job_level - mine
        if diff == 0:
            score = 1.0
        elif diff == -1:
            score = 0.8
        elif diff == 1:
            score = 0.55
        elif diff == 2:
            score = 0.2
        elif diff < -1:
            score = 0.5
        else:
            score = 0.0
        detail = f"{LEVEL_NAMES[job_level].capitalize()} role (from {source}); your experience reads as {LEVEL_NAMES[mine]}"
        return _component(score, detail)

    def _domain(self, text: str) -> Dict[str, Any]:
        wanted = {d for d, aliases in DOMAINS.items() if any(_has(re.escape(a), text) for a in aliases)}
        if not wanted:
            return _component(None, "No specific industry mentioned")
        shared = wanted & self.profile_domains
        if shared:
            return _component(len(shared) / len(wanted), f"You have {', '.join(sorted(shared))} experience")
        return _component(0.0, f"No {', '.join(sorted(wanted))} background in your profile")

    def _projects(self, required: Set[str]) -> Dict[str, Any]:
        if not required or not self.has_projects:
            return _component(None, "No requested tools to compare with your projects" if self.has_projects else "No projects in your profile")
        used = sorted(required & self.project_terms)
        if used:
            return _component(len(used) / len(required), f"Your projects use {', '.join(pretty(t) for t in used[:4])}")
        return _component(0.0, "None of your projects use the requested tools")

    def _education(self, text: str) -> Dict[str, Any]:
        wanted = education_level(text)
        if wanted is None:
            return _component(None, "No degree requirement stated")
        have = self.profile_edu
        if have is None:
            return _component(None, "Couldn't read your degree level from your profile")
        if have >= wanted:
            return _component(1.0, f"Meets the {EDU_NAMES[wanted]} requirement")
        if have == wanted - 1:
            return _component(0.5, f"Asks for a {EDU_NAMES[wanted]}; you have a {EDU_NAMES.get(have, 'lower qualification')}")
        return _component(0.0, f"Asks for a {EDU_NAMES[wanted]}")

    # --------------------------------------------------------------------- main
    def analyze(self, job_title: str, company: str, location: str, jd_text: str,
                enforce_geo: bool = True) -> Dict[str, Any]:
        jd_text = jd_text or ""
        text = f"{job_title}\n{jd_text}"
        is_geo_eligible, geo_reason, geo_meta = GeoLocationEngine.evaluate_location(location, jd_text)
        matched_eng_keywords = [kw for kw in ENGINEERING_KEYWORDS if re.search(rf"\b{kw}\b", text.lower())]

        required = _terms_in(text)
        skills, matched, missing = self._skills(required, text)
        breakdown = {
            "skills": skills,
            "experience": self._experience(jd_text),
            "seniority": self._seniority(job_title, jd_text),
            "domain": self._domain(text),
            "projects": self._projects(required),
            "education": self._education(jd_text),
        }
        for name, comp in breakdown.items():
            comp["weight"] = WEIGHTS[name]

        known = {k: v for k, v in breakdown.items() if v["score"] is not None}
        if enforce_geo and not is_geo_eligible:
            score = 0
            reasons = [f"Location not in your target regions: {geo_reason}"]
        elif not known:
            score = 50
            reasons = ["Not enough detail in the posting to score your fit"]
        else:
            total_w = sum(v["weight"] for v in known.values())
            score = round(100 * sum(v["score"] * v["weight"] for v in known.values()) / total_w)
            # Reasons in order of how much each factor moves the score
            reasons = [v["detail"] for _, v in sorted(known.items(), key=lambda kv: -kv[1]["weight"])]

        if not known and not (enforce_geo and not is_geo_eligible):
            label = "Not enough detail"
        else:
            label = "Strong fit" if score >= STRONG_FIT else ("Moderate fit" if score >= MODERATE_FIT else "Stretch")
        missing_pretty = [pretty(t) for t in missing]
        return {
            "job_title": job_title,
            "company": company,
            "location": location,
            "geo_eligible": is_geo_eligible,
            "geo_reason": geo_reason,
            "geo_meta": geo_meta,
            "is_engineering": bool(matched_eng_keywords),
            "matched_discipline_keywords": matched_eng_keywords[:5],
            "match_score": score,
            "fit_label": label,
            "recommendation": label,
            "fit_reasons": reasons[:4],
            "score_breakdown": breakdown,
            "matched_skills": [pretty(t) if t in required else t.title() for t in matched],
            "missing_tech": missing_pretty[:6],
            "recommended_keywords": missing_pretty[:6],
        }
