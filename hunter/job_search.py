import re
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from matcher.geo_rules import GeoLocationEngine
from hunter.hr_finder import HRFinder
from hunter.live_scraper import LiveJobHunter

class JobHunter:
    """Discovers and scrapes 100% real, active engineering openings across the Gulf
    (UAE, Saudi Arabia, Qatar, Oman) and global migration pathways (Singapore, Germany, UK, Australia),
    strictly enforcing regional rules and the zero-tolerance exclusion of Israel."""

    def __init__(self):
        self.live_scraper = LiveJobHunter()

    def search_jobs(
        self,
        keyword: str = "",
        region_filter: str = "ALL",  # "ALL", "GULF", "MIGRATABLE"
        include_live: bool = True,
        max_days_old: int = 14,
        *args,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Executes a real-time live scrape across LinkedIn, Glassdoor, Indeed, Bayt, and GulfTalent.
        Returns ONLY real active postings with direct application links and max age of 1-2 weeks."""
        kw_clean = keyword.strip() or "software engineer"

        # Search live portals directly with broad query expansion and recency filtering
        try:
            real_jobs = self.live_scraper.search_live(
                keyword=kw_clean,
                region_filter=region_filter,
                max_results=25,
                max_days_old=max_days_old
            )
        except TypeError:
            real_jobs = self.live_scraper.search_live(
                kw_clean,
                region_filter
            )

        return real_jobs

    def fetch_job_from_url(self, url: str) -> Dict[str, Any]:
        """Fetches and parses a real job posting directly from any web URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.find("h1")
                title_text = title.get_text().strip() if title else "Engineering Position"

                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                body_text = soup.get_text(separator="\n")
                clean_lines = [l.strip() for l in body_text.split("\n") if len(l.strip()) > 30]
                summary_text = "\n".join(clean_lines[:30])

                emails = HRFinder.extract_emails_from_text(resp.text)
                hr_email = emails[0] if emails else ""

                return {
                    "job_title": title_text,
                    "company": "External Job Link",
                    "location": "Gulf / International",
                    "portal": url,
                    "hr_email": hr_email,
                    "apply_url": url,
                    "description": summary_text or "Job details fetched from external source."
                }
        except Exception as e:
            print(f"[Fetch URL Error]: {e}")

        return {
            "job_title": "Engineering Role",
            "company": "Company",
            "location": "Gulf Region",
            "portal": url,
            "hr_email": "",
            "apply_url": url,
            "description": "Could not automatically scrape content. Please paste job description manually."
        }
