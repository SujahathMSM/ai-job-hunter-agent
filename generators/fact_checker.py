"""Deterministic (no-LLM) fact checker for tailored CVs and cover letters.

The LLM Reviewer can miss things or be unavailable, so this module provides a
rule-based safety net that compares a draft against the candidate's master
profile and flags:

* technologies / tools that appear in the draft but nowhere in the profile
* numeric claims (percentages, money, multipliers, team sizes) not in the profile
* "N years of experience" claims larger than the experience the profile supports
"""
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

# canonical term -> aliases (all lowercase). Matching is word-boundary based.
TECH_VOCAB: Dict[str, List[str]] = {
    "python": [], "java": [], "javascript": ["js"], "typescript": ["ts"],
    "node.js": ["nodejs", "node js"], "golang": [], "rust": [], "c++": [], "c#": [],
    ".net": ["dotnet"], "php": [], "ruby": [], "kotlin": [], "swift": [], "scala": [],
    "fastapi": [], "django": [], "flask": [], "express": ["express.js", "expressjs"],
    "nest.js": ["nestjs"], "spring boot": ["springboot"], "laravel": [], "rails": [],
    "react": ["react.js", "reactjs"], "react native": [], "vue": ["vue.js", "vuejs"],
    "angular": [], "next.js": ["nextjs"], "tailwind": [],
    "sql": [], "postgresql": ["postgres"], "mysql": [], "mongodb": ["mongo"],
    "redis": [], "timescaledb": [], "sqlite": [], "dynamodb": [], "cassandra": [],
    "elasticsearch": ["opensearch"], "snowflake": [], "bigquery": [],
    "kafka": [], "rabbitmq": [], "mqtt": [], "grpc": [], "graphql": [], "websocket": ["websockets"],
    "docker": [], "kubernetes": ["k8s"], "terraform": [], "ansible": [], "jenkins": [],
    "gitlab": [], "github actions": [], "helm": [], "prometheus": [], "grafana": [],
    "aws": ["amazon web services"], "azure": [], "gcp": ["google cloud"],
    "ec2": [], "lambda": [], "s3": [], "linux": [],
    "pytorch": [], "tensorflow": [], "scikit-learn": ["sklearn"], "pandas": [], "numpy": [],
    "langchain": [], "llamaindex": ["llama-index", "llama index"], "langgraph": [],
    "chromadb": ["chroma"], "pinecone": [], "pgvector": [], "ollama": [],
    "openai": [], "rag": [], "spark": ["pyspark"], "hadoop": [], "airflow": [], "dbt": [],
    "power bi": ["powerbi"], "tableau": [], "selenium": [], "pytest": [],
    "jira": [], "sap": [], "aconex": [], "bpmn": [], "salesforce": [],
}

_NUM_PATTERNS = [
    # percentages: 80%, 99.71 %
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    # multipliers: 10x, 3.5x
    re.compile(r"\b\d+(?:\.\d+)?x\b", re.I),
    # money: $50M, $1.2 million, USD 500k
    re.compile(r"(?:\$|usd\s?|aed\s?|eur\s?|£|€)\s?\d[\d,]*(?:\.\d+)?\s?(?:k|m|bn|b|million|billion)?\b", re.I),
    # team / scale claims: team of 12, managed 8 engineers, 5000 users
    re.compile(r"\b(?:team of|managed|led|mentored)\s+\d+\b", re.I),
    re.compile(r"\b\d[\d,]*\+?\s+(?:users|customers|clients|engineers|developers|employees|requests|transactions)\b", re.I),
]
_YEARS_RE = re.compile(r"\b(\d{1,2})\s?\+?\s?(?:years?|yrs?)\b", re.I)

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
_DURATION_RE = re.compile(
    r"(?:(?P<m1>[A-Za-z]{3})[a-z]*\.?\s+)?(?P<y1>(?:19|20)\d{2})\s*[-–—to]+\s*"
    r"(?:(?P<present>present|current|now|ongoing)|(?:(?P<m2>[A-Za-z]{3})[a-z]*\.?\s+)?(?P<y2>(?:19|20)\d{2}))",
    re.I,
)


def _norm_number(token: str) -> str:
    return re.sub(r"[\s,]", "", token.lower())


def _term_regex(term: str) -> re.Pattern:
    return re.compile(r"(?<![\w+#.])" + re.escape(term) + r"(?![\w+#])", re.I)


def _terms_in(text: str) -> Set[str]:
    """Return canonical vocabulary terms present in text."""
    found: Set[str] = set()
    for canon, aliases in TECH_VOCAB.items():
        for variant in [canon] + aliases:
            if _term_regex(variant).search(text):
                found.add(canon)
                break
    return found


def estimate_experience_years(work_history: List[Dict[str, Any]]) -> Optional[float]:
    """Estimate total years of experience from profile durations. None if unparseable."""
    total_months = 0
    parsed_any = False
    now = datetime.now()
    for job in work_history or []:
        m = _DURATION_RE.search(str(job.get("duration", "")))
        if not m:
            continue
        parsed_any = True
        y1 = int(m.group("y1"))
        m1 = _MONTHS.get((m.group("m1") or "jan")[:3].lower(), 1)
        if m.group("present"):
            y2, m2 = now.year, now.month
        else:
            y2 = int(m.group("y2"))
            m2 = _MONTHS.get((m.group("m2") or "dec")[:3].lower(), 12)
        total_months += max(0, (y2 - y1) * 12 + (m2 - m1) + 1)
    return total_months / 12.0 if parsed_any else None


class FactChecker:
    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile or {}
        self.corpus = json.dumps(self.profile, ensure_ascii=False).lower()
        self.profile_terms = _terms_in(self.corpus)
        self.profile_numbers = {
            _norm_number(m.group(0))
            for pat in _NUM_PATTERNS for m in pat.finditer(self.corpus)
        }
        self.experience_years = estimate_experience_years(self.profile.get("work_history", []))

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def collect_sections(resume: Dict[str, Any], cover_letter: str = "") -> Dict[str, str]:
        """Flatten a tailored resume into named text sections (title is excluded
        because it intentionally mirrors the target role)."""
        sections: Dict[str, str] = {}
        sections["summary"] = str(resume.get("summary") or resume.get("tailored_summary") or "")
        sections["subtitle"] = str(resume.get("tailored_subtitle") or "")
        skills = resume.get("core_skills_categorized") or []
        sections["skills"] = " ; ".join(
            f"{c.get('category', '')}: {c.get('skills', '')}" for c in skills if isinstance(c, dict)
        )
        work_parts: List[str] = []
        for job in resume.get("work_history") or []:
            work_parts.extend(str(b) for b in job.get("bullets", []))
        sections["work bullets"] = "\n".join(work_parts)
        proj_parts: List[str] = []
        for proj in resume.get("projects") or []:
            proj_parts.extend(str(b) for b in proj.get("bullets", []))
            tech = proj.get("technologies", "")
            proj_parts.append(", ".join(tech) if isinstance(tech, list) else str(tech))
        sections["project details"] = "\n".join(proj_parts)
        sections["cover letter"] = cover_letter or ""
        return sections

    # -------------------------------------------------------------------- checks
    def check(self, resume: Dict[str, Any], cover_letter: str = "") -> Dict[str, Any]:
        sections = self.collect_sections(resume, cover_letter)
        flags: List[Dict[str, str]] = []
        seen: Set[str] = set()

        def add(kind: str, claim: str, section: str, detail: str):
            key = f"{kind}:{claim.lower()}"
            if key in seen:
                return
            seen.add(key)
            flags.append({"type": kind, "claim": claim, "section": section, "detail": detail})

        for section, text in sections.items():
            if not text:
                continue
            for term in sorted(_terms_in(text) - self.profile_terms):
                add("unverified_tool", term, section,
                    f"'{term}' is not mentioned anywhere in the candidate profile.")
            for pat in _NUM_PATTERNS:
                for m in pat.finditer(text):
                    token = m.group(0).strip()
                    if _norm_number(token) not in self.profile_numbers:
                        add("unverified_metric", token, section,
                            f"'{token}' does not appear in the candidate profile.")
            if self.experience_years is not None:
                for m in _YEARS_RE.finditer(text):
                    claimed = int(m.group(1))
                    if claimed > int(self.experience_years) + 1:
                        add("inflated_experience", m.group(0), section,
                            f"Claims {claimed} years but profile supports about {self.experience_years:.1f}.")

        score = max(0, 100 - 12 * len(flags))
        return {"flags": flags, "score": score, "clean": not flags}

    # ------------------------------------------------------------- sanitization
    def strip_unverified_skills(self, resume: Dict[str, Any]) -> List[str]:
        """Remove skill items containing vocabulary terms absent from the profile.
        Mutates resume['core_skills_categorized'] in place; returns removed items."""
        removed: List[str] = []
        cleaned_categories = []
        for cat in resume.get("core_skills_categorized") or []:
            if not isinstance(cat, dict):
                cleaned_categories.append(cat)
                continue
            items = [s.strip() for s in str(cat.get("skills", "")).split(",") if s.strip()]
            kept = []
            for item in items:
                if _terms_in(item) - self.profile_terms:
                    removed.append(item)
                else:
                    kept.append(item)
            if kept:
                cleaned_categories.append({**cat, "skills": ", ".join(kept)})
        if resume.get("core_skills_categorized") is not None:
            resume["core_skills_categorized"] = cleaned_categories
        return removed


def format_feedback(flags: List[Dict[str, str]]) -> str:
    """Turn flags into revision instructions for the Drafter."""
    lines = ["A fact-check found unsupported claims in your previous draft. Remove or rephrase them using ONLY facts from the candidate profile:"]
    for f in flags[:12]:
        lines.append(f"- [{f['section']}] {f['claim']}: {f['detail']}")
    return "\n".join(lines)
