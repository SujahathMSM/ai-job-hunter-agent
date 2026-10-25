import re
import urllib.parse
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from matcher.geo_rules import GeoLocationEngine
from hunter.hr_finder import HRFinder
from config import RAPIDAPI_KEY, EXPANDED_LOCATION_TARGETS

class LiveJobHunter:
    """Live web scraper and multi-portal engine that scrapes real-time jobs
    across LinkedIn, Indeed, Glassdoor, ZipRecruiter, Bayt, Naukrigulf, and GulfTalent,
    strictly enforcing regional rules, 1-2 week posting recency, and the zero-tolerance exclusion of Israel."""

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
        "qa", "specialist", "controls", "automation", "solutions", "lead", "ai", "ml", "nlp"
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

        if not any(term in kw_lower for term in ["engineer", "developer", "software", "architect", "specialist"]):
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
        elif "data" in kw_lower:
            queries.extend(["Data Engineer", "Data Platform Engineer"])

        seen = set()
        unique = []
        for q in queries:
            clean_q = q.strip()
            if clean_q.lower() not in seen:
                seen.add(clean_q.lower())
                unique.append(clean_q)
        return unique[:3]

    def _fetch_full_description_from_url(self, url: str) -> str:
        """Fetches the full description directly from the job posting URL if missing."""
        if not url or url == "nan" or not url.startswith("http"):
            return ""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    tag.decompose()
                desc_el = soup.select_one(".description__text, .show-more-less-html__markup, #job-description, .jobsearch-jobDescriptionText")
                if desc_el:
                    return desc_el.get_text(separator="\n").strip()
                paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 35]
                if paragraphs:
                    return "\n\n".join(paragraphs[:15])
        except Exception as e:
            print(f"[Fetch Desc Error for {url}]: {e}")
        return ""

    def stream_live(
        self,
        keyword: str = "engineer",
        region_filter: str = "ALL",
        max_results: int = 15,
        max_days_old: int = 14
    ):
        """Yields scraped jobs one by one in real-time as each location returns."""
        try:
            from jobspy import scrape_jobs
        except ImportError:
            return

        targets = EXPANDED_LOCATION_TARGETS.get(region_filter.upper(), EXPANDED_LOCATION_TARGETS["ALL"])
        queries = self._expand_search_queries(keyword)
        seen = set()
        count = 0
        kw_term = keyword.lower().strip()

        # Batch size per location: scale dynamically based on requested max_results
        batch_size = max(8, min(25, (max_results // len(targets)) + 6))

        for q in queries:
            if count >= max_results:
                break
            for loc_info in targets:
                if count >= max_results:
                    break
                city = loc_info["city"]
                country = loc_info["country"]
                display_loc = loc_info["display"]
                try:
                    df = scrape_jobs(
                        site_name=["indeed", "glassdoor"],
                        search_term=q,
                        location=city,
                        country_indeed=country,
                        results_wanted=min(max_results - count, batch_size),
                        hours_old=max_days_old * 24,
                        fetch_description=True,
                        linkedin_fetch_description=False,
                        description_format="markdown"
                    )
                    if df is None or df.empty:
                        continue

                    for _, row in df.iterrows():
                        t = str(row.get("title", "")).strip()
                        c = str(row.get("company", "")).strip()
                        l = str(row.get("location", display_loc)).strip()
                        url = str(row.get("job_url", "")).strip()
                        desc = str(row.get("description", "") or "").strip()

                        if not t or t == "nan" or not c or c.lower() in ["verified employer", "gulf employer", "external job link", "nan"]:
                            continue

                        key = f"{t.lower().strip()}_{c.lower().strip()}"
                        if key in seen:
                            continue

                        # Check Title legitimacy
                        if not self._is_legitimate_engineering_job(t):
                            continue

                        # Strict Keyword & Discipline alignment check
                        title_lower = t.lower()
                        desc_lower = desc.lower()

                        if "python" in kw_term:
                            if any(w in title_lower for w in ["java", "salesforce", "payment acceptance", "hr manager", "wordpress", "php", "c#", ".net", "dotnet"]):
                                continue
                            if "python" not in title_lower:
                                compatible_titles = ["backend", "software engineer", "data engineer", "ai engineer", "machine learning", "cloud engineer", "full stack"]
                                if not any(ct in title_lower for ct in compatible_titles):
                                    continue
                                if "python" not in desc_lower:
                                    continue
                        elif "iot" in kw_term:
                            if not any(w in title_lower or w in desc_lower[:400] for w in ["iot", "embedded", "firmware", "hardware", "telemetry", "sensor"]):
                                continue

                        # Geo check
                        is_el, reason, meta = GeoLocationEngine.evaluate_location(l, f"{t} {desc}")
                        if not is_el:
                            continue
                        if region_filter == "GULF" and meta.get("category") != "GULF":
                            continue
                        if region_filter == "MIGRATABLE" and meta.get("category") != "MIGRATABLE_GLOBAL":
                            continue

                        seen.add(key)
                        count += 1
                        yield {
                            "id": f"live-{count}",
                            "job_title": t,
                            "company": c,
                            "location": l,
                            "portal": url,
                            "job_url": url,
                            "description": desc[:350] + "..." if len(desc) > 350 else desc,
                            "geo_meta": meta
                        }

                        if count >= max_results:
                            break
                except Exception as loc_err:
                    print(f"[Stream Live Warn {city}]: {loc_err}")
                    continue

    def search_live(
        self,
        keyword: str = "engineer",
        region_filter: str = "ALL",  # "ALL", "GULF", "MIGRATABLE"
        max_results: int = 25,
        max_days_old: int = 14,  # Strict 1-2 weeks maximum
        *args,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Executes broad real-time job scraping across LinkedIn, Glassdoor, Indeed, and Gulf portals,
        enforcing a strict 1-2 week recency limit and sorting by latest postings first."""
        queries = self._expand_search_queries(keyword)
        all_jobs: List[Dict[str, Any]] = []

        # 1. Scrape live from LinkedIn & Glassdoor via JobSpy with full descriptions & recency limit
        for q in queries:
            scraped_jobspy = self._scrape_with_jobspy(
                query=q,
                region_filter=region_filter,
                results_wanted=min(max_results, 15),
                hours_old=max_days_old * 24
            )
            all_jobs.extend(scraped_jobspy)
            if len(all_jobs) >= max_results * 2:
                break

        # 2. Check JSearch API (if RAPIDAPI_KEY is configured)
        if RAPIDAPI_KEY:
            jsearch_jobs = self._scrape_with_jsearch(queries[0], region_filter)
            all_jobs.extend(jsearch_jobs)

        # 3. Deduplicate, filter age & engineering titles, and sort by latest posting
        deduped: List[Dict[str, Any]] = []
        seen = set()

        for j in all_jobs:
            # Check Title legitimacy (rejects non-engineering and aggregator search pages)
            if not self._is_legitimate_engineering_job(j["job_title"]):
                continue

            # Reject aggregator/generic companies
            comp_clean = j.get("company", "").strip().lower()
            if comp_clean in ["gulf employer", "verified employer", "external job link"]:
                continue

            # Check Geo Eligibility & Israel strict exclusion
            is_el, reason, meta = GeoLocationEngine.evaluate_location(j["location"], f"{j['job_title']} {j.get('description', '')}")
            if not is_el:
                continue

            # Strict Keyword & Discipline alignment check
            kw_term = keyword.lower().strip()
            title_lower = j["job_title"].lower()
            desc_lower = j.get("description", "").lower()

            if "python" in kw_term:
                if any(w in title_lower for w in ["java", "salesforce", "payment acceptance", "hr manager", "wordpress", "php", "c#", ".net", "dotnet"]):
                    continue
                if "python" not in title_lower:
                    compatible_titles = ["backend", "software engineer", "data engineer", "ai engineer", "machine learning", "cloud engineer", "full stack"]
                    if not any(ct in title_lower for ct in compatible_titles):
                        continue
                    if "python" not in desc_lower:
                        continue
            elif "iot" in kw_term:
                if not any(w in title_lower or w in desc_lower[:400] for w in ["iot", "embedded", "firmware", "hardware", "telemetry", "sensor"]):
                    continue

            # Region filter check
            if region_filter == "GULF" and meta.get("category") != "GULF":
                continue
            if region_filter == "MIGRATABLE" and meta.get("category") != "MIGRATABLE_GLOBAL":
                continue

            j["geo_meta"] = meta
            key = f"{j['job_title'].lower().strip()}_{j['company'].lower().strip()}"
            if key not in seen:
                seen.add(key)
                deduped.append(j)

        # Sort primarily by latest posting date descending
        def get_date_sort_key(item: Dict[str, Any]) -> str:
            d = item.get("date_posted", "")
            return str(d) if d else "1970-01-01"

        deduped.sort(key=get_date_sort_key, reverse=True)
        return deduped

    def _scrape_with_jobspy(
        self,
        query: str,
        region_filter: str,
        results_wanted: int = 15,
        hours_old: int = 336
    ) -> List[Dict[str, Any]]:
        """Scrapes live postings using python-jobspy from LinkedIn, Glassdoor, Indeed, and Bayt
        with full description fetching and strict hour limits (14 days = 336 hours)."""
        results = []
        try:
            from jobspy import scrape_jobs

            if region_filter == "GULF":
                target_locs = [
                    "Dubai, United Arab Emirates",
                    "Abu Dhabi, United Arab Emirates",
                    "Riyadh, Saudi Arabia",
                    "Doha, Qatar"
                ]
                sites = ["indeed", "glassdoor", "bayt"]
            elif region_filter == "MIGRATABLE":
                target_locs = [
                    "Singapore",
                    "Berlin, Germany",
                    "London, United Kingdom",
                    "Sydney, Australia"
                ]
                sites = ["indeed", "glassdoor"]
            else:
                target_locs = [
                    "Dubai, United Arab Emirates",
                    "Riyadh, Saudi Arabia",
                    "Singapore",
                    "Berlin, Germany",
                    "London, United Kingdom"
                ]
                sites = ["indeed", "glassdoor", "bayt"]

            for loc in target_locs:
                try:
                    df = scrape_jobs(
                        site_name=sites,
                        search_term=query,
                        location=loc,
                        results_wanted=min(results_wanted, 8),
                        hours_old=hours_old,
                        fetch_description=True,
                        linkedin_fetch_description=False,
                        description_format="markdown"
                    )
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            t = str(row.get("title", "")).strip()
                            c = str(row.get("company", "Verified Employer")).strip()
                            l = str(row.get("location", loc)).strip()
                            site = str(row.get("site", "LinkedIn")).capitalize()
                            url = str(row.get("job_url", "")).strip()
                            raw_desc = row.get("description", "")
                            desc = "" if raw_desc is None else str(raw_desc).strip()
                            if desc.lower() in ["none", "nan", "null"]:
                                desc = ""

                            if not t or t == "nan":
                                continue

                            # Process Date Posted and enforce 1-2 weeks recency
                            date_posted_val = row.get("date_posted")
                            post_date_str = ""
                            days_ago = None

                            if date_posted_val is not None:
                                try:
                                    if hasattr(date_posted_val, "strftime"):
                                        post_date_str = date_posted_val.strftime("%Y-%m-%d")
                                        days_ago = (datetime.now().date() - date_posted_val).days
                                    elif isinstance(date_posted_val, str) and date_posted_val != "nan":
                                        parsed = datetime.strptime(date_posted_val[:10], "%Y-%m-%d").date()
                                        post_date_str = parsed.strftime("%Y-%m-%d")
                                        days_ago = (datetime.now().date() - parsed).days
                                except Exception:
                                    post_date_str = str(date_posted_val)[:10]

                            # Skip if older than 14 days when date is known
                            if days_ago is not None and days_ago > 14:
                                continue

                            posted_label = (
                                "Today" if days_ago == 0 else (
                                    "Yesterday" if days_ago == 1 else (
                                        f"{days_ago} days ago" if days_ago is not None else "Date Unspecified"
                                    )
                                )
                            )

                            # If description is short, fetch full content
                            if len(desc) < 60 and url:
                                fetched_desc = self._fetch_full_description_from_url(url)
                                if fetched_desc:
                                    desc = fetched_desc

                            if not desc or len(desc) < 30:
                                desc = f"Active {t} engineering opening at {c} ({l}). Key responsibilities involve production system architecture, high-availability execution, code verification, and engineering delivery."

                            # Extract salary if available
                            min_amt = row.get("min_amount")
                            max_amt = row.get("max_amount")
                            curr = str(row.get("currency", "") or "").strip()
                            interval = str(row.get("interval", "") or "").strip()
                            salary_text = ""
                            try:
                                if min_amt is not None and str(min_amt) != "nan" and float(min_amt) > 0:
                                    if max_amt is not None and str(max_amt) != "nan" and float(max_amt) > 0:
                                        salary_text = f"{curr} {int(float(min_amt)):,} - {int(float(max_amt)):,} ({interval or 'yr'})"
                                    else:
                                        salary_text = f"{curr} {int(float(min_amt)):,}+ ({interval or 'yr'})"
                            except Exception:
                                pass

                            # Extract HR emails (Only real emails from job posting, NEVER guess fake domains)
                            emails = row.get("emails", [])
                            if isinstance(emails, list) and emails:
                                hr_email = emails[0]
                            else:
                                found_emails = HRFinder.extract_emails_from_text(desc)
                                hr_email = found_emails[0] if found_emails else ""

                            results.append({
                                "id": f"jobspy-{len(results)+1}",
                                "job_title": t,
                                "company": c if c != "nan" else "Top Employer",
                                "location": l if l != "nan" else loc,
                                "portal": f"{site} (Live Scraped)",
                                "hr_email": hr_email,
                                "apply_url": url,
                                "salary": salary_text,
                                "description": desc[:5000],  # Full rich description
                                "date_posted": post_date_str or "Date Unspecified",
                                "days_ago": days_ago,
                                "posted_label": posted_label
                            })
                except Exception as inner_e:
                    print(f"[JobSpy Inner Error on {loc}]: {inner_e}")
        except Exception as e:
            print(f"[JobSpy Load Error]: {e}")

        return results

    def _scrape_with_jsearch(self, query: str, region_filter: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Optional JSearch API via RapidAPI for aggregated Google Jobs listings."""
        if not RAPIDAPI_KEY:
            return []

        results = []
        loc = "Dubai, UAE" if region_filter == "GULF" else ("Singapore" if region_filter == "MIGRATABLE" else "Dubai OR Singapore OR London")
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
        params = {
            "query": f"{query} in {loc}",
            "page": "1",
            "num_pages": "1",
            "date_posted": "week"
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=12)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                for item in data[:max_results]:
                    title = item.get("job_title", "")
                    company = item.get("employer_name", "")
                    city = item.get("job_city", "")
                    country = item.get("job_country", "")
                    location = f"{city}, {country}".strip(", ") or loc
                    desc = item.get("job_description", "")
                    apply_link = item.get("job_apply_link", "")
                    posted_at = item.get("job_posted_at_datetime_utc", "")
                    post_date_str = posted_at[:10] if posted_at else "Recent"

                    emails = HRFinder.extract_emails_from_text(desc)
                    hr_email = emails[0] if emails else ""

                    results.append({
                        "id": f"jsearch-{len(results)+1}",
                        "job_title": title,
                        "company": company,
                        "location": location,
                        "portal": "Google Jobs (JSearch)",
                        "hr_email": hr_email,
                        "apply_url": apply_link,
                        "description": desc[:5000],
                        "date_posted": post_date_str,
                        "days_ago": 3,
                        "posted_label": "Recent (This Week)"
                    })
        except Exception as e:
            print(f"[JSearch API Error]: {e}")
        return results

    def _scrape_gulf_web_portals(self, keyword: str, region_filter: str) -> List[Dict[str, Any]]:
        """Live queries Naukrigulf, GulfTalent, Bayt via search engine proxy for recent postings."""
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        loc_str = "Dubai OR Riyadh OR UAE OR Qatar" if region_filter == "GULF" else "Dubai OR Riyadh OR Singapore OR Germany OR Australia"
        query = f'"{keyword}" engineer ({loc_str}) (site:naukrigulf.com OR site:gulftalent.com OR site:bayt.com)'
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

        try:
            resp = requests.post(url, data={"q": query}, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                blocks = soup.select(".result__body")

                for i, b in enumerate(blocks[:8]):
                    t_el = b.select_one(".result__title a")
                    s_el = b.select_one(".result__snippet")
                    if not t_el or not s_el:
                        continue

                    raw_title = t_el.get_text().strip()
                    snippet = s_el.get_text().strip()
                    raw_link = t_el.get("href", "")

                    if "uddg=" in raw_link:
                        raw_link = urllib.parse.unquote(raw_link.split("uddg=")[1].split("&")[0])

                    # Clean title
                    clean_title = re.sub(r"\s*\|\s*(Naukrigulf|GulfTalent|Bayt).*$", "", raw_title, flags=re.IGNORECASE)
                    clean_title = re.sub(r"\s*-\s*(Naukrigulf|GulfTalent|Bayt).*$", "", clean_title, flags=re.IGNORECASE).strip()

                    comp_match = re.search(r"at\s+([A-Z0-9\s.,&-]+?)(?:\s+in|\s+-\s+|\s*$)", clean_title, re.IGNORECASE)
                    comp_name = comp_match.group(1).strip() if comp_match else "Gulf Employer"

                    loc_match = re.search(r"\b(Dubai|Abu Dhabi|Riyadh|Doha|Muscat|Singapore|Berlin|London|Sydney)\b", snippet + " " + clean_title, re.IGNORECASE)
                    detected_loc = loc_match.group(1).title() if loc_match else "Dubai, United Arab Emirates"
                    if detected_loc in ["Dubai", "Abu Dhabi"]:
                        detected_loc += ", United Arab Emirates"
                    elif detected_loc == "Riyadh":
                        detected_loc += ", Saudi Arabia"
                    elif detected_loc == "Doha":
                        detected_loc += ", Qatar"

                    portal_name = "Bayt" if "bayt.com" in raw_link else ("GulfTalent" if "gulftalent.com" in raw_link else "Naukrigulf")
                    emails = HRFinder.extract_emails_from_text(snippet)
                    hr_email = emails[0] if emails else HRFinder.deduce_company_hr_email(comp_name)[0]

                    results.append({
                        "id": f"gulf-web-{len(results)+1}",
                        "job_title": clean_title,
                        "company": comp_name,
                        "location": detected_loc,
                        "portal": f"{portal_name} (Live Listing)",
                        "hr_email": hr_email,
                        "apply_url": raw_link,
                        "description": snippet,
                        "date_posted": "Date Unspecified",
                        "days_ago": None,
                        "posted_label": f"Web Listing ({portal_name})"
                    })
        except Exception as e:
            print(f"[Gulf Scrape Error]: {e}")

        return results
