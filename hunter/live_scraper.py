import re
from typing import List, Dict, Any, Optional
import requests
from matcher.geo_rules import GeoLocationEngine
from hunter.hr_finder import HRFinder
from config import RAPIDAPI_KEY, EXPANDED_LOCATION_TARGETS
from hunter.freshness import assess
from hunter.job_sources import clean_description, scrape_location

class LiveJobHunter:
    """Live job search across Indeed, LinkedIn, Glassdoor, Google Jobs and the regional boards
    (ZipRecruiter, Bayt, Naukri, ...) for each target location. Applies region rules, a
    posting-age limit, and the strict exclusion list."""

    # Key regional hubs
    GULF_LOCATIONS = [
        "Dubai, United Arab Emirates",
        "Abu Dhabi, United Arab Emirates",
        "Riyadh, Saudi Arabia",
        "Doha, Qatar",
        "Muscat, Oman"
    ]

    MIGRATABLE_LOCATIONS = [
        "Singapore",
        "Berlin, Germany",
        "London, United Kingdom",
        "Sydney, Australia"
    ]

    # Blacklist of non-engineering job titles that web scrapers sometimes mistakenly return
    EXCLUDED_TITLE_KEYWORDS = [
        "library", "librarian", "art", "arts", "stage", "drama", "teacher", "teaching",
        "nurse", "nursing", "driver", "cook", "chef", "cleaner", "receptionist",
        "waiter", "cashier", "housekeeping", "sales executive", "storekeeper",
        "fitness", "gym", "beautician", "barista"
    ]

    # Aggregator search result pages / SEO spam (e.g. "417 Vacancies", "4784 Jobs", "Jobs in Dubai")
    AGGREGATOR_PATTERNS = [
        r"\b\d+[\d,]*\+?\s+vacanc(ies|y)\b",
        r"\b\d+[\d,]*\+?\s+jobs\b",
        r"\b\d+[\d,]*\+?\s+openings\b",
        r"\bwith salaries\b",
        r"\bjob search\b",
        r"\bbrowse jobs\b",
        r"\bjobs in\b",
        r"\bvacancies in\b",
        r"\bopen vacancies\b",
    ]

    # Required engineering title indicators
    REQUIRED_TITLE_KEYWORDS = [
        "engineer", "developer", "architect", "programmer", "systems", "software",
        "backend", "frontend", "fullstack", "embedded", "firmware", "hardware",
        "iot", "cloud", "devops", "data", "platform", "technical", "technologies",
        "qa", "specialist", "controls", "automation", "solutions", "lead", "ai", "ml", "nlp",
        "analyst", "support", "document", "controller", "coordinator", "administrator", "it", "officer"
    ]

    def _is_legitimate_engineering_job(self, title: str) -> bool:
        t_lower = title.lower()
        # Reject aggregator SEO category pages (e.g. "417 Vacancies in Dubai")
        if any(re.search(pat, t_lower) for pat in self.AGGREGATOR_PATTERNS):
            return False
        if any(re.search(rf"\b{kw}\b", t_lower) for kw in self.EXCLUDED_TITLE_KEYWORDS):
            return False
        if not any(re.search(rf"\b{kw}\b", t_lower) for kw in self.REQUIRED_TITLE_KEYWORDS):
            return False
        return True

    def _expand_search_queries(self, keyword: str) -> List[str]:
        """Expands narrow search terms into broader related engineering queries for wider coverage."""
        kw = keyword.strip()
        if not kw:
            return ["Software Engineer", "Backend Engineer", "AI Engineer"]

        kw_lower = kw.lower()
        queries = [kw]

        if not any(term in kw_lower for term in ["engineer", "developer", "software", "architect", "specialist", "analyst", "support", "controller", "coordinator", "administrator"]):
            queries.append(f"{kw} Engineer")

        # Focused domain expansions without polluting other languages/stacks
        if any(term in kw_lower for term in ["rag", "llm", "genai", "generative ai", "langgraph", "agent"]):
            queries.extend(["AI Engineer", "LLM Engineer", "Generative AI Engineer"])
        elif any(term in kw_lower for term in ["embedded", "firmware", "iot"]):
            queries.extend(["IoT Engineer", "Embedded Systems Engineer", "Firmware Engineer"])
        elif "python" in kw_lower:
            queries.extend(["Python Engineer", "Python Backend Developer", "Software Engineer Python"])
        elif "backend" in kw_lower:
            queries.extend(["Backend Engineer", "API Engineer", "Systems Engineer"])
        elif "business analyst" in kw_lower or kw_lower == "ba":
            queries.extend(["Business Analyst", "Technical Business Analyst", "Operations Analyst", "Systems Analyst"])
        elif "it support" in kw_lower or "support" in kw_lower:
            queries.extend(["IT Support Specialist", "IT Systems Support", "Desktop Support Engineer", "System Administrator"])
        elif "document" in kw_lower or "controller" in kw_lower:
            queries.extend(["Document Controller", "Technical Document Controller", "Project Document Controller", "Technical Coordinator"])
        elif "data" in kw_lower:
            queries.extend(["Data Engineer", "Data Analyst", "Data Platform Engineer"])

        seen = set()
        unique = []
        for q in queries:
            clean_q = q.strip()
            if clean_q.lower() not in seen:
                seen.add(clean_q.lower())
                unique.append(clean_q)
        return unique[:3]

    @staticmethod
    def clean_description(text: str) -> str:
        return clean_description(text)

    # ----------------------------------------------------------------- filters
    @staticmethod
    def region_meta(location: str, text: str, region: str) -> Optional[Dict[str, Any]]:
        """Geo metadata if the posting belongs to the region, else None.
        The strict exclusion list applies to every region, including WORLDWIDE."""
        is_el, _reason, meta = GeoLocationEngine.evaluate_location(location, text)
        if meta.get("category") == "EXCLUDED":
            return None
        if region == "WORLDWIDE":
            if meta.get("category") == "OUT_OF_TARGET":
                meta = {"category": "WORLDWIDE", "matched_location": location}
            return meta
        if not is_el:
            return None
        if region == "DUBAI":
            loc_check = f"{location} {text[:500]}".lower()
            return meta if any(k in loc_check for k in ["dubai", "uae", "united arab emirates", "abu dhabi", "sharjah", "ajman"]) else None
        if region == "GULF" and meta.get("category") != "GULF":
            return None
        if region == "MIGRATABLE" and meta.get("category") != "MIGRATABLE_GLOBAL":
            return None
        return meta

    def _keyword_aligned(self, keyword: str, title: str, desc: str) -> bool:
        kw_term = keyword.lower().strip()
        title_lower, desc_lower = title.lower(), desc.lower()
        if "python" in kw_term:
            if any(w in title_lower for w in ["java", "salesforce", "payment acceptance", "hr manager", "wordpress", "php", "c#", ".net", "dotnet"]):
                return False
            if "python" not in title_lower:
                compatible = ["backend", "software engineer", "data engineer", "ai engineer", "machine learning", "cloud engineer", "full stack"]
                if not any(ct in title_lower for ct in compatible) or "python" not in desc_lower:
                    return False
        elif "iot" in kw_term:
            if not any(w in title_lower or w in desc_lower[:400] for w in ["iot", "embedded", "firmware", "hardware", "telemetry", "sensor"]):
                return False
        return True

    def _accept(self, job: Dict[str, Any], keyword: str, region: str) -> bool:
        title = job.get("job_title", "")
        desc = job.get("full_description") or job.get("description", "")
        if not self._is_legitimate_engineering_job(title):
            return False
        if not self._keyword_aligned(keyword, title, desc):
            return False
        meta = self.region_meta(job.get("location", ""), f"{title} {desc}", region)
        if meta is None:
            return False
        job["geo_meta"] = meta
        return True

    # ---------------------------------------------------------------- scraping
    def stream_live(
        self,
        keyword: str = "engineer",
        region_filter: str = "ALL",
        max_results: int = 15,
        max_days_old: int = 14
    ):
        """Yields live postings one by one as each location returns, searching every job
        board that covers that location (see hunter/job_sources.py)."""
        region = (region_filter or "ALL").upper()
        targets = EXPANDED_LOCATION_TARGETS.get(region, EXPANDED_LOCATION_TARGETS["ALL"])
        queries = self._expand_search_queries(keyword)
        per_location = max(5, min(20, max_results // len(targets) + 4))
        seen = set()
        count = 0

        for q in queries:
            for loc in targets:
                if count >= max_results:
                    return
                for job in scrape_location(q, loc["city"], loc["country"], loc["display"], per_location, max_days_old):
                    key = (job["job_title"].lower(), job["company"].lower())
                    if key in seen or not self._accept(job, keyword, region):
                        continue
                    seen.add(key)
                    count += 1
                    job["id"] = f"live-{count}"
                    yield job
                    if count >= max_results:
                        return

    def search_live(
        self,
        keyword: str = "engineer",
        region_filter: str = "ALL",  # "ALL", "GULF", "MIGRATABLE", "DUBAI", "WORLDWIDE"
        max_results: int = 25,
        max_days_old: int = 14,
        *args,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Collects live postings from every board for the region, newest first."""
        region = (region_filter or "ALL").upper()
        jobs = list(self.stream_live(keyword, region, max_results, max_days_old))

        if RAPIDAPI_KEY:
            seen = {(j["job_title"].lower(), j["company"].lower()) for j in jobs}
            for j in self._scrape_with_jsearch(self._expand_search_queries(keyword)[0], region, max_days_old=max_days_old):
                key = (j["job_title"].lower(), j["company"].lower())
                if key not in seen and self._accept(j, keyword, region):
                    seen.add(key)
                    jobs.append(j)

        # Newest first; postings known only to be inside the search window go last
        jobs.sort(key=lambda j: j.get("date_posted") or "0000-00-00", reverse=True)
        return jobs

    def _scrape_with_jsearch(self, query: str, region_filter: str, max_results: int = 10, max_days_old: int = 14) -> List[Dict[str, Any]]:
        """Optional JSearch API via RapidAPI (aggregated Google Jobs listings)."""
        if not RAPIDAPI_KEY:
            return []
        loc = {
            "GULF": "Dubai, UAE", "DUBAI": "Dubai, UAE", "MIGRATABLE": "Singapore",
        }.get(region_filter, "Dubai OR Singapore OR London" if region_filter != "WORLDWIDE" else "")
        params = {
            "query": f"{query} in {loc}" if loc else query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "week" if max_days_old <= 7 else "month",
        }
        headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"}
        results: List[Dict[str, Any]] = []
        try:
            resp = requests.get("https://jsearch.p.rapidapi.com/search", headers=headers, params=params, timeout=12)
            if resp.status_code != 200:
                return []
            for item in resp.json().get("data", [])[:max_results]:
                fresh = assess(item.get("job_posted_at_datetime_utc"), max_days_old)
                if fresh is None:
                    continue
                desc = item.get("job_description", "") or ""
                emails = HRFinder.extract_emails_from_text(desc)
                link = item.get("job_apply_link", "")
                location = f"{item.get('job_city') or ''}, {item.get('job_country') or ''}".strip(", ") or loc
                results.append({
                    "id": f"jsearch-{len(results) + 1}",
                    "job_title": item.get("job_title", ""),
                    "company": item.get("employer_name", ""),
                    "location": location,
                    "site": "Google Jobs (JSearch)",
                    "portal": link,
                    "job_url": link,
                    "apply_url": link,
                    "hr_email": emails[0] if emails else "",
                    "has_hr_email": bool(emails),
                    "description": re.sub(r"\s+", " ", desc)[:300],
                    "full_description": desc[:5000],
                    **fresh,
                })
        except Exception as e:
            print(f"[JSearch API Error]: {e}")
        return results
