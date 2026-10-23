import re
from typing import Tuple, Dict, Any, List
from config import GULF_COUNTRIES, MIGRATABLE_COUNTRIES, EXCLUDED_COUNTRIES

class GeoLocationEngine:
    """Validates candidate target regions, specifically focusing on Gulf countries and
    easily migratable countries from Sri Lanka, while enforcing strict exclusion rules (e.g. Israel)."""

    @classmethod
    def evaluate_location(cls, location_str: str, job_text: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """Evaluates whether a job posting matches the geographic requirements.
        Returns:
            (is_allowed, reason, metadata)
        """
        combined_text = f"{location_str} {job_text}".lower()

        # 1. STRICT EXCLUSION CHECK (Highest Priority Rule)
        for excluded in EXCLUDED_COUNTRIES:
            pattern = rf"\b{re.escape(excluded.lower())}\b"
            if re.search(pattern, combined_text):
                return False, f"STRICT_EXCLUSION: Job location matches excluded country '{excluded}'", {
                    "category": "EXCLUDED",
                    "flagged_country": excluded
                }

        # 2. CHECK GULF COUNTRIES
        for gulf in GULF_COUNTRIES:
            pattern = rf"\b{re.escape(gulf.lower())}\b"
            if re.search(pattern, combined_text):
                return True, f"Eligible: Matched Gulf country/hub '{gulf}'", {
                    "category": "GULF",
                    "matched_location": gulf
                }

        # 3. CHECK EASILY MIGRATABLE DESTINATIONS FROM SRI LANKA
        for migratable in MIGRATABLE_COUNTRIES:
            pattern = rf"\b{re.escape(migratable.lower())}\b"
            if re.search(pattern, combined_text):
                return True, f"Eligible: Matched preferred migration pathway '{migratable}'", {
                    "category": "MIGRATABLE_GLOBAL",
                    "matched_location": migratable
                }

        # 4. REMOTE POSITIONS (Allowed if not affiliated with excluded countries)
        if "remote" in combined_text or "worldwide" in combined_text or "anywhere" in combined_text:
            return True, "Eligible: Remote / Global opportunity", {
                "category": "REMOTE",
                "matched_location": "Remote"
            }

        # Not in target regions
        return False, f"Location '{location_str}' is outside Gulf and preferred migration destinations.", {
            "category": "OUT_OF_TARGET",
            "matched_location": location_str
        }

    @classmethod
    def get_supported_regions_summary(cls) -> Dict[str, List[str]]:
        return {
            "gulf_countries": list(set([c for c in GULF_COUNTRIES if len(c) > 3])),
            "migratable_countries": list(set([c for c in MIGRATABLE_COUNTRIES if len(c) > 3])),
            "strictly_excluded": EXCLUDED_COUNTRIES
        }
