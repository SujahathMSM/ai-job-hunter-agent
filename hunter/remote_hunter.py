import re
import time
import requests
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import List, Dict, Any, Optional
from hunter.freshness import MAX_POSTING_AGE_DAYS, assess

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 NexusHuntAI/2.4"
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/xml, */*"
}

SCRAPER_TIMEOUT = (2.0, 3.5)  # 2.0s connect timeout, 3.5s read timeout (prevents proxy socket hang-ups)

class SimpleTTLCache:
    """Thread-safe in-memory cache with Time-To-Live (TTL) expiration.
    Guarantees sub-5ms response times and eliminates external API rate-limiting under load."""

    def __init__(self, default_ttl: int = 900, max_items: int = 300):
        self.default_ttl = default_ttl
        self.max_items = max_items
        self._store: Dict[str, tuple] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            val, expire_at = entry
            if time.time() > expire_at:
                del self._store[key]
                return None
            return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        with self._lock:
            now = time.time()
            if len(self._store) >= self.max_items:
                self._store = {k: v for k, v in self._store.items() if v[1] > now}
                if len(self._store) >= self.max_items:
                    oldest = min(self._store, key=lambda k: self._store[k][1])
                    del self._store[oldest]
            self._store[key] = (value, now + (ttl or self.default_ttl))

    def clear(self):
        with self._lock:
            self._store.clear()

GLOBAL_REMOTE_CACHE = SimpleTTLCache(default_ttl=900)  # 15 minutes TTL

EXCLUDED_TERMS = ["israel", "tel aviv", "tel-aviv", "tlv", "jerusalem", "haifa", "beer sheva", "herzliya", "ra'anana", "petah tikva"]

RESTRICTED_LOCATION_PATTERNS = [
    r"\bus\s*only\b",
    r"\busa\s*only\b",
    r"\bunited\s*states\s*only\b",
    r"\bcanada\s*only\b",
    r"\buk\s*only\b",
    r"\beurope\s*only\b",
    r"\beu\s*only\b",
    r"\bnorth\s*america\s*only\b",
    r"\blatam\s*only\b",
    r"\blatin\s*america\s*only\b",
    r"\btimezone:\s*est\b",
    r"\bmust\s*reside\s*in\s*the\s*us\b",
    r"\bmust\s*be\s*located\s*in\s*us\b",
    r"\bus\s*citizenship\s*required\b",
    r"\bus\s*work\s*authorization\b",
]

COUNTRY_RESTRICTIONS = [
    r"\bcanada\b", r"\busa\b", r"\bunited\s*states\b", r"\bu\.s\.", r"\buk\b",
    r"\bunited\s*kingdom\b", r"\bgermany\b", r"\bfrance\b", r"\baustralia\b",
    r"\beurope\b", r"\bnorth\s*america\b", r"\blatam\b", r"\blatin\s*america\b"
]

def clean_html(raw_html: str) -> str:
    """Strips HTML tags and unescapes entities for clean reading."""
    if not raw_html:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", raw_html, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\*{2,3}(.*?)\*{2,3}", r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def is_worldwide_open(location_str: str, description_str: str = "") -> bool:
    """Checks whether a remote job is open worldwide rather than restricted to US/EU/Canada."""
    combined = f"{location_str} {description_str}".lower()

    # Strict zero tolerance for Israel
    if any(ex in combined for ex in EXCLUDED_TERMS):
        return False

    # Check for hard country restriction phrases
    for pat in RESTRICTED_LOCATION_PATTERNS:
        if re.search(pat, combined, re.IGNORECASE):
            return False

    loc_lower = (location_str or "").lower().strip()
    loc_clean = re.sub(r"[🌐\s]+", " ", loc_lower).strip()

    # Explicit positive signals for worldwide openness
    positives = [
        "worldwide", "anywhere", "global", "work from anywhere", 
        "open globally", "home based", "apac", "emea", "any location", 
        "all countries", "remote - anywhere"
    ]
    if any(p in loc_clean for p in positives):
        return True

    # If location explicitly specifies countries (e.g. 'Canada, USA', 'United States', 'UK') without Worldwide
    for cr in COUNTRY_RESTRICTIONS:
        if re.search(cr, loc_clean):
            return False

    # If it is simply 'remote' or empty, inspect description
    if loc_clean in ["remote", "", "full remote", "remote / flexible"]:
        for pat in RESTRICTED_LOCATION_PATTERNS:
            if re.search(pat, description_str.lower(), re.IGNORECASE):
                return False
        return True

    return False

class GlobalRemoteHunter:
    """Concurrently scrapes and aggregates 100% remote job listings open worldwide
    from unauthenticated JSON APIs, RSS feeds, and direct AI/Tech ATS endpoints."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)

    # 1. RemoteOK API
    def fetch_remoteok(self, keyword: str = "python") -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = f"https://remoteok.com/api?tags={requests.utils.quote(keyword)}"
            r = self.session.get(url, timeout=SCRAPER_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                # Index 0 is legal notice, jobs start at index 1
                for item in data[1:]:
                    pos = item.get("position") or ""
                    comp = item.get("company") or ""
                    loc = item.get("location") or "Worldwide"
                    desc = clean_html(item.get("description") or "")
                    apply_url = item.get("apply_url") or item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}"

                    sal_min = item.get("salary_min")
                    sal_max = item.get("salary_max")
                    salary = f"${sal_min:,} - ${sal_max:,}" if sal_min and sal_max else ""

                    tags = item.get("tags") or []
                    date_posted = item.get("date") or ""

                    jobs.append({
                        "job_id": f"remoteok_{item.get('id')}",
                        "job_title": pos,
                        "company": comp,
                        "location": "🌐 Worldwide / Remote" if not loc or "world" in loc.lower() or "any" in loc.lower() else f"🌐 {loc}",
                        "salary": salary,
                        "portal": apply_url,
                        "description": desc[:3000],
                        "tags": tags[:6],
                        "source": "RemoteOK",
                        "date_posted": str(date_posted),
                        "is_worldwide": is_worldwide_open(loc, desc[:500])
                    })
        except Exception as e:
            print(f"[RemoteOK Error]: {e}")
        return jobs

    # 2. Remotive API
    def fetch_remotive(self, keyword: str = "python") -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = f"https://remotive.com/api/remote-jobs?search={requests.utils.quote(keyword)}"
            r = self.session.get(url, timeout=SCRAPER_TIMEOUT)
            if r.status_code == 200:
                data = r.json().get("jobs", [])
                for item in data:
                    title = item.get("title") or ""
                    comp = item.get("company_name") or ""
                    req_loc = item.get("candidate_required_location") or "Worldwide"
                    desc = clean_html(item.get("description") or "")
                    salary = item.get("salary") or ""
                    url = item.get("url") or ""
                    tags = item.get("tags") or []
                    pub = item.get("publication_date") or ""

                    jobs.append({
                        "job_id": f"remotive_{item.get('id')}",
                        "job_title": title,
                        "company": comp,
                        "location": f"🌐 {req_loc}",
                        "salary": salary,
                        "portal": url,
                        "description": desc[:3000],
                        "tags": tags[:6],
                        "source": "Remotive",
                        "date_posted": str(pub),
                        "is_worldwide": is_worldwide_open(req_loc, desc[:500])
                    })
        except Exception as e:
            print(f"[Remotive Error]: {e}")
        return jobs

    # 3. Jobicy API
    def fetch_jobicy(self, keyword: str = "python") -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = f"https://jobicy.com/api/v2/remote-jobs?count=30&tag={requests.utils.quote(keyword)}"
            r = self.session.get(url, timeout=SCRAPER_TIMEOUT)
            if r.status_code == 200:
                data = r.json().get("jobs", [])
                for item in data:
                    title = item.get("jobTitle") or ""
                    comp = item.get("companyName") or ""
                    geo = item.get("jobGeo") or "Anywhere"
                    desc = clean_html(item.get("jobDescription") or "")
                    s_min = item.get("annualSalaryMin")
                    s_max = item.get("annualSalaryMax")
                    cur = item.get("salaryCurrency") or "USD"
                    salary = f"{cur} {s_min:,} - {s_max:,}" if s_min and s_max else ""

                    jobs.append({
                        "job_id": f"jobicy_{item.get('id')}",
                        "job_title": title,
                        "company": comp,
                        "location": f"🌐 {geo}",
                        "salary": salary,
                        "portal": item.get("url") or "",
                        "description": desc[:3000],
                        "tags": [item.get("jobIndustry", "Tech"), item.get("jobType", "Full-Time")],
                        "source": "Jobicy",
                        "date_posted": str(item.get("pubDate") or ""),
                        "is_worldwide": is_worldwide_open(geo, desc[:500])
                    })
        except Exception as e:
            print(f"[Jobicy Error]: {e}")
        return jobs

    # 4. Himalayas API
    def fetch_himalayas(self, keyword: str = "python") -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = "https://himalayas.app/jobs/api?limit=35"
            r = self.session.get(url, timeout=SCRAPER_TIMEOUT)
            if r.status_code == 200:
                data = r.json().get("jobs", [])
                for item in data:
                    title = item.get("title") or ""
                    comp = item.get("companyName") or ""
                    loc_restr = item.get("locationRestrictions") or []
                    loc_str = ", ".join(loc_restr) if loc_restr else "Worldwide / Anywhere"
                    desc = clean_html(item.get("description") or item.get("excerpt") or "")
                    app_link = item.get("applicationLink") or item.get("guid") or ""

                    min_sal = item.get("minSalary")
                    max_sal = item.get("maxSalary")
                    curr = item.get("currency") or "USD"
                    salary = f"{curr} {min_sal:,} - {max_sal:,}" if min_sal and max_sal else ""

                    # Filter by keyword if provided
                    combined = f"{title} {desc} {item.get('categories', [])}".lower()
                    if keyword.lower() in combined or not keyword:
                        jobs.append({
                            "job_id": f"himalayas_{item.get('companySlug')}_{len(jobs)}",
                            "job_title": title,
                            "company": comp,
                            "location": f"🌐 {loc_str}",
                            "salary": salary,
                            "portal": app_link,
                            "description": desc[:3000],
                            "tags": (item.get("categories") or [])[:5],
                            "source": "Himalayas",
                            "date_posted": item.get("pubDate") or "",
                            "is_worldwide": is_worldwide_open(loc_str, desc[:500])
                        })
        except Exception as e:
            print(f"[Himalayas Error]: {e}")
        return jobs

    # 5. WeWorkRemotely RSS Feed
    def fetch_weworkremotely(self, keyword: str = "python") -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
            r = self.session.get(url, timeout=SCRAPER_TIMEOUT)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:25]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    pub_elem = item.find("pubDate")

                    raw_title = title_elem.text if title_elem is not None else ""
                    link = link_elem.text if link_elem is not None else ""
                    desc = clean_html(desc_elem.text if desc_elem is not None else "")
                    pub = pub_elem.text if pub_elem is not None else ""

                    parts = raw_title.split(":", 1)
                    comp = parts[0].strip() if len(parts) > 1 else "Tech Startup"
                    title = parts[1].strip() if len(parts) > 1 else raw_title

                    if keyword.lower() in (title + " " + desc).lower() or not keyword:
                        jobs.append({
                            "job_id": f"wwr_{hash(link) % 1000000}",
                            "job_title": title,
                            "company": comp,
                            "location": "🌐 Worldwide / Remote",
                            "salary": "",
                            "portal": link,
                            "description": desc[:3000],
                            "tags": ["Full-Time", "Programming", "Remote"],
                            "source": "WeWorkRemotely",
                            "date_posted": str(pub),
                            "is_worldwide": is_worldwide_open("Worldwide", desc[:500])
                        })
        except Exception as e:
            print(f"[WeWorkRemotely Error]: {e}")


        return jobs

    # 6. Arbeitnow API
    def fetch_arbeitnow(self, keyword: str = "python") -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = "https://www.arbeitnow.com/api/job-board-api"
            r = self.session.get(url, timeout=SCRAPER_TIMEOUT)
            if r.status_code == 200:
                data = r.json().get("data", [])
                for item in data:
                    if not item.get("remote"):
                        continue
                    title = item.get("title") or ""
                    comp = item.get("company_name") or ""
                    loc = item.get("location") or "Remote"
                    desc = clean_html(item.get("description") or "")
                    link = item.get("url") or ""
                    tags = item.get("tags") or []

                    combined = f"{title} {desc} {' '.join(tags)}".lower()
                    if keyword.lower() in combined or not keyword:
                        jobs.append({
                            "job_id": f"arbeit_{item.get('slug')}",
                            "job_title": title,
                            "company": comp,
                            "location": f"🌐 {loc}",
                            "salary": "",
                            "portal": link,
                            "description": desc[:3000],
                            "tags": tags[:5],
                            "source": "Arbeitnow",
                            "date_posted": item.get("created_at") or "",
                            "is_worldwide": is_worldwide_open(loc, desc[:500])
                        })
        except Exception as e:
            print(f"[Arbeitnow Error]: {e}")
        return jobs

    # 7. Direct Company ATS Boards (Canonical, GitLab, Linear, LangChain, Modal)
    def fetch_direct_ats(self, keyword: str = "python") -> List[Dict[str, Any]]:
        """Remote roles from companies' own careers pages (Greenhouse, Lever, Ashby, SmartRecruiters)."""
        from hunter.company_boards import search_company_boards
        jobs = []
        for j in search_company_boards(keyword, remote_only=True):
            jobs.append({
                **j,
                "job_id": f"ats_{abs(hash(j['job_url'])) % 10_000_000}",
                "location": f"🌐 {j['location'] or 'Remote'}",
                "tags": [j["company"], "Company careers page"],
                "is_worldwide": is_worldwide_open(j["location"], ""),
            })
        return jobs

    # Orchestrator
    def search_all_remote(
        self,
        keyword: str = "Python",
        worldwide_only: bool = True,
        limit: int = 50,
        source_filter: str = "ALL"
    ) -> List[Dict[str, Any]]:
        """Concurrently queries all remote boards and returns a deduplicated list
        strictly filtered for candidates open worldwide. Cached in memory with 15m TTL."""
        clean_kw = (keyword or "Python").strip().lower()
        cache_key = f"{clean_kw}_{worldwide_only}_{source_filter}"

        # Fast cache hit check (sub-millisecond return for concurrent users)
        cached = GLOBAL_REMOTE_CACHE.get(cache_key)
        if cached is not None:
            return cached[:limit]

        all_jobs: List[Dict[str, Any]] = []

        tasks = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            if source_filter in ["ALL", "REMOTEOK"]:
                tasks.append(executor.submit(self.fetch_remoteok, keyword))
            if source_filter in ["ALL", "REMOTIVE"]:
                tasks.append(executor.submit(self.fetch_remotive, keyword))
            if source_filter in ["ALL", "JOBICY"]:
                tasks.append(executor.submit(self.fetch_jobicy, keyword))
            if source_filter in ["ALL", "HIMALAYAS"]:
                tasks.append(executor.submit(self.fetch_himalayas, keyword))
            if source_filter in ["ALL", "WWR"]:
                tasks.append(executor.submit(self.fetch_weworkremotely, keyword))
            if source_filter in ["ALL", "ARBEITNOW"]:
                tasks.append(executor.submit(self.fetch_arbeitnow, keyword))
            if source_filter in ["ALL", "ATS"]:
                tasks.append(executor.submit(self.fetch_direct_ats, keyword))

        # The executor waits for every source (each has its own request timeout), so collect
        # all results here rather than discarding sources that finish after a fixed deadline.
        for future in tasks:
            try:
                all_jobs.extend(future.result())
            except Exception as e:
                print(f"[Remote Sub-Scraper Task Error]: {e}")

        # Deduplicate by company + title
        deduped = []
        seen = set()
        for j in all_jobs:
            # Strict Israel exclusion across all fields
            full_check = f"{j.get('company', '')} {j.get('location', '')} {j.get('description', '')}".lower()
            if any(ex in full_check for ex in EXCLUDED_TERMS):
                continue

            # Check worldwide restriction if requested
            if worldwide_only and not j.get("is_worldwide", True):
                continue

            dedupe_key = f"{j['company'].lower()}_{j['job_title'].lower()}"
            if dedupe_key in seen:
                continue

            # Live postings only. A company's own careers board lists only open roles, so
            # those stay regardless of date; feed items need a real date inside the age limit.
            source_type = j.get("source_type") or ("ats" if any(k in j.get("source", "") for k in ("Greenhouse", "Ashby", "Lever")) else "public_api")
            if source_type == "ats":
                fresh = assess(j.get("date_posted"), max_days=36500, undated_label="Open on company board")
                if fresh and fresh["days_ago"] is not None and fresh["days_ago"] > MAX_POSTING_AGE_DAYS:
                    fresh = {"date_posted": "", "days_ago": None, "posted_label": "Open on company board"}
            else:
                fresh = assess(j.get("date_posted"), MAX_POSTING_AGE_DAYS)
            if fresh is None:
                continue
            seen.add(dedupe_key)

            # Calculate match score based on candidate's Moratuwa credentials
            match_score = self._calc_match_score(j["job_title"], j.get("description", ""))
            
            clean_url = j.get("portal") or j.get("apply_url") or j.get("url") or ""
            norm_id = j.get("job_id") or j.get("id") or f"job_{abs(hash(j['company'] + j['job_title'])) % 10000000}"

            normalized_job = {
                "id": str(norm_id),
                "job_id": str(norm_id),
                "job_title": j.get("job_title", "").strip(),
                "company": j.get("company", "").strip(),
                "location": j.get("location", "🌐 Worldwide / Remote"),
                "salary": j.get("salary") or "",
                "apply_url": clean_url,
                "portal": clean_url,
                "job_url": clean_url,
                "description": j.get("description") or "",
                "tags": j.get("tags") or [],
                "source": j.get("source", "Remote Board"),
                "source_type": source_type,
                "date_posted": fresh["date_posted"],
                "posted_at": fresh["date_posted"],
                "days_ago": fresh["days_ago"],
                "posted_label": fresh["posted_label"],
                "is_worldwide": j.get("is_worldwide", True),
                "match_score": match_score,
            }
            deduped.append(normalized_job)

        # Newest first (the API re-sorts by the user's fit score)
        deduped.sort(key=lambda x: x.get("date_posted") or "0000-00-00", reverse=True)
        GLOBAL_REMOTE_CACHE.set(cache_key, deduped)
        return deduped[:limit]

    def _calc_match_score(self, title: str, desc: str) -> int:
        """Calculates candidate relevance score against Moratuwa & Python background."""
        score = 65
        combined = f"{title} {desc}".lower()

        keywords = [
            ("python", 10),
            ("fastapi", 8),
            ("backend", 6),
            ("distributed", 5),
            ("postgresql", 5),
            ("timescaledb", 5),
            ("docker", 4),
            ("aws", 4),
            ("mqtt", 4),
            ("telemetry", 4),
            ("rag", 5),
            ("machine learning", 5),
            ("ai", 4),
            ("microservices", 5),
        ]
        for kw, pts in keywords:
            if kw in combined:
                score += pts

        return min(score, 98)
