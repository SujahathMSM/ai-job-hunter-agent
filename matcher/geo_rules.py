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
        loc_lower = (location_str or "").lower().strip()
        text_lower = (job_text or "").lower()
        combined_text = f"{loc_lower} {text_lower}"

        # 1. STRICT EXCLUSION CHECK (Highest Priority Rule)
        # Check strict city and country exclusions
        for excluded in EXCLUDED_COUNTRIES:
            pattern = rf"\b{re.escape(excluded.lower())}\b"
            if re.search(pattern, combined_text):
                return False, f"STRICT_EXCLUSION: Job location matches excluded country '{excluded}'", {
                    "category": "EXCLUDED",
                    "flagged_country": excluded
                }

        # Check IL country code in location only when NOT US Illinois (e.g., "Chicago, IL", "IL, USA")
        if re.search(r"\b,\s*il\b", loc_lower) or re.search(r"\bil\b", loc_lower):
            is_us = any(u in loc_lower or u in text_lower for u in ["usa", "united states", "chicago", "illinois", "peoria", "springfield"])
            if not is_us and ("israel" in combined_text or "tel aviv" in combined_text):
                return False, "STRICT_EXCLUSION: Job location matches excluded country 'Israel (IL)'", {
                    "category": "EXCLUDED",
                    "flagged_country": "Israel"
                }

        # 2. CHECK GULF COUNTRIES
        # Location string takes precedence, fallback to text
        for gulf in GULF_COUNTRIES:
            pattern = rf"\b{re.escape(gulf.lower())}\b"
            if re.search(pattern, loc_lower) or re.search(pattern, text_lower):
                return True, f"Eligible: Matched Gulf country/hub '{gulf}'", {
                    "category": "GULF",
                    "matched_location": gulf
                }

        # 3. CHECK EASILY MIGRATABLE DESTINATIONS FROM SRI LANKA
        for migratable in MIGRATABLE_COUNTRIES:
            # Special safeguard for Male (capital of Maldives): only match in location or with maldives context
            if migratable.lower() in ["male", "male, maldives"]:
                if "maldives" in loc_lower or re.search(r"\bmale,?\s*maldives\b", loc_lower) or (re.search(r"\bmale\b", loc_lower) and "maldives" in combined_text):
                    return True, "Eligible: Matched preferred migration pathway 'Maldives'", {
                        "category": "MIGRATABLE_GLOBAL",
                        "matched_location": "Maldives"
                    }
                continue

            pattern = rf"\b{re.escape(migratable.lower())}\b"
            # Require matching in location or explicit country in text
            if re.search(pattern, loc_lower) or (len(migratable) > 3 and re.search(pattern, text_lower)):
                return True, f"Eligible: Matched preferred migration pathway '{migratable}'", {
                    "category": "MIGRATABLE_GLOBAL",
                    "matched_location": migratable
                }

        # 4. REMOTE POSITIONS (Allowed if not affiliated with excluded countries)
        if any(w in loc_lower for w in ["remote", "worldwide", "anywhere", "global", "work from home"]) or ("remote" in text_lower and len(loc_lower) < 4):
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
