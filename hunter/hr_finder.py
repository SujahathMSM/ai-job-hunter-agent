import os
import re
from typing import List, Optional, Dict, Any
import requests
from config import HUNTER_API_KEY

class HRFinder:
    """Extracts or deduces HR and Talent Acquisition contact emails for job postings,
    with Hunter.io API verification integration."""

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
    def find_verified_hr_email(cls, company_name: str, domain: Optional[str] = None) -> List[str]:
        """Queries Hunter.io for verified HR emails if API key is present; otherwise falls back to deduction."""
        clean_company = re.sub(r"[^a-zA-Z0-9]", "", company_name.lower())
        active_domain = domain if domain else f"{clean_company}.com"

        api_key = os.getenv("HUNTER_API_KEY", HUNTER_API_KEY)
        if api_key and active_domain:
            try:
                url = f"https://api.hunter.io/v2/domain-search?domain={active_domain}&department=hr,recruitment&api_key={api_key}"
                resp = requests.get(url, timeout=6)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    emails = data.get("emails", [])
                    verified = [e.get("value") for e in emails if e.get("value")]
                    if verified:
                        return verified
            except Exception as e:
                print(f"[Hunter.io API Warning]: {e}")

        return cls.deduce_company_hr_email(company_name, domain)

    @classmethod
    def deduce_company_hr_email(cls, company_name: str, domain: Optional[str] = None) -> List[str]:
        """Suggests probable HR emails if domain or clean company name is known."""
        clean_company = re.sub(r"[^a-zA-Z0-9]", "", company_name.lower())
        active_domain = domain if domain else f"{clean_company}.com"

        candidates = [
            f"careers@{active_domain}",
            f"hr@{active_domain}",
            f"recruitment@{active_domain}",
            f"talent@{active_domain}"
        ]
        return candidates
