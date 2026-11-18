import re
from typing import List, Dict, Any
from hunter.remote_hunter import SimpleTTLCache
from matcher.geo_rules import GeoLocationEngine

GLOBAL_DUBAI_CACHE = SimpleTTLCache(default_ttl=600)

UAE_LOCATIONS = [
    ("Dubai", "Dubai, UAE"),
    ("Abu Dhabi", "Abu Dhabi, UAE"),
    ("Sharjah", "Sharjah, UAE"),
]
CATEGORY_SEARCH_TERMS = {
    "BUSINESS_ANALYST": "Business Analyst",
    "IT_SUPPORT": "IT Support",
    "DOCUMENT_CONTROLLER": "Document Controller",
    "SOFTWARE_DEV": "Software Engineer",
    "DATA_ANALYST": "Data Analyst",
}


def infer_category(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["business analyst", "requirements", "process analyst"]):
        return "BUSINESS_ANALYST"
    if any(k in t for k in ["support", "desktop", "helpdesk", "help desk", "systems administrator"]):
        return "IT_SUPPORT"
    if any(k in t for k in ["document", "records", "aconex"]) or re.search(r"\bdocument controller\b", t):
        return "DOCUMENT_CONTROLLER"
    if any(k in t for k in ["data analyst", "bi analyst", "analytics", "business intelligence"]):
        return "DATA_ANALYST"
    return "SOFTWARE_DEV"


class DubaiJobHunter:
    """Specialized Dubai & UAE Career Hunter targeting:
    - Business Analyst & Operations Analyst
    - IT Support & Systems Administrators
    - Document Controllers & Technical Project Coordinators
    - Software Engineers (Python, Backend, Full Stack)
    - Data & Performance Analysts
    Live postings only, from every job board that covers the UAE."""

    def search_dubai_jobs(
        self,
        keyword: str = "",
        category: str = "ALL",  # ALL, BUSINESS_ANALYST, IT_SUPPORT, DOCUMENT_CONTROLLER, SOFTWARE_DEV, DATA_ANALYST
        max_results: int = 40
    ) -> List[Dict[str, Any]]:
        cache_key = f"dubai_{keyword.lower().strip()}_{category}_{max_results}"
        cached = GLOBAL_DUBAI_CACHE.get(cache_key)
        if cached is not None:
            return cached

        from hunter.job_sources import scrape_location

        results: List[Dict[str, Any]] = []
        seen = set()
        kw_clean = keyword.strip()
        search_term = kw_clean or CATEGORY_SEARCH_TERMS.get(category, "Engineer")
        per_city = max(8, min(25, max_results // len(UAE_LOCATIONS) + 5))

        # Live postings only: every board covering the UAE, newest posting window first
        for city, display in UAE_LOCATIONS:
            for job in scrape_location(search_term, city, "united arab emirates", display, per_city):
                key = (job["company"].lower(), job["job_title"].lower())
                if key in seen:
                    continue
                _, _, geo = GeoLocationEngine.evaluate_location(job["location"], f"{job['job_title']} {job['full_description']}")
                if geo.get("category") == "EXCLUDED":
                    continue
                cat = infer_category(job["job_title"])
                if category != "ALL" and cat != category:
                    continue
                seen.add(key)
                loc = job["location"]
                results.append({
                    **job,
                    "id": f"dubai_live_{abs(hash(key)) % 10_000_000}",
                    "location": loc if any(k in loc.lower() for k in ("dubai", "uae", "abu dhabi", "sharjah", "emirates")) else f"{loc}, UAE",
                    "category": cat,
                    "description": job["description"] or f"Opening for {job['job_title']} at {job['company']}.",
                    "tags": [cat.replace("_", " ").title(), job["site"]],
                    "source": f"{job['site']} (Live)",
                    "posted_at": job["date_posted"],
                    "is_dubai": True,
                })

        # Newest first (the API re-sorts by the user's fit score)
        results.sort(key=lambda x: x.get("date_posted") or "0000-00-00", reverse=True)
        GLOBAL_DUBAI_CACHE.set(cache_key, results)
        return results[:max_results]
