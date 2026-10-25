import os
import re
import urllib.parse
from typing import List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from config import HUNTER_API_KEY, APOLLO_API_KEY

class HRFinder:
    """Extracts, verifies, and discovers real HR and Talent Acquisition contacts globally
    using Hunter.io, Apollo.io, and live precision recruiter search."""

    COMMON_HR_PREFIXES = ["careers", "recruitment", "hr", "jobs", "talent", "hiring", "apply"]

    @classmethod
    def extract_emails_from_text(cls, text: str) -> List[str]:
        """Finds any explicit email addresses inside a job posting text."""
        raw_matches = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        clean = []
        for m in raw_matches:
            m = m.strip(".,;:()")
            # Filter out non-email garbage or standard image extensions
            if not any(m.lower().endswith(ext) for ext in [".png", ".jpg", ".gif", ".webp"]):
                if m not in clean:
                    clean.append(m)
        return clean

    @classmethod
    def deduce_company_hr_email(cls, company_name: str, domain: Optional[str] = None) -> List[str]:
        """Suggests general corporate email patterns for manual verification."""
        clean_company = re.sub(r"[^a-zA-Z0-9]", "", company_name.lower())
        active_domain = domain if domain else f"{clean_company}.com"
        return [
            f"careers@{active_domain}",
            f"hr@{active_domain}",
            f"recruitment@{active_domain}",
            f"talent@{active_domain}"
        ]

    @classmethod
    def search_global_hr(
        cls,
        company_name: str,
        domain: Optional[str] = None,
        region: str = "ALL",
        role_focus: str = "recruiter"
    ) -> Dict[str, Any]:
        """Comprehensive search across Hunter.io, Apollo.io, and live LinkedIn recruiter queries
        to discover real, verified HR contacts and recruiters globally."""
        clean_company = company_name.strip()
        comp_slug = re.sub(r"[^a-zA-Z0-9]", "", clean_company.lower())
        active_domain = domain.strip().lower() if domain else f"{comp_slug}.com"
        active_domain = active_domain.replace("https://", "").replace("http://", "").split("/")[0]

        result: Dict[str, Any] = {
            "company": clean_company,
            "domain": active_domain,
            "email_pattern": None,
            "verified_contacts": [],
            "discovered_recruiters": [],
            "search_dorks": [],
            "hunter_active": False,
            "apollo_active": False
        }

        # 1. Query Hunter.io API (if API key is present)
        hunter_key = os.getenv("HUNTER_API_KEY", HUNTER_API_KEY)
        if hunter_key and active_domain:
            result["hunter_active"] = True
            try:
                url = f"https://api.hunter.io/v2/domain-search?domain={active_domain}&department=human_resources&api_key={hunter_key}"
                resp = requests.get(url, timeout=7)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    result["email_pattern"] = data.get("pattern")
                    for em in data.get("emails", []):
                        val = em.get("value")
                        if val:
                            f_name = em.get("first_name") or ""
                            l_name = em.get("last_name") or ""
                            full_n = f"{f_name} {l_name}".strip() or "HR Specialist"
                            result["verified_contacts"].append({
                                "name": full_n,
                                "email": val,
                                "role": em.get("position") or "Human Resources",
                                "confidence": f"{em.get('confidence', 90)}%",
                                "linkedin": em.get("linkedin") or "",
                                "source": "Hunter.io (Verified)"
                            })
            except Exception as e:
                print(f"[Hunter.io API Error]: {e}")

        # 2. Query Apollo.io API (if API key is present)
        apollo_key = os.getenv("APOLLO_API_KEY", APOLLO_API_KEY)
        if apollo_key and active_domain:
            result["apollo_active"] = True
            try:
                headers = {"Content-Type": "application/json", "X-Api-Key": apollo_key}
                payload = {
                    "q_organization_domains": [active_domain],
                    "person_titles": ["Talent Acquisition", "Technical Recruiter", "HR Manager", "Head of People"],
                    "per_page": 8
                }
                resp = requests.post("https://api.apollo.io/v1/contacts/search", json=payload, headers=headers, timeout=8)
                if resp.status_code == 200:
                    contacts = resp.json().get("contacts", [])
                    for c in contacts:
                        em = c.get("email")
                        if em:
                            result["verified_contacts"].append({
                                "name": f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() or "Recruiter",
                                "email": em,
                                "role": c.get("title") or "Talent Acquisition",
                                "confidence": "Verified (Apollo)",
                                "linkedin": c.get("linkedin_url") or "",
                                "source": "Apollo.io (Verified)"
                            })
            except Exception as e:
                print(f"[Apollo.io API Error]: {e}")

        # 3. Live Precision Recruiter Search (Zero-cost, works for any company worldwide)
        region_query = ""
        if region == "GULF":
            region_query = '("Dubai" OR "UAE" OR "Riyadh" OR "Saudi Arabia" OR "Qatar")'
        elif region == "MIGRATABLE":
            region_query = '("Singapore" OR "London" OR "Berlin" OR "Munich" OR "Sydney")'

        dork_query = f'site:linkedin.com/in ("Technical Recruiter" OR "Talent Acquisition" OR "Recruitment Lead" OR "HR Manager") "{clean_company}" {region_query}'.strip()
        ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(dork_query)}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = requests.post(ddg_url, data={"q": dork_query}, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                blocks = soup.select(".result__body")
                for b in blocks[:6]:
                    t_el = b.select_one(".result__title a")
                    s_el = b.select_one(".result__snippet")
                    if not t_el or not s_el:
                        continue
                    raw_text = t_el.get_text().strip()
                    snippet = s_el.get_text().strip()
                    link = t_el.get("href", "")
                    if "uddg=" in link:
                        link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

                    clean_title = re.sub(r"\s*\|\s*LinkedIn.*$", "", raw_text, flags=re.IGNORECASE).strip()
                    parts = re.split(r"[-–|]", clean_title)
                    person_name = parts[0].strip() if len(parts) > 1 else clean_title
                    person_role = " - ".join([p.strip() for p in parts[1:]]) if len(parts) > 1 else "Talent Acquisition / Recruiter"

                    if len(person_name.split()) <= 4 and not any(w in person_name.lower() for w in ["job", "career", "vacanc"]):
                        result["discovered_recruiters"].append({
                            "name": person_name,
                            "role": person_role,
                            "snippet": snippet,
                            "linkedin_url": link
                        })
        except Exception as e:
            print(f"[Recruiter Scrape Warning]: {e}")

        # 4. Generate 1-Click Precision Search Dorks for user
        encoded_comp = urllib.parse.quote(f'"{clean_company}"')
        result["search_dorks"] = [
            {
                "title": f"LinkedIn Recruiters at {clean_company}",
                "description": f"Find Talent Acquisition Specialists & Technical Recruiters at {clean_company}",
                "url": f"https://www.google.com/search?q=site:linkedin.com/in+('Technical+Recruiter'+OR+'Talent+Acquisition'+OR+'HR')+{encoded_comp}"
            },
            {
                "title": f"Engineering Leadership at {clean_company}",
                "description": f"Find Engineering Managers, VP of Engineering & CTO at {clean_company}",
                "url": f"https://www.google.com/search?q=site:linkedin.com/in+('Engineering+Manager'+OR+'Head+of+Engineering'+OR+'CTO')+{encoded_comp}"
            },
            {
                "title": f"Official Careers & Hiring Page for {clean_company}",
                "description": f"Open direct jobs portal and career listings for {clean_company}",
                "url": f"https://www.google.com/search?q={encoded_comp}+careers+jobs+email"
            }
        ]

        return result
